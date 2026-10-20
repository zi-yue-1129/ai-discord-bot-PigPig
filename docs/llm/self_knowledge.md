# Self-knowledge

How the bot knows what it can do, how to use its features, and which content it can see.
Nothing in it is a hand-kept list: it is read from the code that defines each thing, so
there is almost nothing to maintain.

## Where the bot gets its answers

| Question | Source (read at runtime) |
| --- | --- |
| Which slash commands exist, their parameters and choices | The loaded cogs (`@app_commands.command`, `@app_commands.describe`, `@app_commands.choices`) |
| What it can do while chatting | The AI tools registered under `llm/tools/`, grouped by file name |
| Which attachments it can open, with their limits | `ATTACHMENT_KINDS` in `llm/utils/attachment_processor.py` and `attachments.yaml` |
| How many messages it reads | `memory.yaml` (`short_term_limit`) |

Two things use this (`llm/self_knowledge.py`):

- **Always on.** The reply agent's system prompt ends with an "About yourself" block: what it
  can see (and what it cannot: sound, stickers, other file types) and the ability groups. About 450 tokens.
- **On demand.** The info agent has the `get_bot_guide(topic)` tool (`llm/tools/bot_guide.py`).
  It returns the full overview, or the details of the commands and abilities that match the
  topic, including parameters, choices and restrictions.

## When you change the bot

- **Add a slash command.** Give the command and every parameter a real description
  (`@app_commands.describe`). Nothing else. A test fails if a command has no description.
- **Add an AI tool.** Write a one-sentence description at the start of its docstring or
  `description`. It is grouped by the file it lives in. A test fails if the description is missing.
- **Add an attachment type.** Add an `AttachmentKind` to `ATTACHMENT_KINDS`. That one entry
  makes the bot open the file *and* tell users it can.
- **Usage that a description cannot carry** (buttons under the music player, how memory differs
  from knowledge): add a `GUIDE_NOTES` string to the cog class. It is optional, shown once
  after the commands of that cog, and found by whole-word search. See `YTMusic`, `ReminderCog`, `UserDataCog`.
- **Change what the bot sees in the history** (for example reading stickers): update the fixed
  sentences in `_describe_visible_content` in `llm/self_knowledge.py`; they describe
  `llm/memory/short_term.py`.

No prompt file needs editing, and the live `configs/prompt/` copies are not involved.
