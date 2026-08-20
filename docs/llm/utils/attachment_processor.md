### Create File: docs/llm/utils/attachment_processor.md
# File: `llm/utils/attachment_processor.py`

## Overview
Convert Discord Attachments to LangChain content_parts (base64 data URIs).

Supported types:
- image/* — resized and encoded as JPEG base64 image_url parts
- application/pdf — rendered page-by-page via pdf2image
- video/* — key-frame sampled via decord

Unsupported types and processing failures each return a single ``text`` part
so the calling agent always receives well-formed content.

## Classes

No classes defined in this file.

## Functions

### `_download(url) -> bytes`
Download a URL and return the raw bytes.  Args:     url: HTTP/HTTPS URL to fetch.  Returns:     Raw response bytes.  Raises:     aiohttp.ClientResponseError: If the server returns a non-2xx status.     aiohttp.ClientError: On network-level failures.

### `_pil_to_content_part(img) -> dict`
Encode a PIL Image as a LangChain ``image_url`` content part (JPEG base64).  Args:     img: PIL Image object in RGB mode.  Returns:     Dict with ``type`` == ``"image_url"`` and a ``data:image/jpeg;base64,…`` URL.

### `_resize_if_needed(img, max_dim) -> Image.Image`
Proportionally resize *img* so its longest side does not exceed *max_dim*.  Args:     img: Source PIL Image.     max_dim: Maximum allowed value for ``max(width, height)``.  Returns:     The original image if already within limits, otherwise a resized copy.

### `_decode_image(data, max_dimension) -> Image.Image`
Synchronously decode and resize an image; intended for thread-pool execution.  Args:     data: Raw image file bytes.     max_dimension: Maximum allowed value for the longest image side.  Returns:     RGB PIL Image, resized if necessary.

### `_process_image(data) -> list[dict]`
Decode raw image bytes, optionally resize, and encode as a content part.  Args:     data: Raw image file bytes.  Returns:     A single-element list containing an ``image_url`` content part.

### `_render_pdf(data, cfg) -> tuple[list, bool, list[int], int, int]`
Synchronously render PDF pages to PIL Images; intended for thread-pool execution.  Args:     data: Raw PDF file bytes.     cfg: ``_AttachmentPdfConfig`` instance with rendering parameters.  Returns:     Tuple of ``(pages, truncated, selected_indices, half, total_pages)`` where     *pages* is a list of PIL Images for the selected page range and *half* is     the count of front pages used when truncation occurred.

### `_process_pdf(data, filename) -> list[dict]`
Render PDF pages to images and encode each as a content part.  Page count drives DPI selection: - <= threshold_full  → dpi_full - <= threshold_medium → dpi_medium - else               → dpi_compressed  If total pages exceed ``max_pages``, the first and last ``max_pages // 2`` pages are sampled and a truncation notice is prepended.  Args:     data: Raw PDF file bytes.     filename: Original filename (used in log context).  Returns:     List of content parts — optionally a leading ``text`` truncation notice     followed by one ``image_url`` part per selected page.

### `_decode_video(data, cfg) -> list[Image.Image]`
Synchronously decode video key frames; intended for thread-pool execution.  Args:     data: Raw video file bytes.     cfg: ``_AttachmentVideoConfig`` instance with frame-sampling parameters.  Returns:     List of RGB PIL Images, one per sampled frame.

### `_process_video(data, filename) -> list[dict]`
Sample key frames from a video and encode each as a content part.  Frames are sampled at least ``min_interval_sec`` seconds apart.  If the resulting candidate count exceeds ``max_frames`` the candidates are uniformly subsampled.  Args:     data: Raw video file bytes.     filename: Original filename (used in log context).  Returns:     List of ``image_url`` content parts, one per sampled frame.

### `process_attachment(attachment) -> list[dict]`
Convert a Discord Attachment to a list of LangChain content_parts.  Dispatches to type-specific processors based on ``attachment.content_type``. Returns an empty list if attachment processing is globally disabled. Returns a ``text`` fallback part for unsupported MIME types or on any processing failure so the caller always receives well-formed content.  Args:     attachment: A ``discord.Attachment`` (or compatible mock) with         ``content_type``, ``filename``, and ``url`` attributes.  Returns:     List of dicts, each a LangChain content_part with ``"type"`` either     ``"image_url"`` or ``"text"``.  Empty list when globally disabled.
