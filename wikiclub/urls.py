from django.contrib import admin
from django.urls import path
from users import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/init', views.auth_init),
    path('api/auth/callback', views.auth_callback),
]
