from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer,
    UserRegisterSerializer,
    UserUpdateSerializer,
    CustomTokenObtainPairSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .authentication import CustomJWTAuthentication
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.renderers import JSONRenderer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=user.id)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    renderer_classes = [JSONRenderer]

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            return Response(
                {"detail": "Method not allowed"}, 
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        return super().dispatch(request, *args, **kwargs)

class GitHubLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    renderer_classes = [JSONRenderer]

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET":
            return Response(
                {"detail": "Method not allowed"}, 
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        return super().dispatch(request, *args, **kwargs)