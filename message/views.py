from django.shortcuts import render
from rest_framework import generics
from .models import Message
from .serializers import MessageSerializer
from rest_framework.permissions import AllowAny

class MessageCreateView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
