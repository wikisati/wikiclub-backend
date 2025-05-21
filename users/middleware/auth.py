# ✅ middleware/auth.py (fully reviewed)
from django.utils.deprecation import MiddlewareMixin
from users.models import CustomUser

class TokenAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            try:
                request.user = CustomUser.objects.get(access_token=token)
            except CustomUser.DoesNotExist:
                request.user = None