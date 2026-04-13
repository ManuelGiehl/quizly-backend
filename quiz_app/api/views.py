"""Quiz API views (CRUD-ish endpoints scoped to the authenticated owner).

The heavy lifting (YouTube → Whisper → Gemini) is triggered via serializers/services.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from quiz_app.models import Quiz

from .serializers import (
    QuizCreateSerializer,
    QuizDetailSerializer,
    QuizPartialUpdateSerializer,
)


def _quiz_queryset_for_user(user):
    """Base queryset for the current user (includes questions for serialization)."""
    return Quiz.objects.filter(owner=user).prefetch_related("questions")


def _quiz_by_pk_or_none(pk):
    """Fetch a quiz by PK including questions; return None if missing."""
    try:
        return Quiz.objects.prefetch_related("questions").get(pk=pk)
    except Quiz.DoesNotExist:
        return None


def _owned_quiz_or_error_response(request, pk):
    """Return (quiz, None) when owned; otherwise (None, Response) with 404/403."""
    quiz = _quiz_by_pk_or_none(pk)
    if quiz is None:
        return None, Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if quiz.owner_id != request.user.id:
        err = Response(
            {"detail": "You do not have permission to access this quiz."},
            status=status.HTTP_403_FORBIDDEN,
        )
        return None, err
    return quiz, None


def _patch_quiz_response(quiz, request, user):
    """PATCH handler: validate allowed fields, persist, and return refreshed detail."""
    serializer = QuizPartialUpdateSerializer(quiz, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    refreshed = _quiz_queryset_for_user(user).get(pk=quiz.pk)
    return Response(QuizDetailSerializer(refreshed).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def quiz_detail(request, pk):
    """Quiz detail endpoint (GET), partial update (PATCH), and delete (DELETE)."""
    quiz, err = _owned_quiz_or_error_response(request, pk)
    if err is not None:
        return err
    if request.method == "GET":
        return Response(QuizDetailSerializer(quiz).data)
    if request.method == "DELETE":
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    return _patch_quiz_response(quiz, request, request.user)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def quiz_list(request):
    """List quizzes for current user (GET) or create one from YouTube URL (POST)."""
    if request.method == "GET":
        quizzes = _quiz_queryset_for_user(request.user)
        return Response(QuizDetailSerializer(quizzes, many=True).data)
    serializer = QuizCreateSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    quiz = serializer.save()
    quiz = _quiz_queryset_for_user(request.user).get(pk=quiz.pk)
    return Response(QuizDetailSerializer(quiz).data, status=status.HTTP_201_CREATED)
