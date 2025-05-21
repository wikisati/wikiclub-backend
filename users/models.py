from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    wiki_id = models.CharField(max_length=255, unique=True)
    avatar = models.URLField(blank=True, null=True)
