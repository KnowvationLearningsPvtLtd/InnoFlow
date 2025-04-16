from django.urls import path, include
from .views import RegisterView, LoginView

urlpatterns = [
    path('auth/', include('users.auth_urls')),  # Linking the auth routes
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
]