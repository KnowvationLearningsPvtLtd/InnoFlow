from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from ai_integration.models import AIModelConfig, ModelComparison, ModelResponse, TaskStatus
from ai_integration.tasks import run_ai_model_task
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from time import sleep

User = get_user_model()

class AIIntegrationFullTests(APITestCase):
    def setUp(self):
        # Create a user & authenticate for API tests
        self.user = User.objects.create_user(username='aiuser', password='aiuserpass')
        self.client.force_authenticate(user=self.user)

        # Create a model config via API POST endpoint
        self.config_url = reverse('aimodelconfig-list')  # from router registration in ai_integration/urls.py
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
        # Get list of model configs
        response = self.client.get(self.config_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.json()) >= 1)

    @patch('ai_integration.utils.openai_provider.OpenAIProvider.generate_completion')
    def test_model_comparison_and_task_flow(self, mock_generate_completion):
        # Simulate provider generating a completion text
        mock_generate_completion.return_value = "Simulated completion result"

        # Create a model comparison via the ModelComparison endpoint
        comparison_url = reverse('modelcomparison-list')
        comparison_data = {
            "prompt": "Summarize this text: Lorem ipsum dolor sit amet.",
            "compared_models": [self.model_config_id]
        }
        comp_resp = self.client.post(comparison_url, comparison_data, format='json')
        self.assertEqual(comp_resp.status_code, status.HTTP_201_CREATED)
        comparison_id = comp_resp.data['id']

        # Since the view uses transaction.on_commit to trigger the task,
        # allow a short wait or force running of the task synchronously.
        # For test purposes we call run_ai_model_task directly.
        run_ai_model_task(self.model_config_id, comparison_data["prompt"], comparison_id)

        # Now check that a ModelResponse has been created for this comparison.
        responses = ModelResponse.objects.filter(comparison__id=comparison_id)
        self.assertTrue(responses.exists())
        self.assertEqual(responses.first().response, "Simulated completion result")

    @patch('ai_integration.utils.openai_provider.OpenAIProvider.generate_completion', return_value="Simulated completion result")
    def test_compare_models_action(self, mock_generate):
        # Test the custom compare-models action endpoint.
        compare_url = reverse('modelcomparison-compare-models')
        data = {
            "prompt": "Generate answer for life.",
            "models": [self.model_config_id]
        }
        compare_resp = self.client.post(compare_url, data, format='json')
        self.assertEqual(compare_resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("comparison_id", compare_resp.data)
        self.assertIn("results", compare_resp.data)
        # In this test our view calls the OpenAI provider so result may be None if error occurs.
        # Since we are not patching the provider here, we only check for structure.
        
    def test_task_status_view(self):
        # Create a task status record and test list endpoint.
        task_status_url = reverse('taskview-list')
        TaskStatus.objects.create(task_id="test_task_123", status="pending")
        resp = self.client.get(task_status_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertTrue(len(data) >= 1)

    def test_integration_workflow_ports(self):
        # This test ensures that node ports are created and validated.
        # Assume we have nodes (from workflows app) connected to ai_integration via provider.
        # For example, we update ports on a node and then validate them.
        # (This test simulates a full integration if workflows and ai_integration are wired together.)
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
