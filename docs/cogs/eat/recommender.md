# File: `cogs/eat/recommender.py`

## Overview
Lightweight Weighted Recommender.

## Classes

### `WeightedRecommender`
Weighted recommender based on user rating history.

- **Attributes**:
  - None specified.

- **Methods**:
  - `__init__(db: DB) -> Any`: No description provided.
  - `suggest_keyword(discord_id: str, available_keywords: list[str]) -> str`: Suggest the next search keyword based on user preferences.
  - `rank_candidates(discord_id: str, candidates: list[dict]) -> list[dict]`: Rank candidate restaurants, excluding disliked ones and weighting liked categories.

## Functions

No module-level functions defined in this file.
