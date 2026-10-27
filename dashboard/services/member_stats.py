"""Erasing a member's cumulative stats from the procedural memory database."""

from __future__ import annotations

from typing import Optional

import aiosqlite

from cogs.memory.db.member_tables import MEMBER_STATS_TABLES


async def delete_member_stats(
    db: aiosqlite.Connection, user_id: str, guild_id: Optional[str] = None
) -> dict[str, int]:
    """Deletes a member's stats rows (without committing).

    Args:
        db: Open connection to the procedural database.
        user_id: The member.
        guild_id: Only this guild (default: every guild).

    Returns:
        Deleted row counts by table. A table the database does not have yet counts as 0.
    """
    where, params = "user_id = ?", [user_id]
    if guild_id is not None:
        where, params = where + " AND guild_id = ?", params + [guild_id]
    deleted: dict[str, int] = {}
    for table in MEMBER_STATS_TABLES:
        try:
            cursor = await db.execute(f"DELETE FROM {table} WHERE {where}", params)
        except aiosqlite.OperationalError as exc:
            if "no such table" not in str(exc):
                raise
            deleted[table] = 0
        else:
            deleted[table] = cursor.rowcount
    return deleted
