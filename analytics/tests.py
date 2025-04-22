from django.test import TestCase, RequestFactory
from rest_framework.test import APITestCase, APIClient
from django.utils import timezone
from datetime import timedelta
from analytics.models import WorkflowAnalytics, PerformanceMetrics, WorkflowUsageStats, UserActivityLog
from analytics.services import AnalyticsService
from analytics.middleware import AnalyticsMiddleware
from workflows.models import Workflow
from users.models import UserProfile
import json
from rest_framework_simplejwt.tokens import RefreshToken

class AnalyticsAPITest(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(username="testuser", email="test@example.com")
        self.user.set_password('testpass')  # Set a password for the user
        self.user.save()  # Save the user to the database
        self.workflow = Workflow.objects.create(name="Test Workflow", user=self.user)
        
        # Obtain token for the user
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        now = timezone.now()
        # Create dummy analytics records with timezone-aware datetimes
        WorkflowAnalytics.objects.create(
            workflow=self.workflow,
            execution_time=1.5,
            success_rate=1.0,
            error_count=0,
            executed_at=now - timedelta(days=1)
        )
        PerformanceMetrics.objects.create(
            workflow=self.workflow,
            average_response_time=0.5,
            throughput=100,
            memory_usage=50.0,
            cpu_usage=30.0,
            measured_at=now - timedelta(hours=1)
        )
        WorkflowUsageStats.objects.create(
            workflow=self.workflow,
            total_executions=10,
            unique_users=2,
            last_executed=now,
        )
        UserActivityLog.objects.create(
            user=self.user,
            activity_type='login',
            details={'ip': '127.0.0.1'},
            created_at=now - timedelta(minutes=30)
        )
        self.client = APIClient()
        
        # Define base URL
        self.base_url = '/api/analytics/'

    def test_workflow_performance(self):
        url = f"{self.base_url}workflow_performance/"
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_system_performance(self):
        url = f"{self.base_url}system_performance/"
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_usage_statistics(self):
        url = f"{self.base_url}usage_statistics/"
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_workflow_execution_stats(self):
        url = f"{self.base_url}workflow_execution_stats/?start_date=2000-01-01&end_date=2100-01-01"
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_node_performance_stats(self):
        url = f"{self.base_url}node_performance_stats/?workflow_id={self.workflow.id}"
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_user_activity_report(self):
        url = f"{self.base_url}user_activity_report/?activity_type=login&user_id={self.user.id}"
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_system_performance_report(self):
        today = timezone.now().date().isoformat()
        url = f"{self.base_url}system_performance_report/?day={today}&hour=12"
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)

    def test_workflow_performance_chart(self):
        url = f"{self.base_url}workflow_performance_chart/?workflow_id={self.workflow.id}&days=7"
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('image_base64', response.data)

    def test_monthly_report(self):
        now = timezone.now()
        url = f"{self.base_url}monthly_report/?year={now.year}&month={now.month}"
        response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('workflow_stats', response.data)
        self.assertIn('user_stats', response.data)
        self.assertIn('system_stats', response.data)

    def test_integration_all_endpoints(self):
        endpoints = {
            f"workflow_performance/": {},
            f"system_performance/": {},
            f"usage_statistics/": {},
            f"workflow_execution_stats/": {"start_date": "2000-01-01", "end_date": "2100-01-01"},
            f"node_performance_stats/": {"workflow_id": self.workflow.id},
            f"user_activity_report/": {"activity_type": "login", "user_id": self.user.id},
            f"system_performance_report/": {"day": timezone.now().date().isoformat(), "hour": 12},
            f"workflow_performance_chart/": {"workflow_id": self.workflow.id, "days": 7},
            f"monthly_report/": {"year": timezone.now().year, "month": timezone.now().month},
        }
        
        for endpoint, params in endpoints.items():
            url = f"{self.base_url}{endpoint}"
            if params:
                query_string = "&".join([f"{k}={v}" for k, v in params.items()])
                url += f"?{query_string}"
            response = self.client.get(url, HTTP_AUTHORIZATION=f'Bearer {self.token}')
            self.assertEqual(response.status_code, 200)

class AnalyticsServiceTest(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create(username="serviceuser", email="service@example.com")
        self.workflow = Workflow.objects.create(user=self.user)  # updated: pass user
        now = timezone.now()
        self.analytics = WorkflowAnalytics.objects.create(
            workflow=self.workflow,
            execution_time=2.0,
            success_rate=0.8,
            error_count=1,
            executed_at=now - timedelta(days=2)
        )
        self.activity = UserActivityLog.objects.create(
            user=self.user,
            activity_type='test',
            details={'test': True},
            created_at=now - timedelta(minutes=20)
        )
        self.metric = PerformanceMetrics.objects.create(
            workflow=self.workflow,
            average_response_time=0.7,
            throughput=80,
            memory_usage=40.0,
            cpu_usage=25.0,
            measured_at=now - timedelta(minutes=45)
        )

    def test_workflow_execution_stats_service(self):
        stats = AnalyticsService.workflow_execution_stats(
            start_date="2000-01-01", end_date="2100-01-01", workflow_id=self.workflow.id
        )
        self.assertTrue(len(list(stats)) >= 1)

    def test_user_activity_report_service(self):
        stats = AnalyticsService.user_activity_report(
            activity_type='test', user_id=self.user.id,
            day=str(self.activity.created_at.date()),
            hour=self.activity.created_at.hour
        )
        self.assertTrue(len(list(stats)) >= 1)

    def test_system_performance_report_service(self):
        stats = AnalyticsService.system_performance_report(day=str(self.metric.measured_at.date()))
        self.assertTrue(len(list(stats)) >= 1)

class AnalyticsMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserProfile.objects.create(username="middlewareuser", email="middleware@example.com")
        self.workflow = Workflow.objects.create(name="Middleware Test Workflow", user=self.user)
    
    def test_analytics_middleware_creates_record(self):
        from django.http import JsonResponse
        def dummy_get_response(request):
            response = JsonResponse({'status': 'ok'})
            response.status_code = 200
            response.elapsed = 1.2  # simulate elapsed time
            return response
        
        middleware = AnalyticsMiddleware(dummy_get_response)
        request = self.factory.post('/api/workflows/', data=json.dumps({'workflow_id': self.workflow.id}), content_type='application/json')
        initial_count = WorkflowAnalytics.objects.count()
        middleware(request)
        new_count = WorkflowAnalytics.objects.count()
        self.assertEqual(new_count, initial_count + 1)
