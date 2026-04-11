from rest_framework import serializers

from quiz_app.models import Question, Quiz
from quiz_app.services.gemini_quiz import GeminiQuizError
from quiz_app.services.quiz_from_video import create_quiz_from_youtube
from quiz_app.services.transcription import TranscriptionError
from quiz_app.services.youtube import normalize_youtube_watch_url


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = (
            "id",
            "question_title",
            "question_options",
            "answer",
            "created_at",
            "updated_at",
        )


class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = (
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "transcript",
            "questions",
        )


class QuizPartialUpdateSerializer(serializers.ModelSerializer):
    """PATCH: only ``title`` and ``description`` (per API contract)."""

    class Meta:
        model = Quiz
        fields = ("title", "description")
        extra_kwargs = {
            "title": {"required": False, "allow_blank": False},
            "description": {"required": False, "allow_blank": True},
        }


class QuizCreateSerializer(serializers.Serializer):
    url = serializers.URLField()

    def validate_url(self, value):
        try:
            return normalize_youtube_watch_url(value)
        except ValueError as exc:
            raise serializers.ValidationError("Invalid YouTube URL.") from exc

    def create(self, validated_data):
        request = self.context["request"]
        canonical = validated_data["url"]
        try:
            return create_quiz_from_youtube(request.user, canonical)
        except (ValueError, TranscriptionError, GeminiQuizError) as exc:
            raise serializers.ValidationError({"url": str(exc)}) from exc
