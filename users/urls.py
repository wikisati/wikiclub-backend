from django.urls import path
from .views import (
    auth_init,
    auth_callback,
    get_current_user,
    user_stats,
    logout_view,
    health_check
)

urlpatterns = [
    path("auth/init", auth_init),
    path("auth/callback", auth_callback),
    path("me", get_current_user),
    path("stats", user_stats),
    path("logout", logout_view),
    path("health", health_check),
]
