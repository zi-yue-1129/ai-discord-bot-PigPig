# File: `llm/utils/media.py`

## Overview
This file is part of the `llm` subsystem. It is responsible for `media` related functionality within the PigPig system, contributing to the LLM pipeline and orchestration.

## Functions

### `standardize_image(image, target_size) -> Any`
Provides `standardize_image` functionality. Internally, it interacts with methods like `resize`.

### `is_valid_image(img, expected_size) -> Any`
Provides `is_valid_image` functionality. Executes the underlying business logic for this operation.

### `image_to_base64(pil_image) -> Any`
Provides `image_to_base64` functionality. Internally, it interacts with methods like `BytesIO` and `save`.

### `encode_video(video_data) -> Any`
Provides `encode_video` functionality. Internally, it interacts with methods like `info` and `BytesIO`.

### `safe_process_pdf(file_data) -> Any`
Provides `safe_process_pdf` functionality. Internally, it interacts with methods like `convert_from_bytes` and `standardize_image`.

### `process_attachment_data(message) -> Any`
Provides `process_attachment_data` functionality. Internally, it interacts with methods like `ClientSession` and `report_error`.
