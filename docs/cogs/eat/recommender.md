# File: `cogs/eat/recommender.py`

## Overview
Lightweight Weighted Recommender.

Replaces the PyTorch LSTM model with a real-time weighted algorithm based on user rating history.
Calculates preference vectors directly from the DB and ranks candidate restaurants without training.

## Classes

### `WeightedRecommender`
Weighted recommender based on user rating history.

- **Attributes**:
  - `db` (`Any`): Instance attribute managing db.

- **Methods**:
  - `suggest_keyword(discord_id, available_keywords) -> str`: Suggest the next search keyword based on user preferences.  Prioritizes tags/keywords the user has liked; chooses randomly if no history exists.  Args:     discord_id: Server or user ID.     available_keywords: List of existing keywords in the database.  Returns:     Suggested search keyword string.
  - `rank_candidates(discord_id, candidates) -> list[dict]`: Rank candidate restaurants, excluding disliked ones and weighting liked categories.  Args:     discord_id: Server or user ID.     candidates: List of PlaceResult dictionaries (from Provider).  Returns:     Sorted list of PlaceResult dictionaries (higher score first).
