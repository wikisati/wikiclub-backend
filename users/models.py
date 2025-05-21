from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    wiki_id = models.CharField(max_length=255, unique=True)
    access_token = models.TextField(blank=True, null=True)
    edit_count = models.IntegerField(default=0)
    registration_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.username or self.wiki_id
