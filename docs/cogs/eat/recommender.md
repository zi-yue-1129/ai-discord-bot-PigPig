# File: `cogs/eat/recommender.py`

## Overview
Lightweight Weighted Recommender.

Replaces the PyTorch LSTM model with a real-time weighted algorithm based on user rating history.
Calculates preference vectors directly from the DB and ranks candidate restaurants without training.

## Classes

### `WeightedRecommender`
Weighted recommender based on user rating history.

- **Attributes**:
  - `db` (`Any`): Attribute holding db data.

- **Methods**:
  - `__init__(db: DB) -> Any`: Executes __init__ logic.
  - `suggest_keyword(discord_id: str, available_keywords: list[str]) -> str`: Suggest the next search keyword based on user preferences.
  - `rank_candidates(discord_id: str, candidates: list[dict]) -> list[dict]`: Rank candidate restaurants, excluding disliked ones and weighting liked categories.

## Functions

No top-level functions defined.
