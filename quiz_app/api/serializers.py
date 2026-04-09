from rest_framework import serializers

from quiz_app.models import Question, Quiz
from quiz_app.services.stub_quiz import create_stub_quiz
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
            "questions",
        )


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
        return create_stub_quiz(request.user, canonical)
