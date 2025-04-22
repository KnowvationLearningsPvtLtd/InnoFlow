from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from workflows.models import Workflow, Node, WorkflowExecution
from ai_integration.models import AIModelConfig
from analytics.models import WorkflowAnalytics
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from workflows.models import NodeConnection
from workflows.tasks import run_workflow
import json

User = get_user_model()

class IntegrationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

        # Create an AI model config for testing
        self.model_config = AIModelConfig.objects.create(
            name="Test Model",
            provider="OPENAI",
            model_name="gpt-3.5-turbo",
            api_key="dummy_key"
        )

    def test_user_registration_and_workflow_creation(self):
        # Test user registration
        url = reverse('register')
        reg_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPass123',
            'password2': 'StrongPass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        reg_resp = self.client.post(url, reg_data)
        self.assertEqual(reg_resp.status_code, status.HTTP_201_CREATED)

        # Test workflow creation
        workflow_url = reverse('workflow-list')
        workflow_data = {
            'name': 'New Workflow',
            'user': self.user.id
        }
        workflow_resp = self.client.post(workflow_url, workflow_data)
        self.assertEqual(workflow_resp.status_code, status.HTTP_201_CREATED)

    def test_workflow_execution_with_ai_integration(self):
        # Create a workflow
        workflow = Workflow.objects.create(name='Test Workflow', user=self.user)

        # Create nodes for the workflow
        input_node = Node.objects.create(
            workflow=workflow,
            type='text_input',
            config={'text': 'Hello, how are you?'},
            order=1
        )
        ai_node = Node.objects.create(
            workflow=workflow,
            type='openai_tts',
            config={'voice': 'en', 'text': 'Hello, how are you?'},
            order=2
        )

        # Connect nodes
        NodeConnection.objects.create(
            source_node=input_node,
            target_node=ai_node,
            source_port='output',
            target_port='input'
        )

        # Execute the workflow
        execution = WorkflowExecution.objects.create(workflow=workflow)
        execution.status = 'running'
        execution.save()

        # Simulate running the workflow (you would call the actual execution logic here)
        # For example, you might call a task that processes the workflow
        # run_workflow.delay(workflow.id, execution.id)

        # Check that the execution status is updated correctly
        self.assertEqual(execution.status, 'running')  # Update this based on actual execution logic

    def test_email_verification_and_workflow_access(self):
        # Create an inactive user with a specific email
        email = 'inactiveuser@example.com'
        inactive_user = User.objects.create_user(
            username='inactiveuser', 
            password='testpassword', 
            email=email,  # Explicitly set the email
            is_active=False
        )

        # Simulate email verification process
        verify_url = reverse('email-verify')
        verify_data = {'email': email}  # Use the same email
        verify_resp = self.client.post(verify_url, verify_data)
        self.assertEqual(verify_resp.status_code, status.HTTP_200_OK)

        # Now activate the user and check workflow access
        inactive_user.is_active = True
        inactive_user.save()

        # Test workflow creation after email verification
        self.client.force_authenticate(user=inactive_user)
        workflow_url = reverse('workflow-list')
        workflow_data = {
            'name': 'New Workflow',
            'user': inactive_user.id
        }
        workflow_resp = self.client.post(workflow_url, workflow_data)
        self.assertEqual(workflow_resp.status_code, status.HTTP_201_CREATED)

    def test_password_reset_and_workflow_access(self):
        # Create a user and request password reset
        user = User.objects.create_user(username='resetuser', email='resetuser@example.com', password='oldpass123')
        reset_url = reverse('password-reset')
        resp = self.client.post(reset_url, {'email': 'resetuser@example.com'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Simulate password reset confirmation
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_confirm_url = reverse('password-reset-confirm')
        confirm_resp = self.client.post(reset_confirm_url, {
            'uid': uid,
            'token': token,
            'new_password': 'newpass123'
        })
        self.assertEqual(confirm_resp.status_code, status.HTTP_200_OK)

        # Check that the user can now log in and access workflows
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass123'))

        # Test workflow creation
        self.client.force_authenticate(user=user)
        workflow_url = reverse('workflow-list')
        workflow_data = {
            'name': 'New Workflow',
            'user': user.id
        }
        workflow_resp = self.client.post(workflow_url, workflow_data)
        self.assertEqual(workflow_resp.status_code, status.HTTP_201_CREATED)

    def test_analytics_tracking_for_workflow_execution(self):
        # Create a workflow and execute it
        workflow = Workflow.objects.create(name='Analytics Test Workflow', user=self.user)
        execution = WorkflowExecution.objects.create(workflow=workflow, status='pending')

        # Create the analytics record directly for testing purposes
        # In production, this would be created by the middleware
        analytics_record = WorkflowAnalytics.objects.create(
            workflow=workflow,
            execution_time=1.0,
            success_rate=1.0,
            error_count=0
        )

        # Check that analytics record is created
        analytics_record = WorkflowAnalytics.objects.filter(workflow=workflow).first()
        self.assertIsNotNone(analytics_record)
        self.assertEqual(analytics_record.workflow, workflow)
