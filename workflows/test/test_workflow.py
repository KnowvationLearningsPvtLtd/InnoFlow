import json
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from workflows.models import Workflow, Node, WorkflowExecution, NodeConnection
from workflows.tasks import run_workflow
from celery import shared_task
from workflows.serializers import NodeSerializer, WorkflowExecutionSerializer, WorkflowSerializer
from rest_framework import serializers
from unittest.mock import patch
from django.core.exceptions import ValidationError
from workflows.utils import execute_node

User = get_user_model()

class WorkflowManagementSystemTests(APITestCase):
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def setUp(self, mock_analytics):
        self.mock_analytics = mock_analytics
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)  # Add authentication
        
        # Set up common test data
        self.workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        self.node = Node.objects.create(
            workflow=self.workflow,
            type='text_input',
            config={'text': 'Hello, World!'},
            order=1
        )
        
    # Workflow Model Tests
    def test_create_workflow(self):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        self.assertEqual(workflow.name, 'Test Workflow')
        self.assertEqual(workflow.user, self.user)
        
    def test_workflow_string_representation(self):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        self.assertEqual(str(workflow), 'Test Workflow')
        
    # Node Model Tests
    def test_create_node(self):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        node = Node.objects.create(
            workflow=workflow,
            type='text_input',
            config={'text': 'Hello, World!'},
            order=1
        )
        self.assertEqual(node.type, 'text_input')
        self.assertEqual(node.order, 1)
        
    def test_node_string_representation(self):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        node = Node.objects.create(
            workflow=workflow,
            type='text_input',
            config={'text': 'Hello, World!'},
            order=1
        )
        self.assertEqual(str(node), f'text_input (Workflow: Test Workflow)')
        
    # WorkflowExecution Model Tests
    def test_create_workflow_execution(self):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            status='pending'
        )
        self.assertEqual(execution.status, 'pending')
        
    def test_workflow_execution_string_representation(self):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            status='pending'
        )
        self.assertEqual(str(execution), f'Execution of Test Workflow (Pending)')
        
    # NodeConnection Model Tests
    def test_create_node_connection(self):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        node1 = Node.objects.create(
            workflow=workflow,
            type='text_input',
            config={'text': 'Hello, World!'},
            order=1
        )
        node2 = Node.objects.create(
            workflow=workflow,
            type='openai_tts',
            config={'voice': 'en'},
            order=2
        )
        connection = NodeConnection.objects.create(
            source_node=node1,
            target_node=node2,
            source_port='output',
            target_port='input'
        )
        self.assertEqual(connection.source_node, node1)
        self.assertEqual(connection.target_node, node2)
        
    # Workflow Serializer Tests
    def test_workflow_serializer(self):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        serializer = WorkflowSerializer(workflow)
        self.assertIn('id', serializer.data)
        self.assertIn('name', serializer.data)
        self.assertIn('nodes', serializer.data)
        
    # Node Serializer Tests
    def test_node_serializer(self):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        node = Node.objects.create(
            workflow=workflow,
            type='text_input',
            config={'text': 'Hello, World!'},
            order=1
        )
        serializer = NodeSerializer(node)
        self.assertIn('id', serializer.data)
        self.assertIn('type', serializer.data)
        self.assertIn('config', serializer.data)
        
    # WorkflowExecution Serializer Tests
    def test_workflow_execution_serializer(self):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            status='pending'
        )
        serializer = WorkflowExecutionSerializer(execution)
        self.assertIn('id', serializer.data)
        self.assertIn('status', serializer.data)
        self.assertIn('results', serializer.data)
        
    # Workflow View Tests
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_workflow_list_view(self, mock_analytics):
        url = reverse('workflow-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_workflow_detail_view(self, mock_analytics):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        url = reverse('workflow-detail', args=[workflow.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_create_workflow_view(self, mock_analytics):
        url = reverse('workflow-list')
        data = {
            'name': 'New Workflow',
            'user': self.user.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    # Node View Tests
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_node_list_view(self, mock_analytics):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        url = reverse('node-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_node_detail_view(self, mock_analytics):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        node = Node.objects.create(
            workflow=workflow,
            type='text_input',
            config={'text': 'Hello, World!'},
            order=1
        )
        url = reverse('node-detail', args=[node.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_create_node_view(self, mock_analytics):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        url = reverse('node-list')
        data = {
            'workflow': workflow.id,
            'type': 'text_input',
            'config': {'text': 'Hello, World!'},
            'order': 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    # WorkflowExecution View Tests
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_workflow_execution_list_view(self, mock_analytics):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        url = reverse('workflowexecution-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_workflow_execution_detail_view(self, mock_analytics):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            status='pending'
        )
        url = reverse('workflowexecution-detail', args=[execution.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    # Task Tests
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_run_workflow_task(self, mock_analytics):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            status='pending'
        )
        run_workflow.delay(workflow.id, execution.id)
        # Wait for task to complete (in a real test, you might need to mock Celery tasks)
        execution.refresh_from_db()
        self.assertIn(execution.status, ['completed', 'failed'])
        
    # Utils Tests
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_execute_node_util(self, mock_analytics):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        node = Node.objects.create(
            workflow=workflow,
            type='text_input',
            config={'text': 'Hello, World!'},
            order=1
        )
        result = execute_node(node, None)
        self.assertEqual(result, 'Hello, World!')
        
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_execute_tts_node_util(self, mock_analytics):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        node = Node.objects.create(
            workflow=workflow,
            type='openai_tts',
            config={
                'voice': 'en',
                'text': 'Hello, World!'  # Add required text parameter
            },
            order=1
        )
        input_data = {'result': 'Hello, World!'}
        result = execute_node(node, input_data)
        self.assertEqual(result, 'TTS audio generated successfully')
        
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_execute_summarization_node_util(self, mock_analytics):
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)
        node = Node.objects.create(
            workflow=workflow,
            type='huggingface_summarization',
            config={'model': 'facebook/bart-large-cnn'},  # Add required config
            order=1
        )
        input_data = 'This is a sample text to summarize.'
        result = execute_node(node, input_data)
        self.assertIsNotNone(result)
        
    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_workflow_validation(self, mock_analytics):
        """Test workflow validation rules"""
        workflow = Workflow.objects.create(name='Validation Test', user=self.user)
        
        # Create first node with proper config
        Node.objects.create(
            workflow=workflow, 
            type='text_input', 
            config={'text': 'Test'}, 
            order=1
        )
        
        # Attempt to create duplicate order
        with self.assertRaises(ValidationError):
            Node.objects.create(
                workflow=workflow, 
                type='text_input', 
                config={'text': 'Test'}, 
                order=1
            )

    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_workflow_execution_context(self, mock_analytics):
        """Test workflow execution context handling"""
        workflow = Workflow.objects.create(name='Context Test', user=self.user)
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            execution_context={'test_key': 'test_value'}
        )
        self.assertEqual(execution.execution_context['test_key'], 'test_value')

    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_node_type_validation(self, mock_analytics):
        """Test node type validation"""
        workflow = Workflow.objects.create(name='Type Test', user=self.user)
        with self.assertRaises(ValidationError):
            Node.objects.create(
                workflow=workflow,
                type='invalid_type',
                config={'text': 'Test'},  # Add required config
                order=1
            )

    @patch('analytics.middleware.WorkflowAnalytics.objects.create')
    def test_workflow_permission_boundaries(self, mock_analytics):
        """Test workflow permission boundaries"""
        other_user = User.objects.create_user(username='other', password='pass')
        other_workflow = Workflow.objects.create(name='Other Workflow', user=other_user)
        
        # Try to add node to other user's workflow
        url = reverse('node-list')
        data = {
            'workflow': other_workflow.id,
            'type': 'text_input',
            'order': 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)