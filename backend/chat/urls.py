from django.urls import path
from .views import ChatView, ChatStreamView

urlpatterns = [
    path('', ChatView.as_view(), name='chat'),
    path('stream/<int:chat_id>/', ChatStreamView.as_view(), name='chat_stream'),
]