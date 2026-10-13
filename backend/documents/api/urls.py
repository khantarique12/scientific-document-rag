
from django.urls import path

from .views import DocumentListCreateView, QuestionAnswerView


urlpatterns = [
    path(
        "",
        DocumentListCreateView.as_view(),
        name="document-list-create",
    ),
    path(
        "ask/",
        QuestionAnswerView.as_view(),
        name="document-ask",
    ),
]
