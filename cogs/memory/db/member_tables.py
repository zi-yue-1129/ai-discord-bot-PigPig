"""Which procedural-database tables hold what a member said or did, for erasing it.

Every erase path reads these lists (the dashboard's ``delete_member_stats`` and
``/memory clear``), so a new table cannot be missed by one of them.
"""

# Tables keyed by (user_id, guild_id) that are built from a member's messages.
MEMBER_STATS_TABLES = ("user_stats", "user_public_terms")

# The columns of ``user_stats`` that hold the member's words and emojis (the rest are counts).
USER_STATS_TEXT_COLUMNS = ("top_words", "top_emojis")
