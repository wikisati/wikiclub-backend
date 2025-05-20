import json
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from authlib.integrations.django_client import OAuth
from .models import UserProfile, JWTSession
from .serializers import UserSerializer
import requests

oauth = OAuth()
oauth.register(
    name='mediawiki',
    client_id=settings.MEDIAWIKI_CLIENT_ID,
    client_secret=settings.MEDIAWIKI_CLIENT_SECRET,
    access_token_url=settings.MEDIAWIKI_TOKEN_URL,
    access_token_params=None,
    authorize_url=settings.MEDIAWIKI_AUTH_URL,
    authorize_params=None,
    api_base_url='https://en.wikipedia.org/w/api.php',
    client_kwargs={
        'scope': 'read',
        'token_endpoint_auth_method': 'client_secret_post',
    },
)

@csrf_exempt
@require_http_methods(['GET'])
def login(request):
    redirect_uri = settings.MEDIAWIKI_CALLBACK_URL
    return oauth.mediawiki.authorize_redirect(request, redirect_uri)

@csrf_exempt
@require_http_methods(['GET'])
def callback(request):
    token = oauth.mediawiki.authorize_access_token(request)
    if not token:
        return JsonResponse({'error': 'Failed to get access token'}, status=400)

    # Get user info from MediaWiki
    user_info = get_mediawiki_user_info(token['access_token'])
    if not user_info:
        return JsonResponse({'error': 'Failed to get user info'}, status=400)

    # Create or update user
    user, created = User.objects.get_or_create(
        username=user_info['name'],
        defaults={'email': user_info.get('email', '')}
    )

    # Create or update profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'mediawiki_username': user_info['name'],
            'mediawiki_email': user_info.get('email'),
            'mediawiki_edit_count': user_info.get('editcount', 0),
            'mediawiki_registration_date': datetime.fromisoformat(user_info.get('registration', '').replace('Z', '+00:00')),
            'last_login_time': datetime.now(),
        }
    )

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    # Store refresh token
    JWTSession.objects.create(
        user=user,
        refresh_token=refresh_token,
        expires_at=datetime.now() + timedelta(days=7)
    )

    response = JsonResponse({
        'user': UserSerializer(user).data,
        'access_token': access_token,
        'refresh_token': refresh_token
    })

    # Set HTTP-only cookies
    response.set_cookie(
        'access_token',
        access_token,
        httponly=True,
        secure=True,
        samesite='Lax',
        max_age=900  # 15 minutes
    )
    response.set_cookie(
        'refresh_token',
        refresh_token,
        httponly=True,
        secure=True,
        samesite='Lax',
        max_age=604800  # 7 days
    )

    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    user = request.user
    return JsonResponse(UserSerializer(user).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    # Clear JWT session
    JWTSession.objects.filter(user=request.user).delete()
    
    response = JsonResponse({'message': 'Successfully logged out'})
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response

def get_mediawiki_user_info(access_token):
    params = {
        'action': 'query',
        'meta': 'userinfo',
        'uiprop': 'editcount|registration|emailable|gender|groups',
        'format': 'json',
        'access_token': access_token
    }
    
    response = requests.get('https://en.wikipedia.org/w/api.php', params=params)
    if response.status_code != 200:
        return None
        
    data = response.json()
    if 'query' not in data or 'userinfo' not in data['query']:
        return None
        
    return data['query']['userinfo'] 