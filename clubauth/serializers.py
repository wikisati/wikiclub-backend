from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'mediawiki_username',
            'mediawiki_email',
            'mediawiki_edit_count',
            'mediawiki_registration_date',
            'last_login_time',
            'avatar_url'
        ]

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(source='userprofile', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'profile'] 