"""Local Whisper transcription (requires ``ffmpeg`` on PATH)."""

from __future__ import annotations

import threading

import whisper

_cache: dict = {"name": None, "model": None}
_lock = threading.Lock()


class TranscriptionError(Exception):
    """Whisper model load or ``transcribe`` failed."""


def _load_whisper_model(model_name: str):
    try:
        return whisper.load_model(model_name)
    except Exception as exc:
        raise TranscriptionError(
            f"Could not load Whisper model {model_name!r}."
        ) from exc


def get_whisper_model(model_name: str):
    """Load and cache one Whisper model (thread-safe)."""
    with _lock:
        if _cache["model"] is not None and _cache["name"] == model_name:
            return _cache["model"]
        model = _load_whisper_model(model_name)
        _cache["model"] = model
        _cache["name"] = model_name
        return model


def transcribe_audio_file(audio_path: str, model_name: str) -> str:
    """Return plain text for one audio file path."""
    model = get_whisper_model(model_name)
    try:
        result = model.transcribe(audio_path)
    except Exception as exc:
        raise TranscriptionError("Whisper transcription failed.") from exc
    return (result.get("text") or "").strip()
