from django.db import models
from users.models import UserProfile
from workflows.models import Workflow

class WorkflowAnalytics(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    execution_time = models.FloatField()
    success_rate = models.FloatField()
    error_count = models.IntegerField(default=0)
    executed_at = models.DateTimeField(auto_now_add=True)

class UserActivityLog(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50)
    details = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

class PerformanceMetrics(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    average_response_time = models.FloatField()
    throughput = models.IntegerField()
    memory_usage = models.FloatField()
    cpu_usage = models.FloatField()
    measured_at = models.DateTimeField(auto_now_add=True)

class WorkflowUsageStats(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    total_executions = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)
    last_executed = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
