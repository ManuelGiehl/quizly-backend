from django.urls import path

from . import views

urlpatterns = [
    path("quizzes/", views.quiz_list, name="quiz-list"),
    path("quizzes/<int:pk>/", views.quiz_detail, name="quiz-detail"),
]
