from django.urls import path
from .views import MessageCreateView

urlpatterns = [
    path('message/', MessageCreateView.as_view(), name='message-create'),
]
