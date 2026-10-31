"""Marks which server a fact in the global user memory was told in.

User memory is keyed by Discord ID only, so one member's memory is shown on every server they
talk to the bot in. Each saved fact is tagged with the server it came from, and when the memory is
read the tag is turned into "this server" or "another server", so the model can tell what was said
here from what was said somewhere else.

Only the server **id** is stored. A server name is chosen by its owner (so it could carry
instructions into every other server's prompt) and would tell other servers which communities the
member belongs to.
"""

from __future__ import annotations

import re
import time
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Sequence, Tuple

from addons.logging import get_logger

logger = get_logger(server_id="Bot", source=__name__)

# Added to the merge prompt so the merge model keeps the tags next to their facts.
SOURCE_TAG_INSTRUCTION = (
    "A fact may end with a [source: ...] tag saying where it was told. Keep that tag "
    "attached to its fact; when the same fact comes from several places keep every tag. "
    "Never add a tag to a fact that has none and never change a tag."
)

# A tag typed into the fact itself would pass for a real one (the merge prompt keeps every tag).
# Everything here must run in linear time: the dashboard calls it on member-supplied text on the
# bot's event loop, so no unbounded scan from each "[" and no repeated passes.
_TAG_OPEN = r"(?i:\[(?=\s{0,20}source))"
_STORED_TAG = re.compile(r"\[source: (?:server id=\d+|direct message)\]")
_SERVER_TAG = re.compile(r"\[source: server id=(\d+)\]")


def _neutralize_tags(text: str, keep: "frozenset[str]") -> str:
    """Make every typed ``[source`` opening harmless, except the exact tags in ``keep``.

    The ``[`` of an opening becomes ``(``, so the text can no longer pass for a tag. Nothing is
    removed, so a pass cannot join the rest of the text into a new tag, and one pass is enough.

    Args:
        text: Text that may hold typed tags.
        keep: Exact tag strings that stay as they are.

    Returns:
        The text with the other tag openings neutralized.
    """
    if keep:
        kept = "|".join(re.escape(tag) for tag in sorted(keep, key=len, reverse=True))
        pattern = re.compile(f"(?P<keep>{kept})|{_TAG_OPEN}")
    else:
        pattern = re.compile(_TAG_OPEN)
    return pattern.sub(lambda match: match.group(0) if match.groupdict().get("keep") else "(", text)


def drop_unknown_tags(new_text: str, stored_text: Optional[str]) -> str:
    """Neutralize tags a member typed into their memory themselves.

    For memory edited outside the bot (the dashboard), where ``tag_with_source`` never runs. The
    member sees the stored tags and sends them back with their edit, so a tag stays only when the
    stored text of that field already had it. A kept tag is not tied to its original fact: a member
    can move one onto another of their own facts. That is their own data and tags are a hint about
    where something was said, not a security boundary.

    Args:
        new_text: The edited memory text.
        stored_text: What is stored now, or ``None``.

    Returns:
        ``new_text`` with every tag that was not already stored neutralized.
    """
    known = frozenset(_STORED_TAG.findall(stored_text or ""))
    return _neutralize_tags(new_text, known).strip()


def tag_with_source(text: str, context: Optional[Any]) -> str:
    """Append the place ``text`` was told in to it.

    Args:
        text: The fact to save.
        context: The Discord message or interaction that triggered the save, or ``None``.

    Returns:
        ``text`` followed by ``[source: server id=<id>]`` or ``[source: direct message]``. Any tag
        already typed into ``text`` is neutralized. Without a context the text is returned unchanged.
    """
    if context is None:
        return text
    text = _neutralize_tags(text, keep=frozenset())
    guild = getattr(context, "guild", None)
    tag = "[source: direct message]" if guild is None else f"[source: server id={guild.id}]"
    # Every line is its own fact; the merge keeps a tag next to its fact and never tags an untagged one.
    return "\n".join(f"{line.strip()} {tag}" if line.strip() else "" for line in text.strip().split("\n"))


# Reattaching tags compares every merged line with the known facts. The text comes from the merge
# model and from members, so the work is bounded: long lines are not compared by similarity (the
# cost grows with the square of the length) and all similarity work shares one time budget; lines
# reached after it ran out are only matched when identical or contained, and that is logged.
_MAX_FUZZY_CHARS = 400
_MAX_CONTAIN_WORK = 20_000_000
_FUZZY_BUDGET_SECONDS = 0.4
_MIN_CONTAINED_CHARS = 4
_MIN_SIMILARITY = 0.7
_MIN_SIMILARITY_TO_NEW = 0.65  # unrelated short sentences already reach 0.58; reworded ones 0.67+


def _normalize(text: str) -> str:
    """Reduce a fact for comparison: case, spacing and edge punctuation do not matter, symbols do.

    ``C++`` and ``C#`` are different facts, so symbols inside the text are kept.
    """
    return re.sub(r"\s+", " ", text.casefold()).strip(" .。!！,，;；:：")


def _split_fact(line: str) -> Tuple[str, Tuple[str, ...]]:
    """Split a line into its text (indentation kept) and the stored tags it carries (in order, no repeats)."""
    return _STORED_TAG.sub("", line).rstrip(), tuple(dict.fromkeys(_STORED_TAG.findall(line)))


def _is_word_char(char: str) -> bool:
    """Whether ``char`` continues a Latin word (CJK text has no word boundaries to respect)."""
    return char.isascii() and char.isalnum()


def _contains(fact: str, key: str) -> bool:
    """Whether ``fact`` occurs in ``key`` as whole words: ``likes jazz`` is not in ``dislikes jazz``."""
    start = key.find(fact)
    while start != -1:
        end = start + len(fact)
        starts_clean = not (_is_word_char(fact[0]) and start > 0 and _is_word_char(key[start - 1]))
        ends_clean = not (_is_word_char(fact[-1]) and end < len(key) and _is_word_char(key[end]))
        if starts_clean and ends_clean:
            return True
        start = key.find(fact, start + 1)
    return False


def _most_similar(key: str, candidates: Dict[str, Tuple[str, ...]], minimum: float, deadline: float) -> Optional[str]:
    """The candidate fact most similar to ``key`` (at least ``minimum``), if any.

    Args:
        key: Normalized text to compare.
        candidates: Normalized facts mapped to their tags.
        minimum: Lowest accepted similarity ratio.
        deadline: ``time.monotonic()`` value after which no more comparisons are made.

    Returns:
        The best candidate, or ``None`` when none is similar enough or the limits (line length,
        time) leave the comparison out.
    """
    if len(key) > _MAX_FUZZY_CHARS:
        return None
    matcher = SequenceMatcher(None, autojunk=False)
    matcher.set_seq2(key)
    best_ratio, best_fact = 0.0, None
    for fact in candidates:
        if len(fact) > _MAX_FUZZY_CHARS:
            continue
        if time.monotonic() > deadline:
            break
        matcher.set_seq1(fact)
        if matcher.real_quick_ratio() < minimum or matcher.quick_ratio() < minimum:
            continue
        ratio = matcher.ratio()
        if ratio > best_ratio:
            best_ratio, best_fact = ratio, fact
    return best_fact if best_ratio >= minimum else None


def _union(*tag_groups: Sequence[str]) -> Tuple[str, ...]:
    """Tags of all groups in order, without repeats."""
    return tuple(dict.fromkeys(tag for group in tag_groups for tag in group))


def reattach_source_tags(
    merged_text: Optional[str], earlier_texts: Sequence[Optional[str]], new_tagged_text: str
) -> Optional[str]:
    """Put each fact's source tag back after the merge model rewrote the memory.

    The model is asked to keep the tags, but it may drop, move or invent them, so the code decides.
    Each merged line is matched with the earlier facts and the facts being saved:

    * identical to a known fact: that fact's tags plus the known tags the model gave it (the same
      fact told in other words elsewhere, merged by the model);
    * containing known facts (whole words): their tags plus the known tags the model gave it;
    * similar to a known fact (reworded): the known tags the model gave it if any, else that fact's
      tags; if it was an earlier fact that has tags, this save's tags are added too, since the
      change can only come from this save. An earlier fact stored without a tag stays without one;
    * nothing: the known tags the model gave it, else this save's tags if it resembles what is being
      saved, else none. A wrong "told here" is worse than a missing tag.

    A tag the model made up is always dropped. The matching is a heuristic: when a merge changes
    the meaning of a fact (a contradiction) the new wording may carry only the old tag, and a
    member who plants a known tag in their own text can move it onto another of their own facts.

    Args:
        merged_text: One field of the merged memory.
        earlier_texts: The memory fields stored before this save.
        new_tagged_text: What is being saved, already tagged by ``tag_with_source``.

    Returns:
        ``merged_text`` with the tags put back (``None`` and the empty string are returned as they are).
    """
    if not merged_text:
        return merged_text
    facts: Dict[str, Tuple[str, ...]] = {}
    new_facts: Dict[str, Tuple[str, ...]] = {}
    sources = [(earlier, False) for earlier in earlier_texts] + [(new_tagged_text, True)]
    for text, is_new in sources:
        for line in (text or "").split("\n"):
            clean, tags = _split_fact(line)
            key = _normalize(clean)
            if key:
                facts[key] = _union(facts.get(key, ()), tags)
                if is_new:
                    new_facts[key] = facts[key]
    known_tags = {tag for tags in facts.values() for tag in tags}
    new_tags = _union(*new_facts.values())

    lines = merged_text.split("\n")
    allow_similarity = len(merged_text) * len(facts) <= _MAX_CONTAIN_WORK
    deadline = time.monotonic() + _FUZZY_BUDGET_SECONDS
    result: List[str] = []
    for line in lines:
        clean, present = _split_fact(line)
        key = _normalize(clean)
        shown = _neutralize_tags(clean, frozenset())  # a malformed tag the model invented is text, not a tag
        if not key:
            result.append(shown)
            continue
        given = tuple(tag for tag in present if tag in known_tags)
        tags: Tuple[str, ...]
        if key in facts:
            # The same fact told in other words elsewhere: the model merged them and kept both tags.
            tags = _union(facts[key], given)
        elif allow_similarity and (contained := [t for f, t in facts.items() if len(f) >= _MIN_CONTAINED_CHARS and _contains(f, key)]):
            tags = _union(*contained, given)
        elif allow_similarity and (similar := _most_similar(key, facts, _MIN_SIMILARITY, deadline)) is not None:
            # Similarity is a guess: when the model tagged the line itself, its known tags win.
            tags = given or facts[similar]
            if not given and similar not in new_facts and tags:
                tags = _union(tags, new_tags)
        elif given:
            tags = given
        elif allow_similarity and (like_new := _most_similar(key, new_facts, _MIN_SIMILARITY_TO_NEW, deadline)) is not None:
            tags = new_facts[like_new]
        else:
            tags = ()
        result.append(f"{shown} {' '.join(tags)}" if tags else shown)
    if time.monotonic() > deadline:
        logger.warning("Source tag matching ran out of its %.1f s budget; later lines were matched without similarity", _FUZZY_BUDGET_SECONDS)
    return "\n".join(result)


def render_sources(text: str, current_guild_id: Optional[str]) -> str:
    """Turn stored server ids into "this server" / "another server" for whoever reads the memory.

    Args:
        text: Stored memory text.
        current_guild_id: The server the memory is being read in, or ``None`` in a direct message.

    Returns:
        ``text`` with each ``[source: server id=<id>]`` replaced; other text is left alone.
    """
    def replace(match: "re.Match[str]") -> str:
        where = "this server" if current_guild_id is not None and match.group(1) == str(current_guild_id) else "another server"
        return f"[source: {where}]"

    return _SERVER_TAG.sub(replace, text)
