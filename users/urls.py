from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, RegisterView, CustomTokenView
)

router = DefaultRouter()
router.register(r'profiles', UserViewSet, basename='userprofile')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
    path('token/', CustomTokenView.as_view(), name='token_obtain_pair'),
]