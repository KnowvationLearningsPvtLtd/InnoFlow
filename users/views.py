from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.models import User
from .serializers import UserCreateSerializer, LoginSerializer

# Get the User model (works with custom user models too)
User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    View for user registration
    """
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "message": "User registered successfully",
            "user_id": user.id,
            "username": user.username
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    """
    View for user login
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response({"message": "Login successful"}, status=status.HTTP_200_OK)