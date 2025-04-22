# analytics/serializers.py
from rest_framework import serializers
from .models import WorkflowAnalytics, PerformanceMetrics, WorkflowUsageStats, UserActivityLog

class WorkflowAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowAnalytics
        fields = '__all__'

class PerformanceMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceMetrics
        fields = '__all__'

class WorkflowUsageStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowUsageStats
        fields = '__all__'

class UserActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivityLog
        fields = '__all__'