from django.contrib import admin

from quiz_app.models import Question, Quiz


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "video_url", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "video_url", "owner__username")
    inlines = (QuestionInline,)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "quiz", "question_title", "order", "created_at")
    list_filter = ("created_at",)
    search_fields = ("question_title", "quiz__title")
