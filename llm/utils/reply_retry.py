"""Asks the reply model once more when its reply is empty.

The live Qwen sometimes answers with nothing postable and no tool call: completely empty
output, or only an action written as text ("[add_reaction: 🤖]"), which is hidden. The same
request asked again almost always gets a real answer, so one more attempt is made before the
bot posts its "I don't know what to say" fallback. A reply with a tool call is never asked
again, so an action never runs twice.
"""

from __future__ import annotations

from typing import Awaitable, Callable, List, Sequence

from langchain_core.messages import BaseMessage, HumanMessage

from llm.utils.send_message import EmptyReplyError

EMPTY_REPLY_REMINDER = (
    "[System reminder, not a user message] Your last reply was empty. Answer the latest user message now: "
    "write your reply inside <som> ... <eom>, and perform any action the user asked for "
    "(nickname, reaction, sticker) with a real function call after <eom>, never as text."
)


async def run_with_empty_retry(
    attempt: Callable[[List[BaseMessage], bool], Awaitable[str]],
    messages: Sequence[BaseMessage],
    on_empty: Callable[[EmptyReplyError], None],
) -> str:
    """Runs the reply once, and once more with a reminder when the first reply is empty.

    Args:
        attempt: Streams one reply for the given messages. Its second argument tells whether
            an empty reply may post the fallback (True) or must raise ``EmptyReplyError``
            without posting anything (False).
        messages: The reply agent's messages; not modified.
        on_empty: Called with the error of an empty first reply, before the retry.

    Returns:
        The result of the attempt that answered.
    """
    try:
        return await attempt(list(messages), False)
    except EmptyReplyError as empty:
        on_empty(empty)
    return await attempt([*messages, HumanMessage(content=EMPTY_REPLY_REMINDER)], True)
