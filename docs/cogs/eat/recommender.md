# File: `cogs/eat/recommender.py`

## Overview
Lightweight Weighted Recommender.

Replaces the PyTorch LSTM model with a real-time weighted algorithm based on user rating history.
Calculates preference vectors directly from the DB and ranks candidate restaurants without training.

## Classes

### `WeightedRecommender`
Weighted recommender based on user rating history.

- **Attributes**:
  - `db` (`Any`): Instance attribute for db.

- **Methods**:
  - `__init__(db) -> Any`: Handles the `__init__` functionality. Executes the underlying business logic for this operation.
  - `suggest_keyword(discord_id, available_keywords) -> str`: Suggest the next search keyword based on user preferences.
  - `rank_candidates(discord_id, candidates) -> list[...]`: Rank candidate restaurants, excluding disliked ones and weighting liked categories.
