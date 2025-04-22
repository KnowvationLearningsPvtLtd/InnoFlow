import base64
import io
from datetime import datetime, timedelta
from django.db.models import Count, Avg, Sum, Q, F, Max
from django.utils import timezone
import matplotlib.pyplot as plt
from .models import WorkflowAnalytics, UserActivityLog, PerformanceMetrics, WorkflowUsageStats
from workflows.models import Workflow, Node
from users.models import UserProfile

class AnalyticsService:
    @staticmethod
    def workflow_execution_stats(start_date=None, end_date=None, workflow_id=None, user_id=None):
        qs = WorkflowAnalytics.objects.all()
        if start_date:
            qs = qs.filter(executed_at__gte=start_date)
        if end_date:
            qs = qs.filter(executed_at__lte=end_date)
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        if user_id:
            qs = qs.filter(workflow__user_id=user_id)
        return qs.values('workflow').annotate(
            avg_execution_time=Avg('execution_time'),
            total_errors=Sum('error_count'),
            avg_success_rate=Avg('success_rate'),
            executions=Count('id')
        )

    @staticmethod
    def node_performance_stats(workflow_id=None):
        qs = WorkflowAnalytics.objects.all()
        if workflow_id:
            qs = qs.filter(workflow_id=workflow_id)
        # Removed grouping over 'node' and 'memory_usage' since those fields are not defined.
        return qs.values('workflow').annotate(
            avg_execution_time=Avg('execution_time'),
            total_errors=Sum('error_count')
        ).order_by('-avg_execution_time')

    @staticmethod
    def user_activity_report(activity_type=None, user_id=None, day=None, hour=None):
        qs = UserActivityLog.objects.all()
        if activity_type:
            qs = qs.filter(activity_type=activity_type)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if day:
            qs = qs.filter(created_at__date=day)
        if hour:
            qs = qs.filter(created_at__hour=hour)
        return qs.values('user', 'activity_type').annotate(
            count=Count('id'),
            last_activity=Max('created_at')
        )

    @staticmethod
    def system_performance_report(day=None, hour=None):
        qs = PerformanceMetrics.objects.all()
        if day:
            qs = qs.filter(measured_at__date=day)
        if hour:
            qs = qs.filter(measured_at__hour=hour)
        return qs.values('workflow').annotate(
            avg_response_time=Avg('average_response_time'),
            avg_throughput=Avg('throughput'),
            avg_memory=Avg('memory_usage'),
            avg_cpu=Avg('cpu_usage')
        )

    @staticmethod
    def workflow_performance_chart(workflow_id, days=7):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        qs = WorkflowAnalytics.objects.filter(
            workflow_id=workflow_id,
            executed_at__range=(start_date, end_date)
        ).order_by('executed_at')
        if not qs.exists():
            return ""
        dates = [wa.executed_at for wa in qs]
        times = [wa.execution_time for wa in qs]
        plt.figure(figsize=(8, 3))
        plt.plot(dates, times, marker='o')
        plt.title('Workflow Execution Time')
        plt.xlabel('Date')
        plt.ylabel('Execution Time (s)')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return img_base64

    @staticmethod
    def monthly_report(year, month):
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)
        stats = AnalyticsService.workflow_execution_stats(start_date=start, end_date=end)
        user_stats = AnalyticsService.user_activity_report(day=start)
        system_stats = AnalyticsService.system_performance_report(day=start)
        return {
            "workflow_stats": list(stats),
            "user_stats": list(user_stats),
            "system_stats": list(system_stats),
        }
