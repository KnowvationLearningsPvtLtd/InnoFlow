# analytics/serializers.py

class PerformanceMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerformanceMetrics
        fields = '__all__'

class WorkflowUsageStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowUsageStats
        fields = '__all__'