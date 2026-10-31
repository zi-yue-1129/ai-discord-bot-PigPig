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
# model and from members, so the work is bounded: long lines are never fuzzy-compared (the cost
# grows with the square of the length), there is a cap on comparisons, and a time budget after which
# the rest of the lines are only matched when identical or contained.
_MAX_FUZZY_PAIRS = 4_000
_MAX_FUZZY_CHARS = 120
_MAX_CONTAIN_WORK = 20_000_000
_FUZZY_BUDGET_SECONDS = 0.25
_MIN_CONTAINED_CHARS = 4
_MIN_SIMILARITY = 0.7
_MIN_SIMILARITY_TO_NEW = 0.65  # unrelated short sentences already reach 0.58; reworded ones 0.67+


def _normalize(text: str) -> str:
    """Reduce a fact for comparison: case, spacing and edge punctuation do not matter, symbols do.

    ``C++`` and ``C#`` are different facts, so symbols inside the text are kept.
    """
    return re.sub(r"\s+", " ", text.casefold()).strip(" .。!！,，;；:：")


def _split_fact(line: str) -> Tuple[str, Tuple[str, ...]]:
    """Split a line into its text and the stored tags it carries (in order, without repeats)."""
    return _STORED_TAG.sub("", line).strip(), tuple(dict.fromkeys(_STORED_TAG.findall(line)))


def _most_similar(
    key: str, candidates: Dict[str, Tuple[str, ...]], minimum: float, deadline: float
) -> Optional[Tuple[str, ...]]:
    """The tags of the candidate most similar to ``key`` (at least ``minimum``), if any.

    Args:
        key: Normalized text to compare.
        candidates: Normalized facts mapped to their tags.
        minimum: Lowest accepted similarity ratio.
        deadline: ``time.monotonic()`` value after which no more comparisons are made.

    Returns:
        The tags of the best candidate, or ``None`` when none is similar enough or the limits
        (line length, time) leave the comparison out.
    """
    if len(key) > _MAX_FUZZY_CHARS:
        return None
    matcher = SequenceMatcher(None, autojunk=False)
    matcher.set_seq2(key)
    best_ratio, best_tags = 0.0, None
    for fact, tags in candidates.items():
        if len(fact) > _MAX_FUZZY_CHARS:
            continue
        if time.monotonic() > deadline:
            break
        matcher.set_seq1(fact)
        if matcher.real_quick_ratio() < minimum or matcher.quick_ratio() < minimum:
            continue
        ratio = matcher.ratio()
        if ratio > best_ratio:
            best_ratio, best_tags = ratio, tags
    return best_tags if best_ratio >= minimum else None


def _match_tags(
    key: str, facts: Dict[str, Tuple[str, ...]], allow_contained: bool, allow_fuzzy: bool, deadline: float
) -> Optional[Tuple[bool, Tuple[str, ...]]]:
    """Find the earlier or new fact(s) a merged line comes from.

    Args:
        key: Normalized merged line.
        facts: Normalized known facts mapped to their tags.
        allow_contained: Whether to look for facts contained in the line.
        allow_fuzzy: Whether to compare against every fact by similarity.
        deadline: ``time.monotonic()`` value after which no more fuzzy comparisons are made.

    Returns:
        ``(exact, tags)``: ``exact`` is True when the line is identical to a known fact; the tags
        may be empty for a fact stored without one. ``None`` when nothing matches.
    """
    if key in facts:
        return True, facts[key]
    # The model may have joined several facts into one line: every fact it contains counts.
    if allow_contained:
        contained = [tags for fact, tags in facts.items() if len(fact) >= _MIN_CONTAINED_CHARS and fact in key]
        if contained:
            return False, tuple(dict.fromkeys(tag for tags in contained for tag in tags))
    # Otherwise it may have reworded one fact: take the most similar one.
    if allow_fuzzy:
        similar = _most_similar(key, facts, _MIN_SIMILARITY, deadline)
        if similar is not None:
            return False, similar
    return None


def reattach_source_tags(
    merged_text: Optional[str], earlier_texts: Sequence[Optional[str]], new_tagged_text: str
) -> Optional[str]:
    """Put each fact's source tag back after the merge model rewrote the memory.

    The model is asked to keep the tags, but it may drop, move or invent them, so the code decides.
    A merged line identical to a known fact gets exactly that fact's tags. A line that contains
    known facts or rewords one gets their tags plus the known tags the model gave it. A line that
    matches nothing keeps the known tags the model gave it, else gets this save's tag if it resembles
    what is being saved, else stays untagged: wrongly claiming "told here" is worse than no tag.
    A tag the model made up is always dropped, and a fact stored without a tag stays without one.

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
                facts[key] = tuple(dict.fromkeys([*facts.get(key, ()), *tags]))
                if is_new:
                    new_facts[key] = facts[key]
    known_tags = {tag for tags in facts.values() for tag in tags}

    lines = merged_text.split("\n")
    allow_contained = len(merged_text) * len(facts) <= _MAX_CONTAIN_WORK
    allow_fuzzy = allow_contained and len(facts) * len(lines) <= _MAX_FUZZY_PAIRS
    deadline = time.monotonic() + _FUZZY_BUDGET_SECONDS
    result: List[str] = []
    for line in lines:
        clean, present = _split_fact(line)
        key = _normalize(clean)
        if not key:
            result.append(clean)
            continue
        given = tuple(tag for tag in present if tag in known_tags)
        match = _match_tags(key, facts, allow_contained, allow_fuzzy, deadline)
        if match is not None and match[0]:
            tags = match[1]
        elif match is not None:
            tags = tuple(dict.fromkeys([*match[1], *given]))
        elif given:
            tags = given
        elif allow_fuzzy:
            tags = _most_similar(key, new_facts, _MIN_SIMILARITY_TO_NEW, deadline) or ()
        else:
            tags = ()
        result.append(f"{clean} {' '.join(tags)}" if tags else clean)
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
