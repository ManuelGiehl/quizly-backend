from django.urls import path

from . import views

urlpatterns = [
    path("quizzes/", views.quiz_list, name="quiz-list"),
]
