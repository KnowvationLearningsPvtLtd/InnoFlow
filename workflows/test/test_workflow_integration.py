from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from workflows.models import Workflow, Node, WorkflowExecution, NodeConnection
from workflows.execution import WorkflowExecutor
from workflows.utils import execute_node
from unittest.mock import patch, MagicMock
import json

User = get_user_model()

class WorkflowIntegrationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.workflow = Workflow.objects.create(
            name='Test Complex Workflow',
            user=self.user
        )
        
        self.input_node = Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            config={'text': 'Test input'},
            order=1
        )
        
        self.summarize_node = Node.objects.create(
            workflow=self.workflow,
            type='huggingface_summarization',
            config={'model': 'facebook/bart-large-cnn'},
            order=2
        )
        
        self.tts_node = Node.objects.create(
            workflow=self.workflow,
            type='openai_tts',
            config={'voice': 'en', 'text': 'Test'},
            order=3
        )

    @patch('workflows.execution.execute_node_util')
    def test_complete_workflow_execution(self, mock_execute):
        # Setup mock responses that match the expected data flow
        mock_execute.side_effect = [
            "Test input",  # input node
            "Summarized content",  # summarization node
            "TTS audio generated successfully"  # tts node
        ]

        NodeConnection.objects.create(
            source_node=self.input_node,
            target_node=self.summarize_node,
            source_port='output',
            target_port='input'
        )
        
        NodeConnection.objects.create(
            source_node=self.summarize_node,
            target_node=self.tts_node,
            source_port='output',
            target_port='input'
        )
        
        execution = WorkflowExecution.objects.create(workflow=self.workflow)
        executor = WorkflowExecutor(execution)
        executor.execute_workflow()
        
        self.assertEqual(execution.status, 'completed')
        self.assertEqual(mock_execute.call_count, 3)

    @patch('workflows.execution.execute_node_util')
    def test_workflow_error_handling(self, mock_execute):
        def mock_execute_with_error(*args, **kwargs):
            node = args[0]
            if node.type == 'text_input':
                return "Test input"
            raise ValueError("Simulated error")

        mock_execute.side_effect = mock_execute_with_error
        
        error_node = Node.objects.create(
            workflow=self.workflow,
            type='huggingface_summarization',
            config={'model': 'test-model'},
            order=4
        )
        
        execution = WorkflowExecution.objects.create(workflow=self.workflow)
        executor = WorkflowExecutor(execution)
        
        with self.assertRaises(ValueError):
            executor.execute_workflow()
        
        self.assertEqual(execution.status, 'failed')
        self.assertIsNotNone(execution.error_logs)

    @patch('workflows.execution.execute_node_util')
    def test_workflow_with_variables(self, mock_execute):
        test_var_value = "Variable substituted result"
        mock_execute.return_value = test_var_value
        
        workflow_with_vars = Workflow.objects.create(
            name='Variable Workflow',
            user=self.user
        )
        
        var_node = Node.objects.create(
            workflow=workflow_with_vars,
            type='text_input',
            config={'text': '${test_var}'},
            order=1
        )
        
        execution = WorkflowExecution.objects.create(
            workflow=workflow_with_vars,
            variables={'test_var': 'replaced_value'}
        )
        executor = WorkflowExecutor(execution)
        executor.execute_workflow()
        
        self.assertEqual(execution.status, 'completed')
        self.assertEqual(execution.results[var_node.id], test_var_value)

    @patch('workflows.execution.execute_node_util')
    def test_workflow_retry_mechanism(self, mock_execute):
        retry_attempts = []
        def mock_execute_with_retries(node, input_data, **kwargs):
            # For nodes not meant to retry (orders other than 4), return success immediately.
            if node.order != 4:
                return f"Node {node.order} success"
            retry_attempts.append(1)
            if len(retry_attempts) <= 2:
                raise ValueError(f"Failure attempt {len(retry_attempts)}")
            return "Success after retries"
        mock_execute.side_effect = mock_execute_with_retries
        
        retry_node = Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            config={'text': 'Retry test'},
            order=4,
            max_retries=3
        )
        
        execution = WorkflowExecution.objects.create(workflow=self.workflow)
        executor = WorkflowExecutor(execution)
        executor.execute_workflow()
        
        # Only the retry node will experience retries; hence we expect 3 attempts.
        self.assertEqual(len(retry_attempts), 3)
        self.assertEqual(execution.status, 'completed')
        self.assertEqual(execution.results[retry_node.id], "Success after retries")
