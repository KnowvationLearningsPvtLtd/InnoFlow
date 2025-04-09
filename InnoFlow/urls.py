"""
URL configuration for InnoFlow project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# OAuth views
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

class GithubLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # JWT auth
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # App APIs
    path('api/users/', include('users.urls')),
    path('api/workflows/', include('workflows.urls')),

    # REST auth
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

    # Social auth endpoints
    path('api/auth/social/google/', GoogleLogin.as_view(), name='google_login'),
    path('api/auth/social/github/', GithubLogin.as_view(), name='github_login'),

    # Optional: include the default socialaccount routes (e.g. for admin testing)
    path('api/auth/social/allauth/', include('allauth.socialaccount.urls')),
]
