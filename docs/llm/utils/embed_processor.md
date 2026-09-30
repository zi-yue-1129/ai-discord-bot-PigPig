# File: `llm/utils/embed_processor.py`

## Overview
This file is part of the LLM integration and orchestration pipeline and handles its respective logic within the PigPig bot architecture. It is responsible for the operations defined in `llm/utils/embed_processor.py`.

## Classes

None

## Functions

### `process_embed(embed) -> list[dict]`
Convert a Discord Embed to LangChain content_parts.  Text fields (title, description, fields, url) are serialized as a single structured text part. Images and thumbnails are appended as image_url parts when ``attachment_config.embeds.include_images`` is enabled. Empty embeds (no text and no images) return an empty list.  Args:     embed: A Discord ``Embed`` object (or compatible mock) to convert.  Returns:     A list of content-part dicts compatible with the LangChain     ``content_parts`` format. Each dict has at minimum a ``"type"`` key     with value ``"text"`` or ``"image_url"``.
