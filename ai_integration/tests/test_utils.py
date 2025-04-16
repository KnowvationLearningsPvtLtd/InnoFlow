# ai_integration/tests/test_utils.py
from django.test import TestCase
from unittest.mock import patch, MagicMock
from ai_integration.utils.openai_utils import generate_completion

class OpenAIUtilsTest(TestCase):
    @patch('ai_integration.utils.openai_utils.openai.chat.completions.create')
    def test_openai_text_completion_success(self, mock_create):
        # Create a proper mock response structure
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_create.return_value = mock_response
        
        # Call the function
        result = generate_completion("Test prompt")
        
        # Verify
        self.assertEqual(result, "Test response")