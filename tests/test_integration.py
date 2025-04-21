from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from workflows.models import Workflow, Node, WorkflowExecution
from ai_integration.models import AIModelConfig, ModelResponse
from analytics.models import UserActivityLog, WorkflowAnalytics
from django.utils import timezone
import time

User = get_user_model()

class InnoFlowIntegrationTests(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test workflow
        self.workflow = Workflow.objects.create(
            name='Test Integration Workflow',
            user=self.user
        )

    def test_user_authentication(self):
        """Test user login and authentication"""
        # Logout first
        self.client.force_authenticate(user=None)
        
        # Test login
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_workflow_creation_and_execution(self):
        """Test creating and executing a workflow"""
        # Create a new workflow
        workflow_data = {
            'name': 'Test Workflow',
            'description': 'Test workflow description',
            'user': self.user.id  # Add user field
        }
        response = self.client.post(reverse('workflow-list'), workflow_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        workflow_id = response.data['id']

        # Add nodes to workflow
        node_data = {
            'workflow': workflow_id,
            'type': 'text_input',
            'config': {'text': 'Hello, World!'},
            'order': 1
        }
        response = self.client.post(reverse('node-list'), node_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Execute workflow
        response = self.client.post(
            reverse('workflow-execute', args=[workflow_id]), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('ai_integration.providers_registry.ProviderRegistry.get_provider')
    def test_ai_model_integration(self, mock_get_provider):
        """Test AI model integration"""
        # Mock AI provider
        mock_provider = MagicMock()
        mock_provider.generate_completion.return_value = "AI generated response"
        mock_get_provider.return_value = mock_provider

        # Create AI model config
        model_config = AIModelConfig.objects.create(
            name="Test Model",
            provider="OPENAI",
            model_name="gpt-3.5-turbo",
            api_key="test_key"
        )

        # Create node with AI model
        node = Node.objects.create(
            workflow=self.workflow,
            type='ai_completion',
            config={'model_config_id': model_config.id},
            order=1
        )

        # Execute workflow with AI node
        execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            status='pending'
        )
        response = self.client.post(
            reverse('workflow-execute', args=[self.workflow.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_analytics_tracking(self):
        """Test analytics event tracking"""
        # Execute workflow to generate analytics
        response = self.client.post(
            reverse('workflow-execute', args=[self.workflow.id]), format='json'
        )

        # Check if analytics event was recorded using WorkflowAnalytics
        events = WorkflowAnalytics.objects.filter(
            workflow=self.workflow
        )
        self.assertTrue(events.exists())

        # Check if user activity was logged
        activities = UserActivityLog.objects.filter(
            user=self.user,
            activity_type='workflow_execution'
        )
        self.assertTrue(activities.exists())

    def test_error_handling(self):
        """Test error handling in workflow execution"""
        # Create node with missing configuration
        Node.objects.create(
            workflow=self.workflow,
            type='ai_completion',
            config={},  # Missing model_config_id
            order=1
        )

        # Execute workflow with invalid node
        response = self.client.post(
            reverse('workflow-execute', args=[self.workflow.id]), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Initial response is OK
        
        # Poll for the task to complete
        execution = WorkflowExecution.objects.get(workflow=self.workflow)
        for _ in range(10):
            execution.refresh_from_db()
            if execution.status != 'pending':
                break
            time.sleep(1)

        # Check execution status
        execution.refresh_from_db()
        self.assertEqual(execution.status, 'failed')
        self.assertIsNotNone(execution.error_message)

    def test_workflow_results_caching(self):
        """Test workflow results caching"""
        # Create valid node first
        Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            config={'text': 'Hello, World!'},
            order=1
        )
        
        response1 = self.client.post(
            reverse('workflow-execute', args=[self.workflow.id]), format='json'
        )
        response2 = self.client.post(
            reverse('workflow-execute', args=[self.workflow.id]), format='json'
        )
        
        # Get response data safely
        response1_data = response1.json() if hasattr(response1, 'json') else response1.data
        response2_data = response2.json() if hasattr(response2, 'json') else response2.data
        
        # Check if 'execution_id' exists before accessing it
        if 'execution_id' in response1_data and 'execution_id' in response2_data:
            exec1 = WorkflowExecution.objects.get(id=response1_data['execution_id'])
            exec2 = WorkflowExecution.objects.get(id=response2_data['execution_id'])
            self.assertEqual(exec1.results, exec2.results)
        else:
            self.fail("execution_id not found in response")
