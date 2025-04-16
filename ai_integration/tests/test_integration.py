# ai_integration/tests/test_integration.py
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from unittest.mock import patch
from ai_integration.models import AIModelConfig

class IntegrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Make sure these URLs match your URL configuration
        self.model_url = reverse('aimodelconfig-list')
        self.compare_url = '/api/ai/compare-models/'
        
    @patch('ai_integration.tasks.run_ai_model_task')
    def test_full_workflow(self, mock_run_task):
        # Mock the task return value
        mock_run_task.return_value = "Mocked AI response"
        
        # Create a model
        model_data = {
            'name': 'Test GPT Model',
            'provider': 'openai',
            'model_id': 'gpt-3.5-turbo',
            'api_key': 'test-key'
        }
        
        # Use the correct URL for creating a model
        response = self.client.post(self.model_url, model_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Rest of your test...