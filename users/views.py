import os
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response

User = get_user_model()

@api_view(['GET'])
def auth_init(request):
    state = request.GET.get("next", "/")
    url = (
        "https://meta.wikimedia.org/w/rest.php/oauth2/authorize"
        f"?client_id={settings.WIKI_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={settings.WIKI_REDIRECT_URI}"
        f"&state={state}"
    )
    return Response({"redirect": url})


@api_view(['GET'])
def auth_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state", "/")

    token_url = "https://meta.wikimedia.org/w/rest.php/oauth2/access_token"
    user_url = "https://meta.wikimedia.org/w/rest.php/oauth2/resource/profile"

    # Step 1: Exchange code for access token
    token_response = requests.post(token_url, data={
        "client_id": settings.WIKI_CLIENT_ID,
        "client_secret": settings.WIKI_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.WIKI_REDIRECT_URI,
    })

    if settings.DEBUG:
        print("Token Response:", token_response.status_code, token_response.text)

    if token_response.status_code != 200:
        return Response({"detail": "Failed to exchange token"}, status=400)

    access_token = token_response.json().get("access_token")
    if not access_token:
        return Response({"detail": "Access token not received"}, status=400)

    # Step 2: Fetch user profile
    profile_response = requests.get(user_url, headers={"Authorization": f"Bearer {access_token}"})
    if profile_response.status_code != 200:
        return Response({"detail": "Failed to fetch user profile"}, status=400)

    profile = profile_response.json()
    if settings.DEBUG:
        print("Wikimedia Profile:", profile)

    # Fallback to avoid missing keys
    wiki_id = profile.get("sub")
    username = profile.get("preferred_username") or profile.get("username") or wiki_id
    real_name = profile.get("name", "")

    if not wiki_id or not username:
        return Response({"detail": "Missing user ID or username"}, status=400)

    # Step 3: Create or retrieve user
    user, _ = User.objects.get_or_create(
        wiki_id=wiki_id,
        defaults={
            "username": username,
            "first_name": real_name,
        }
    )

    # Step 4: Redirect to frontend with user name (for now)
    return redirect(f"https://wikiclub.in/dashboard?name={user.first_name or user.username}")
