import re

with open("cogs/memory/services/message_tracker.py", "r") as f:
    content = f.read()

# Replace the redundant channel_state fetch
bad_fetch = '''            # Get previous summary for context
            channel_state = await self.storage.get_channel_memory_state(channel.id)
            previous_summary = channel_state.get("last_summary_text", "") if channel_state else ""'''

good_fetch = '''            # Get previous summary for context
            previous_summary = state.get("last_summary_text", "") if state else ""'''

content = content.replace(bad_fetch, good_fetch)

with open("cogs/memory/services/message_tracker.py", "w") as f:
    f.write(content)
