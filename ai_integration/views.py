from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

class TestModelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ...
