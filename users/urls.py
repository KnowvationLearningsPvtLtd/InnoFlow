from django.urls import path, include


urlpatterns = [
    path('auth/', include('users.auth_urls')),  # Linking the auth routes
]

from django.urls import path
from .views import RegisterView, LoginView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
]
