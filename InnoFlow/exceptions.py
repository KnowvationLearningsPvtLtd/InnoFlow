# Create a new file: InnoFlow/exceptions.py
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # Handle JWT specific errors
    if isinstance(exc, (InvalidToken, TokenError)):
        return Response(
            {"detail": "Authentication failed. Please log in again."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    return response