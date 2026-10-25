"""The server quiz: questions made from episodic memories, and how answers are scored.

Each question comes from one memory, so its answer can be shown with a source (channel, day
and a link to the original messages). A question is only used when its correct option really
appears in that memory, which keeps the model from making facts up.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence

OPTION_COUNT = 4
ANSWER_SECONDS = 20
# Points for a correct answer: the base plus a bonus that shrinks to 0 at the deadline.
BASE_POINTS = 500
SPEED_POINTS = 500

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)
_SPACES_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class QuizQuestion:
    """One multiple-choice question and where it came from.

    Attributes:
        question: The question text.
        options: Exactly ``OPTION_COUNT`` distinct options.
        answer: Index of the correct option.
        channel_id: Channel of the memory the question was made from.
        timestamp: When that conversation started (UNIX time), if known.
        jump_url: Link to the original messages, if known.
    """

    question: str
    options: Sequence[str]
    answer: int
    channel_id: Optional[str] = None
    timestamp: Optional[float] = None
    jump_url: Optional[str] = None


def _normalise(text: str) -> str:
    return _SPACES_RE.sub("", str(text)).casefold()


def parse_question(reply: str, memory_text: str, metadata: Mapping[str, Any]) -> Optional[QuizQuestion]:
    """Builds a question from the model's JSON reply; None when it is malformed or not grounded.

    The reply must hold ``question``, ``options`` (4 distinct, non-empty) and ``answer`` (0-3),
    and the correct option must appear in ``memory_text``.
    """
    match = _JSON_RE.search(reply or "")
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    question = str(data.get("question") or "").strip()
    options = data.get("options")
    answer = data.get("answer")
    if not question or not isinstance(options, list) or len(options) != OPTION_COUNT:
        return None
    options = [str(option).strip()[:80] for option in options]
    if any(not option for option in options) or len({_normalise(o) for o in options}) != OPTION_COUNT:
        return None
    if not isinstance(answer, int) or isinstance(answer, bool) or not 0 <= answer < OPTION_COUNT:
        return None
    if _normalise(options[answer]) not in _normalise(memory_text):
        return None
    timestamp = metadata.get("start_timestamp") or metadata.get("timestamp")
    try:
        timestamp = float(timestamp) if timestamp is not None else None
    except (TypeError, ValueError):
        timestamp = None
    return QuizQuestion(
        question=question[:300],
        options=options,
        answer=answer,
        channel_id=str(metadata["channel_id"]) if metadata.get("channel_id") else None,
        timestamp=timestamp,
        jump_url=metadata.get("jump_url") or None,
    )


def usable_memory(metadata: Mapping[str, Any], content: str, hidden: Sequence[int]) -> bool:
    """Whether a memory may become a question: it has text and not every author opted out."""
    if len((content or "").strip()) < 20:
        return False
    authors = {str(a) for a in metadata.get("author_ids") or []}
    return not authors or not authors <= {str(h) for h in hidden}


def points_for(elapsed: float, seconds: float = ANSWER_SECONDS) -> int:
    """Points for a correct answer given after ``elapsed`` seconds."""
    left = max(0.0, min(1.0, 1 - elapsed / seconds))
    return BASE_POINTS + round(SPEED_POINTS * left)


@dataclass
class QuizRound:
    """Answers to one question: each player's first answer counts."""

    question: QuizQuestion
    started_at: float
    answers: Dict[int, tuple] = field(default_factory=dict)

    def answer(self, user_id: int, option: int, now: float) -> bool:
        """Records an answer; False when the player already answered."""
        if user_id in self.answers:
            return False
        self.answers[user_id] = (option, now - self.started_at)
        return True

    def points(self) -> Dict[int, int]:
        """Points earned this round, for the players who answered correctly."""
        return {
            user_id: points_for(elapsed)
            for user_id, (option, elapsed) in self.answers.items()
            if option == self.question.answer
        }


@dataclass
class QuizScoreboard:
    """Running totals across a game."""

    totals: Dict[int, int] = field(default_factory=dict)

    def add(self, points: Mapping[int, int]) -> None:
        for user_id, value in points.items():
            self.totals[user_id] = self.totals.get(user_id, 0) + value

    def standings(self, limit: int = 5) -> List[tuple]:
        return sorted(self.totals.items(), key=lambda item: (-item[1], item[0]))[:limit]
