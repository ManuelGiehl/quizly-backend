from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from quiz_app.models import Quiz

from .serializers import QuizCreateSerializer, QuizDetailSerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def quiz_create(request):
    serializer = QuizCreateSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    quiz = serializer.save()
    quiz = Quiz.objects.prefetch_related("questions").get(pk=quiz.pk)
    out = QuizDetailSerializer(quiz)
    return Response(out.data, status=status.HTTP_201_CREATED)
