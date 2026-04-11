"""YouTube URL → audio (yt-dlp) → Whisper → Gemini JSON → quiz + questions in DB."""

from __future__ import annotations

import uuid
from pathlib import Path

from django.conf import settings

from quiz_app.models import Question, Quiz
from quiz_app.services.gemini_quiz import generate_quiz_from_transcript
from quiz_app.services.transcription import transcribe_audio_file
from quiz_app.services.youtube import download_best_audio, extract_youtube_metadata


def _title_from_metadata(meta: dict, fallback_video_id: str) -> str:
    raw = meta.get("title")
    if isinstance(raw, str) and (t := raw.strip()):
        return t[:255]
    return f"Quiz for video {fallback_video_id}"


def _ensure_audio_work_dir() -> Path:
    root = Path(settings.BASE_DIR) / "media" / "quizly_audio"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _download_temp_audio(canonical_url: str, work: Path, stem: str) -> str:
    out_tmpl = str(work / f"{stem}.%(ext)s")
    return download_best_audio(canonical_url, out_tmpl)


def _unlink_audio(path: str) -> None:
    Path(path).unlink(missing_ok=True)


def _persist_quiz_and_questions(owner, url, transcript, payload) -> Quiz:
    quiz = Quiz.objects.create(
        owner=owner,
        title=payload["title"],
        description=payload["description"],
        video_url=url,
        transcript=transcript,
    )
    for order, row in enumerate(payload["questions"], start=1):
        Question.objects.create(
            quiz=quiz,
            question_title=row["question_title"],
            question_options=row["question_options"],
            answer=row["answer"],
            order=order,
        )
    return quiz


def _title_and_transcript(canonical_url: str) -> tuple[str, str]:
    video_id = canonical_url.rsplit("v=", 1)[-1]
    meta = extract_youtube_metadata(canonical_url)
    title = _title_from_metadata(meta, video_id)
    stem = uuid.uuid4().hex
    work = _ensure_audio_work_dir()
    audio_path = _download_temp_audio(canonical_url, work, stem)
    try:
        text = transcribe_audio_file(audio_path, settings.WHISPER_MODEL)
    finally:
        _unlink_audio(audio_path)
    return title, text


def create_quiz_from_youtube(owner, canonical_url: str) -> Quiz:
    """Full pipeline: metadata + download + Whisper + Gemini → persisted quiz."""
    _yt_title, transcript = _title_and_transcript(canonical_url)
    if not transcript.strip():
        raise ValueError("Transcript is empty; cannot generate a quiz.")
    payload = generate_quiz_from_transcript(transcript)
    return _persist_quiz_and_questions(owner, canonical_url, transcript, payload)
