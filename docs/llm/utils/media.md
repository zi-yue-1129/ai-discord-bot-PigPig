# File: `llm/utils/media.py`

## Overview
The `media.py` module provides comprehensive media processing utilities for the LLM system. It handles image standardization, video frame extraction, PDF processing, and attachment processing for various media formats.

## Functions

### `standardize_image(image, target_size) -> Any`
**Parameters:**
- `image`: PIL Image object to standardize
- `target_size`: Target dimensions tuple (width, height)

**Returns:**
- `PIL.Image`: Resized image to target dimensions

**Description:**
Resizes an image to the specified target dimensions for consistent processing.

### `is_valid_image(img, expected_size) -> Any`
**Parameters:**
- `img`: PIL Image object to validate
- `expected_size`: Expected dimensions tuple

**Returns:**
- `bool`: True if image matches expected size

**Description:**
Validates that an image meets the expected dimensions after standardization.

### `image_to_base64(pil_image) -> Any`
**Parameters:**
- `pil_image`: PIL Image object to convert

**Returns:**
- `str`: Base64-encoded image string (JPEG format)

**Description:**
Converts a PIL Image to base64-encoded JPEG string for transmission or storage.

**Process:**
1. **BytesIO Buffer**: Creates in-memory buffer
2. **JPEG Conversion**: Saves image as JPEG format
3. **Base64 Encoding**: Encodes bytes to UTF-8 string

### `encode_video(video_data) -> Any`
Performs encode_video operations.

### `safe_process_pdf(file_data) -> Any`
**Parameters:**
- `file_data`: Raw PDF file data as bytes

**Returns:**
- `List[PIL.Image]`: List of standardized page images

**Description:**
Safely converts PDF pages to standardized images using pdf2image.

**Processing Pipeline:**
1. **PDF Conversion**: Uses pdf2image to convert pages to images
2. **Standardization**: Resizes all pages to target dimensions
3. **Error Handling**: Returns empty list on conversion failures

### `process_attachment_data(message) -> Any`
Performs process_attachment_data operations.

