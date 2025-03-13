from django.shortcuts import render
from rest_framework import generics
from .models import Subscription
from .serializers import SubscriptionSerializer
from rest_framework.permissions import AllowAny

class SubscriptionCreateView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
