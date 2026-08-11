# File: `llm/utils/attachment_processor.py`

## Overview
Convert Discord Attachments to LangChain content_parts (base64 data URIs).

Supported types:
- image/* — resized and encoded as JPEG base64 image_url parts
- application/pdf — rendered page-by-page via pdf2image
- video/* — key-frame sampled via decord

Unsupported types and processing failures each return a single ``text`` part
so the calling agent always receives well-formed content.

## Functions

### `process_attachment(attachment) -> list[dict]`
Convert a Discord Attachment to a list of LangChain content_parts.

Dispatches to type-specific processors based on ``attachment.content_type``.
Returns an empty list if attachment processing is globally disabled.
Returns a ``text`` fallback part for unsupported MIME types or on any
processing failure so the caller always receives well-formed content.

Args:
    attachment: A ``discord.Attachment`` (or compatible mock) with
        ``content_type``, ``filename``, and ``url`` attributes.

Returns:
    List of dicts, each a LangChain content_part with ``"type"`` either
    ``"image_url"`` or ``"text"``.  Empty list when globally disabled.
