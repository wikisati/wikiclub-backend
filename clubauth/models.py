from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mediawiki_username = models.CharField(max_length=255, unique=True)
    mediawiki_email = models.EmailField(null=True, blank=True)
    mediawiki_edit_count = models.IntegerField(default=0)
    mediawiki_registration_date = models.DateTimeField(null=True)
    last_login_time = models.DateTimeField(default=timezone.now)
    avatar_url = models.URLField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.mediawiki_username}'s profile"

class JWTSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    refresh_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'expires_at']),
        ] 