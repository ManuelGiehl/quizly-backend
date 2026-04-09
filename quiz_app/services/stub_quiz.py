"""Temporary quiz content until yt-dlp + Whisper + Gemini are wired in."""

from quiz_app.models import Question, Quiz


def _stub_title_desc(video_id: str) -> tuple[str, str]:
    title = f"Quiz for video {video_id}"
    description = "Placeholder (AI pipeline not connected yet)."
    return title, description


def _stub_question_rows():
    """Yield 10 rows with 4 options each (matches final product shape)."""
    for i in range(1, 11):
        opts = [
            f"Q{i} — option A",
            f"Q{i} — option B",
            f"Q{i} — option C",
            f"Q{i} — option D",
        ]
        yield {"title": f"Placeholder question {i}", "options": opts, "answer": opts[0]}


def create_stub_quiz(owner, canonical_url: str) -> Quiz:
    """Persist quiz + questions; ``canonical_url`` must already be normalized."""
    video_id = canonical_url.rsplit("v=", 1)[-1]
    title, description = _stub_title_desc(video_id)
    quiz = Quiz.objects.create(
        owner=owner,
        title=title,
        description=description,
        video_url=canonical_url,
    )
    for order, row in enumerate(_stub_question_rows(), start=1):
        Question.objects.create(
            quiz=quiz,
            question_title=row["title"],
            question_options=row["options"],
            answer=row["answer"],
            order=order,
        )
    return quiz
