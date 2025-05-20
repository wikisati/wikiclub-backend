import requests, os
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

    # Exchange code for token
    r = requests.post(token_url, data={
        "client_id": settings.WIKI_CLIENT_ID,
        "client_secret": settings.WIKI_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.WIKI_REDIRECT_URI,
    })
    access_token = r.json().get("access_token")

    # Fetch user profile
    r = requests.get(user_url, headers={"Authorization": f"Bearer {access_token}"})
    profile = r.json()
    wiki_id = profile["sub"]

    user, _ = User.objects.get_or_create(wiki_id=wiki_id, defaults={
        "username": profile["preferred_username"],
        "first_name": profile.get("name", ""),
    })

    # Return frontend a redirect with user info (or set cookie instead)
    return redirect(f"https://wikiclub.in/dashboard?name={user.first_name}")
