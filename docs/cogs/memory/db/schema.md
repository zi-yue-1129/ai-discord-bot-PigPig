# File: `cogs/memory/db/schema.py`

## Overview
Database schema creation for the memory cog.

Contains SQL statements to create required tables and indexes, and performs
small migrations if needed.

All comments and logs are written in English per project rules.

## Functions

### `create_tables(conn) -> None`
Create necessary tables and indexes on the provided SQLite connection.

This mirrors the previous implementation in DatabaseManager._create_tables.
