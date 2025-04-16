from django.test import TestCase
from unittest.mock import patch, MagicMock
from ai_integration.tasks import run_ai_model_task
from ai_integration.models import AIModelConfig, ModelComparison, ModelResponse

class RunAIModelTaskTest(TestCase):
    def setUp(self):
        self.model_config = AIModelConfig.objects.create(
            name="Test Model",
            provider="OPENAI",
            model_name="gpt-3.5-turbo",
            is_active=True,
            api_key="test_key"
        )
        self.comparison = ModelComparison.objects.create(prompt="Test prompt")
    
    @patch('ai_integration.utils.openai_utils.openai_text_completion')
    def test_run_openai_task(self, mock_openai):
        mock_openai.return_value = "OpenAI response"
        
        # Call the task
        response = run_ai_model_task(self.model_config.id, "Test prompt", self.comparison.id)
        
        # Check that the utility function was called
        mock_openai.assert_called_once_with("Test prompt", self.model_config.model_name)
        
        # Check the response
        self.assertEqual(response, "OpenAI response")
        
        # Check that a ModelResponse was created
        model_response = ModelResponse.objects.get(comparison=self.comparison)
        self.assertEqual(model_response.response, "OpenAI response")
        self.assertIsNotNone(model_response.latency)
    
    @patch('ai_integration.utils.claude_utils.claude_text_completion')
    def test_run_claude_task(self, mock_claude):
        # Update model config to use Anthropic
        self.model_config.provider = "ANTHROPIC"
        self.model_config.save()
        
        mock_claude.return_value = "Claude response"
        
        # Call the task
        response = run_ai_model_task(self.model_config.id, "Test prompt", self.comparison.id)
        
        # Check that the utility function was called
        mock_claude.assert_called_once_with("Test prompt", self.model_config.model_name)
        
        # Check the response
        self.assertEqual(response, "Claude response")