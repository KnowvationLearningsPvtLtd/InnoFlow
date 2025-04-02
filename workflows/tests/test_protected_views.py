# workflows/tests/test_protected_views.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from workflows.models import Workflow

User = get_user_model()

class ProtectedEndpointsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='securepassword123'
        )
        
        # Login and get token
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'securepassword123'
        }, format='json')
        
        self.token = response.data['access']
        
        # Create a test workflow
        self.workflow = Workflow.objects.create(
            name="Test Workflow",
            user=self.user
        )
        
    def test_authenticated_access(self):
        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Access protected endpoint
        response = self.client.get('/api/workflows/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_unauthenticated_access(self):
        # Clear authentication
        self.client.credentials()
        
        # Try to access protected endpoint
        response = self.client.get('/api/workflows/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)