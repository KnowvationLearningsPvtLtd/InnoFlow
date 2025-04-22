from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TestCase
from ai_integration.models import AIModelConfig, ModelComparison, ModelResponse, TaskStatus
from ai_integration.tasks import run_ai_model_task
from unittest.mock import patch, MagicMock
from time import sleep

User = get_user_model()

# ============================
# Unit Tests for Providers, Serializers, and Models
# ============================

class TestProviders(TestCase):
    def test_claude_provider_generate_completion(self):
        from ai_integration.utils.claude_provider import ClaudeProvider
        api_key = "dummy_key"
        provider = ClaudeProvider(api_key)
        prompt = "Hello, how are you?"
        with patch('anthropic.Client') as mock_client:
            mock_response = MagicMock()
            mock_response.completion = 'I am fine, thank you!'
            mock_client.return_value.completions.create.return_value = mock_response
            response = provider.generate_completion(prompt)
            self.assertEqual(response, 'I am fine, thank you!')

    def test_deepseek_provider_generate_completion(self):
        from ai_integration.utils.deepseek_provider import DeepSeekProvider
        api_key = "dummy_key"
        model_name = "dummy_model"
        provider = DeepSeekProvider(api_key, model_name)
        prompt = "Hello, how are you?"
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"choices": [{"message": {"content": "I am fine, thank you!"}}]}
            mock_post.return_value = mock_response
            response = provider.generate_completion(prompt)
            self.assertEqual(response, 'I am fine, thank you!')

    def test_huggingface_provider_generate_completion(self):
        from ai_integration.utils.huggingface_provider import HuggingFaceProvider
        model_name = "gpt2"
        provider = HuggingFaceProvider(model_name)
        prompt = "Hello, how are you?"
        with patch('ai_integration.utils.huggingface_provider.pipeline') as mock_pipeline:
            mock_callable = MagicMock(return_value=[{"generated_text": "I am fine, thank you!"}])
            mock_pipeline.return_value = mock_callable
            response = provider.generate_completion(prompt)
            self.assertEqual(response, 'I am fine, thank you!')

    def test_ollama_provider_generate_completion(self):
        from ai_integration.utils.ollama_provider import OllamaProvider
        base_url = "http://dummy_url"
        model_name = "dummy_model"
        provider = OllamaProvider(base_url, model_name)
        prompt = "Hello, how are you?"
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "I am fine, thank you!"}
            mock_post.return_value = mock_response
            response = provider.generate_completion(prompt)
            self.assertEqual(response, 'I am fine, thank you!')

    def test_openai_provider_generate_completion(self):
        from ai_integration.utils.openai_provider import OpenAIProvider
        api_key = "dummy_key"
        model_name = "gpt-3.5-turbo"
        provider = OpenAIProvider(api_key, model_name)
        prompt = "Hello, how are you?"
        # Patch the OpenAI class used in openai_provider.py, not openai.ChatCompletion.create.
        with patch('ai_integration.utils.openai_provider.OpenAI') as mock_openai:
            instance = mock_openai.return_value
            instance.responses.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content='I am fine, thank you!'))]
            )
            response = provider.generate_completion(prompt)
            self.assertIsInstance(response, str)
            self.assertTrue(response.strip() != "", "Returned string should not be empty")

class TestSerializers(APITestCase):
    def test_ai_model_config_serializer(self):
        from ai_integration.serializers import AIModelConfigSerializer
        model_config = AIModelConfig.objects.create(
            name="Test Model",
            provider="OPENAI",
            model_name="gpt-3.5-turbo",
            api_key="dummy_key"
        )
        serializer = AIModelConfigSerializer(model_config)
        self.assertIn("name", serializer.data)
        
    def test_model_response_serializer(self):
        from ai_integration.serializers import ModelResponseSerializer
        model_config = AIModelConfig.objects.create(
            name="Test Model",
            provider="OPENAI",
            model_name="gpt-3.5-turbo",
            api_key="dummy_key"
        )
        comparison = ModelComparison.objects.create(prompt="Test prompt")
        response_obj = ModelResponse.objects.create(
            comparison=comparison,
            model_config=model_config,
            response="Test response",
            latency=0.5
        )
        serializer = ModelResponseSerializer(response_obj)
        self.assertIn("response", serializer.data)
        
class TestModels(TestCase):
    def test_create_ai_model_config(self):
        model_config = AIModelConfig.objects.create(
            name="Test Model",
            provider="OPENAI",
            model_name="gpt-3.5-turbo",
            api_key="dummy_key"
        )
        self.assertEqual(model_config.name, "Test Model")
        
    def test_create_model_comparison(self):
        model_config = AIModelConfig.objects.create(
            name="Test Model",
            provider="OPENAI",
            model_name="gpt-3.5-turbo",
            api_key="dummy_key"
        )
        comparison = ModelComparison.objects.create(prompt="Test prompt")
        comparison.compared_models.add(model_config)
        self.assertEqual(comparison.prompt, "Test prompt")
        
    def test_create_model_response(self):
        model_config = AIModelConfig.objects.create(
            name="Test Model",
            provider="OPENAI",
            model_name="gpt-3.5-turbo",
            api_key="dummy_key"
        )
        comparison = ModelComparison.objects.create(prompt="Test prompt")
        response_obj = ModelResponse.objects.create(
            comparison=comparison,
            model_config=model_config,
            response="Test response",
            latency=0.5
        )
        self.assertEqual(response_obj.response, "Test response")
        
    def test_create_task_status(self):
        task_status = TaskStatus.objects.create(
            task_id="test_task_id",
            status="pending"
        )
        self.assertEqual(task_status.task_id, "test_task_id")

# ============================
# Integration Tests for API and Task Flows
# ============================

class AIIntegrationFullTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='aiuser', password='aiuserpass')
        self.client.force_authenticate(user=self.user)
        self.config_url = reverse('aimodelconfig-list')
        self.model_config_data = {
            'name': 'Test Model',
            'provider': 'OPENAI',
            'model_name': 'gpt-3.5-turbo',
            'api_key': 'dummy_key',
            'parameters': {}
        }
        config_resp = self.client.post(self.config_url, self.model_config_data, format='json')
        self.assertEqual(config_resp.status_code, status.HTTP_201_CREATED)
        self.model_config_id = config_resp.data['id']
        
    def test_model_config_listing(self):
        response = self.client.get(self.config_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.json()) >= 1)
    
    @patch('ai_integration.utils.openai_provider.OpenAIProvider.generate_completion')
    def test_model_comparison_and_task_flow(self, mock_generate_completion):
        mock_generate_completion.return_value = "Simulated completion result"
        comparison_url = reverse('modelcomparison-list')
        comparison_data = {
            "prompt": "Summarize this text: Lorem ipsum dolor sit amet.",
            "compared_models": [self.model_config_id]
        }
        comp_resp = self.client.post(comparison_url, comparison_data, format='json')
        self.assertEqual(comp_resp.status_code, status.HTTP_201_CREATED)
        comparison_id = comp_resp.data['id']
        run_ai_model_task(self.model_config_id, comparison_data["prompt"], comparison_id)
        responses = ModelResponse.objects.filter(comparison__id=comparison_id)
        self.assertTrue(responses.exists())
        self.assertEqual(responses.first().response, "Simulated completion result")
    
    @patch('ai_integration.utils.openai_provider.OpenAIProvider.generate_completion', return_value="Simulated completion result")
    def test_compare_models_action(self, mock_generate_completion):
        compare_url = reverse('modelcomparison-compare-models')
        data = {
            "prompt": "Generate answer for life.",
            "models": [self.model_config_id]
        }
        compare_resp = self.client.post(compare_url, data, format='json')
        self.assertEqual(compare_resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("comparison_id", compare_resp.data)
        self.assertIn("results", compare_resp.data)
    
    def test_task_status_view(self):
        task_status_url = reverse('taskview-list')
        TaskStatus.objects.create(task_id="test_task_123", status="pending")
        resp = self.client.get(task_status_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.json()) >= 1)
        
    def test_integration_workflow_ports(self):
        from ai_integration.node_port_inntegration import update_workflow_ports, validate_node_ports
        from workflows.models import Workflow, Node
        workflow = Workflow.objects.create(name="Port Test Workflow", user=self.user)
        node = Node.objects.create(
            workflow=workflow,
            type='text_input',
            config={'text': 'Port test'},
            order=1
        )
        port_update_result = update_workflow_ports(workflow.id)
        self.assertIn('workflow_id', port_update_result)
        errors = validate_node_ports(node)
        self.assertEqual(len(errors), 0)


