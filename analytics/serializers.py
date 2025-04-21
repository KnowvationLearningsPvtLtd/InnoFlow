# analytics/serializers.py
from rest_framework import serializers
from .models import PerformanceMetrics, WorkflowUsageStats


class PerformanceMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceMetrics
        fields = '__all__'

class WorkflowUsageStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowUsageStats
        fields = '__all__'