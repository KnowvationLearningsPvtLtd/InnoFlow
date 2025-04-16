from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from ai_integration.models import AIModelConfig, ModelComparison

class AIModelConfigViewSetTest(APITestCase):
    def setUp(self):
        self.url = reverse('aimodelconfig-list')
        self.model_data = {
            'name': 'Test Model',
            'model_type': 'gpt-3.5-turbo',
            'api_key': 'test-key',
            'parameters': {'temperature': 0.7, 'max_tokens': 100}
        }
        
    def test_create_model(self):
        response = self.client.post(self.url, self.model_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AIModelConfig.objects.count(), 1)
        
    def test_list_models(self):
        AIModelConfig.objects.create(**self.model_data)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class ModelComparisonViewSetTest(APITestCase):
    def setUp(self):
        # Create test models
        self.model1 = AIModelConfig.objects.create(
            name='Model 1',
            model_type='gpt-3.5-turbo',
            api_key='test-key-1',
            parameters={'temperature': 0.7}
        )
        
        self.model2 = AIModelConfig.objects.create(
            name='Model 2',
            model_type='gpt-4',
            api_key='test-key-2',
            parameters={'temperature': 0.5}
        )
        
        # Set up URLs
        self.comparison_url = reverse('modelcomparison-list')
        
        # Create comparison data
        self.comparison_data = {
            'prompt': 'Test prompt',
            'models': [self.model1.id, self.model2.id]
        }
        
        # Create a comparison for testing results
        self.comparison = ModelComparison.objects.create(
            prompt='Test results prompt',
            results={'model1': 'Result 1', 'model2': 'Result 2'}
        )
        self.comparison.models.add(self.model1, self.model2)
        
        # Set up results URL
        self.results_url = reverse('modelcomparison-results', args=[self.comparison.id])
    
    @patch('ai_integration.views.generate_completion')
    def test_compare_models(self, mock_generate):
        # Mock the generate_completion function
        mock_generate.return_value = "Mocked response"
        
        response = self.client.post(self.comparison_url, self.comparison_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ModelComparison.objects.count(), 2)  # 1 from setUp + 1 new
        
    def test_get_results(self):
        response = self.client.get(self.results_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)