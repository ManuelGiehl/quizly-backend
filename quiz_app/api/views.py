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
    return Quiz.objects.filter(owner=user).prefetch_related("questions")


def _quiz_by_pk_or_none(pk):
    try:
        return Quiz.objects.prefetch_related("questions").get(pk=pk)
    except Quiz.DoesNotExist:
        return None


def _owned_quiz_or_error_response(request, pk):
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
    serializer = QuizPartialUpdateSerializer(quiz, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    refreshed = _quiz_queryset_for_user(user).get(pk=quiz.pk)
    return Response(QuizDetailSerializer(refreshed).data)


@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def quiz_detail(request, pk):
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
    if request.method == "GET":
        quizzes = _quiz_queryset_for_user(request.user)
        return Response(QuizDetailSerializer(quizzes, many=True).data)
    serializer = QuizCreateSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    quiz = serializer.save()
    quiz = _quiz_queryset_for_user(request.user).get(pk=quiz.pk)
    return Response(QuizDetailSerializer(quiz).data, status=status.HTTP_201_CREATED)
