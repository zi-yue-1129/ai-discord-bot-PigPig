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

### `is_processing_failure(parts) -> bool`
Return whether *parts* is the fallback emitted for a failed attachment.

### `_download(url) -> bytes`
Download a URL and return the raw bytes.

### `_pil_to_content_part(img) -> dict`
Encode a PIL Image as a LangChain ``image_url`` content part (JPEG base64).

### `_resize_if_needed(img, max_dim) -> Image.Image`
Proportionally resize *img* so its longest side does not exceed *max_dim*.

### `_decode_image(data, max_dimension) -> Image.Image`
Synchronously decode and resize an image; intended for thread-pool execution.

### `_process_image(data) -> list[...]`
Decode raw image bytes, optionally resize, and encode as a content part.

### `_render_pdf(data, cfg) -> tuple[...]`
Synchronously render PDF pages to PIL Images; intended for thread-pool execution.

### `_process_pdf(data, filename) -> list[...]`
Render PDF pages to images and encode each as a content part.

### `_decode_video(data, cfg) -> list[...]`
Synchronously decode video key frames; intended for thread-pool execution.

### `_process_video(data, filename) -> list[...]`
Sample key frames from a video and encode each as a content part.

### `process_attachment(attachment) -> list[...]`
Convert a Discord Attachment to a list of LangChain content_parts.
