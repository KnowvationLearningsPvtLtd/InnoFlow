from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from users.views import RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

def home(request):
    return HttpResponse("Welcome to the API. Use /api/auth/register/ or /api/auth/login/ for authentication.")

urlpatterns = [
    path('', home),  
    path("admin/", admin.site.urls),
    path('register/', RegisterView.as_view(), name='register'),
    # Authentication URLs
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/auth/social/", include("allauth.socialaccount.urls")),
    # JWT token endpoints
    path("api/token/", TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("api/token/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    # Application URLs with namespaces
    path("api/workflows/", include("workflows.urls", namespace="workflows")),
    path("api/users/", include("users.urls", namespace="users")),
    # You can add other app URLs with namespaces as needed
    path("api/analytics/", include("analytics.urls", namespace="analytics")),
    path("api/ai/", include("ai_integration.urls", namespace="ai_integration")),
]