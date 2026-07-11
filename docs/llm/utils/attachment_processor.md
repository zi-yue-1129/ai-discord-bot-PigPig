# File: `llm/utils/attachment_processor.py`

## Overview
This file belongs to the LLM Pipeline Subsystem. Its core responsibility is to handle logic related to `attachment_processor.py`, providing vital integrations within the PigPig bot ecosystem.
Convert Discord Attachments to LangChain content_parts (base64 data URIs).

Supported types:
- image/* — resized and encoded as JPEG base64 image_url parts
- application/pdf — rendered page-by-page via pdf2image
- video/* — key-frame sampled via decord

Unsupported types and processing failures each return a single ``text`` part
so the calling agent always receives well-formed content.

## Classes

## Functions

### `_download(url: str) -> bytes`
Download a URL and return the raw bytes.

### `_pil_to_content_part(img: Image.Image) -> dict`
Encode a PIL Image as a LangChain ``image_url`` content part (JPEG base64).

### `_resize_if_needed(img: Image.Image, max_dim: int) -> Image.Image`
Proportionally resize *img* so its longest side does not exceed *max_dim*.

### `_decode_image(data: bytes, max_dimension: int) -> Image.Image`
Synchronously decode and resize an image; intended for thread-pool execution.

### `_process_image(data: bytes) -> list[dict]`
Decode raw image bytes, optionally resize, and encode as a content part.

### `_render_pdf(data: bytes, cfg: object) -> tuple[Tuple]`
Synchronously render PDF pages to PIL Images; intended for thread-pool execution.

### `_process_pdf(data: bytes, filename: str) -> list[dict]`
Render PDF pages to images and encode each as a content part.

### `_decode_video(data: bytes, cfg: object) -> list[Image.Image]`
Synchronously decode video key frames; intended for thread-pool execution.

### `_process_video(data: bytes, filename: str) -> list[dict]`
Sample key frames from a video and encode each as a content part.

### `process_attachment(attachment: discord.Attachment) -> list[dict]`
Convert a Discord Attachment to a list of LangChain content_parts.
