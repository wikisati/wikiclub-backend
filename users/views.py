import os
import requests
import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

User = get_user_model()

@api_view(['GET'])
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
def auth_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state", "/")

    token_url = "https://meta.wikimedia.org/w/rest.php/oauth2/access_token"
    user_url = "https://meta.wikimedia.org/w/rest.php/oauth2/resource/profile"

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

    profile_response = requests.get(user_url, headers={"Authorization": f"Bearer {access_token}"})
    if profile_response.status_code != 200:
        return Response({"detail": "Failed to fetch user profile"}, status=400)

    profile = profile_response.json()
    if settings.DEBUG:
        print("Wikimedia Profile:", profile)

    wiki_id = profile.get("sub")
    username = profile.get("preferred_username") or profile.get("username") or wiki_id
    real_name = profile.get("name", "")

    if not wiki_id or not username:
        return Response({"detail": "Missing user ID or username"}, status=400)

    user, _ = User.objects.get_or_create(
        wiki_id=wiki_id,
        defaults={"username": username, "first_name": real_name}
    )
    user.access_token = access_token
    user.save()

    response = redirect(f"https://wikiclub.in/dashboard?name={user.first_name or user.username}")
    response.set_cookie("wikiclub_token", access_token, httponly=True, samesite="Lax")
    return response


@api_view(['GET'])
def me_view(request):
    token = request.COOKIES.get("wikiclub_token")
    if not token:
        return Response({"detail": "Not authenticated"}, status=401)

    user_url = "https://meta.wikimedia.org/w/rest.php/oauth2/resource/profile"
    profile_response = requests.get(user_url, headers={"Authorization": f"Bearer {token}"})
    if profile_response.status_code != 200:
        return Response({"detail": "Failed to fetch user profile"}, status=400)

    profile = profile_response.json()
    return Response({
        "name": profile.get("name"),
        "username": profile.get("preferred_username") or profile.get("username"),
        "wiki_id": profile.get("sub")
    })


@api_view(['GET'])
def stats_view(request):
    token = request.COOKIES.get("wikiclub_token")
    if not token:
        return Response({"detail": "Not authenticated"}, status=401)

    return Response({
        "total_edits": 184,
        "bytes_added": 32000,
        "top_projects": ["enwiki", "wikidata", "commons"]
    })


@api_view(['POST'])
def logout_view(request):
    response = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
    response.delete_cookie("wikiclub_token")
    return response


@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok"})


@api_view(['GET'])
def get_current_user(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return Response({"detail": "Unauthorized"}, status=401)

    try:
        user = User.objects.get(access_token=token)
        return Response({
            "name": user.first_name or user.username,
            "wiki_id": user.wiki_id,
            "joined": user.date_joined,
        })
    except User.DoesNotExist:
        return Response({"detail": "Invalid token"}, status=401)


@api_view(['GET'])
def get_stats(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        user = User.objects.get(access_token=token)
        return Response({
            "edits": user.edit_count,
            "bytes_added": 4200,
            "top_projects": ["enwiki", "wikidata", "commons"],
        })
    except User.DoesNotExist:
        return Response({"detail": "Invalid token"}, status=401)


@api_view(["POST"])
def logout(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        user = User.objects.get(access_token=token)
        user.access_token = None
        user.save()
        return Response({"detail": "Logged out successfully"})
    except User.DoesNotExist:
        return Response({"detail": "Invalid token"}, status=401)


@api_view(['GET'])
def whoami(request):
    token = request.GET.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return Response({"detail": "Missing access token"}, status=401)

    try:
        user = User.objects.get(access_token=token)
    except User.DoesNotExist:
        return Response({"detail": "Invalid token"}, status=401)

    return JsonResponse({
        "name": user.first_name or user.username,
        "username": user.username,
        "wiki_id": user.wiki_id,
        "joined": user.date_joined.strftime("%Y-%m-%d"),
    })


@api_view(['GET'])
def user_stats(request):
    token = request.GET.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return Response({"detail": "Missing access token"}, status=401)

    try:
        user = User.objects.get(access_token=token)
    except User.DoesNotExist:
        return Response({"detail": "Invalid token"}, status=401)

    wiki_id = user.wiki_id
    if not wiki_id:
        return Response({"detail": "No wiki_id found"}, status=400)

    base_url = "https://wikimedia.org/api/rest_v1"
    headers = {"User-Agent": "WikiClubSATI/1.0"}

    meta_resp = requests.get(f"{base_url}/metrics/edits/per-user/{wiki_id}/all-projects/all-editor-types/monthly/2023/01/01/2025/12/31", headers=headers)
    edit_data = meta_resp.json() if meta_resp.status_code == 200 else {}

    total_edits = sum(point["edits"] for point in edit_data.get("items", []))

    bytes_resp = requests.get(f"{base_url}/metrics/bytes-added/per-user/{wiki_id}/all-projects/all-editor-types/monthly/2023/01/01/2025/12/31", headers=headers)
    bytes_data = bytes_resp.json() if bytes_resp.status_code == 200 else {}

    total_bytes = sum(point["net_bytes_diff"] for point in bytes_data.get("items", []))

    today = datetime.date.today()
    contrib_days = {}
    for point in edit_data.get("items", []):
        timestamp = point["timestamp"]
        count = point["edits"]
        if count > 0:
            date_key = f"{timestamp[:4]}-{timestamp[4:6]}"
            contrib_days[date_key] = contrib_days.get(date_key, 0) + count

    return JsonResponse({
        "wiki_id": wiki_id,
        "total_edits": total_edits,
        "total_bytes": total_bytes,
        "active_months": contrib_days,
    })
