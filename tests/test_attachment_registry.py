"""One registry decides which attachments are opened and how they are described to the bot itself."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from llm.utils import attachment_processor


def _config(**overrides: Any) -> SimpleNamespace:
    """Build an attachment config shaped like the real one, with per-section overrides."""
    sections: Dict[str, Any] = {
        "enabled": True,
        "max_download_bytes": 50 * 1024 * 1024,
        "image": SimpleNamespace(enabled=True, max_dimension=1024),
        "pdf": SimpleNamespace(enabled=True, max_pages=7),
        "video": SimpleNamespace(enabled=True, max_frames=3),
    }
    sections.update(overrides)
    return SimpleNamespace(**sections)


def test_every_enabled_kind_is_described_with_its_live_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(attachment_processor, "attachment_config", _config())

    assert attachment_processor.describe_supported_attachments() == [
        "images (resized to fit 1024 px)",
        "PDF files (first 7 pages, read as images)",
        "videos (up to 3 still frames, no sound)",
    ]


def test_a_disabled_kind_is_not_described(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config(pdf=SimpleNamespace(enabled=False, max_pages=7))
    monkeypatch.setattr(attachment_processor, "attachment_config", config)

    assert attachment_processor.describe_supported_attachments() == [
        "images (resized to fit 1024 px)",
        "videos (up to 3 still frames, no sound)",
    ]


def test_nothing_is_described_when_attachments_are_switched_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(attachment_processor, "attachment_config", _config(enabled=False))

    assert attachment_processor.describe_supported_attachments() == []


@pytest.mark.asyncio
async def test_a_kind_added_to_the_registry_is_both_opened_and_described(monkeypatch: pytest.MonkeyPatch) -> None:
    async def read_audio(data: bytes, filename: str) -> list[dict]:
        return [{"type": "text", "text": f"[Transcript of {filename}: {data.decode()}]"}]

    async def download(url: str) -> bytes:
        return b"hello"

    audio = attachment_processor.AttachmentKind(
        name="audio",
        handles=lambda content_type: content_type.startswith("audio/"),
        settings=lambda: SimpleNamespace(enabled=True, max_seconds=30),
        process=read_audio,
        describe=lambda settings: f"audio clips (first {settings.max_seconds} seconds)",
    )
    monkeypatch.setattr(attachment_processor, "attachment_config", _config())
    monkeypatch.setattr(attachment_processor, "ATTACHMENT_KINDS", (*attachment_processor.ATTACHMENT_KINDS, audio))
    monkeypatch.setattr(attachment_processor, "_download", download)
    attachment = MagicMock(content_type="audio/mpeg", filename="song.mp3", url="https://example.com/a", size=10)

    parts = await attachment_processor.process_attachment(attachment)

    assert parts == [{"type": "text", "text": "[Transcript of song.mp3: hello]"}]
    assert attachment_processor.describe_supported_attachments()[-1] == "audio clips (first 30 seconds)"
