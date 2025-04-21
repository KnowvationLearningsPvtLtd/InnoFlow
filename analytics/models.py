from django.db import models
from users.models import UserProfile
from workflows.models import Workflow
from django.conf import settings
from django.utils import timezone

class WorkflowAnalytics(models.Model):
    workflow = models.ForeignKey('workflows.Workflow', on_delete=models.CASCADE)
    execution_time = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20)
    
    class Meta:
        verbose_name_plural = "Workflow Analytics"

class UserActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.created_at}"

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

class ExecutionMetrics(models.Model):
    execution = models.OneToOneField(
        'workflows.WorkflowExecution',
        on_delete=models.CASCADE,
        related_name='metrics'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True)
    workflow_id = models.IntegerField()
    total_execution_time = models.FloatField(null=True)
    memory_usage = models.FloatField(null=True)
    cpu_usage = models.FloatField(null=True)
    status = models.CharField(max_length=50)

    def __str__(self):
        return f"Metrics for execution {self.execution_id}"

class AIModelUsage(models.Model):
    metrics = models.ForeignKey(
        ExecutionMetrics,
        on_delete=models.CASCADE,
        related_name='ai_model_usages'
    )
    model_id = models.IntegerField()
    node_id = models.IntegerField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True)
    tokens_used = models.IntegerField(null=True)
    api_calls = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)

    def __str__(self):
        return f"AI Model {self.model_id} usage in node {self.node_id}"
