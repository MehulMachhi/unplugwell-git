from django.db import models
from django.contrib.sites.models import Site
# Create your models here.

class Subscription(models.Model):
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    email = models.EmailField()