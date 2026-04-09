from django.urls import path

from . import views

urlpatterns = [
    path("quizzes/", views.quiz_create, name="quiz-create"),
]
