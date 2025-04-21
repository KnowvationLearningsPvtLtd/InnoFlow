from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import WorkflowAnalytics, UserActivityLog, PerformanceMetrics, WorkflowUsageStats
from .serializers import WorkflowAnalyticsSerializer
from .services import AnalyticsService
from django.db.models import Avg, Sum
# Create your views here.

class AnalyticsViewSet(viewsets.ModelViewSet):
    queryset = WorkflowAnalytics.objects.all()
    serializer_class = WorkflowAnalyticsSerializer

    @action(detail=False, methods=['get'])
    def workflow_performance(self, request):
        # Aggregate workflow performance metrics
        performance_data = WorkflowAnalytics.objects.values('workflow') \
            .annotate(
                avg_execution_time=Avg('execution_time'),
                total_errors=Sum('error_count'),
                success_rate=Avg('success_rate')
            )
        return Response(performance_data)

    @action(detail=False, methods=['get'])
    def system_performance(self, request):
        """Get overall system performance metrics"""
        performance_data = PerformanceMetrics.objects.values('workflow') \
            .annotate(
                avg_response_time=Avg('average_response_time'),
                avg_throughput=Avg('throughput'),
                avg_memory=Avg('memory_usage'),
                avg_cpu=Avg('cpu_usage')
            )
        return Response(performance_data)

    @action(detail=False, methods=['get'])
    def usage_statistics(self, request):
        """Get workflow usage statistics"""
        usage_data = WorkflowUsageStats.objects.values('workflow') \
            .annotate(
                total_runs=Sum('total_executions'),
                total_users=Sum('unique_users')
            )
        return Response(usage_data)

    @action(detail=False, methods=['get'])
    def workflow_execution_stats(self, request):
        # Query params: start_date, end_date, workflow_id, user_id
        stats = AnalyticsService.workflow_execution_stats(
            start_date=request.query_params.get('start_date'),
            end_date=request.query_params.get('end_date'),
            workflow_id=request.query_params.get('workflow_id'),
            user_id=request.query_params.get('user_id')
        )
        return Response(list(stats))

    @action(detail=False, methods=['get'])
    def node_performance_stats(self, request):
        stats = AnalyticsService.node_performance_stats(
            workflow_id=request.query_params.get('workflow_id')
        )
        return Response(list(stats))

    @action(detail=False, methods=['get'])
    def user_activity_report(self, request):
        stats = AnalyticsService.user_activity_report(
            activity_type=request.query_params.get('activity_type'),
            user_id=request.query_params.get('user_id'),
            day=request.query_params.get('day'),
            hour=request.query_params.get('hour')
        )
        return Response(list(stats))

    @action(detail=False, methods=['get'])
    def system_performance_report(self, request):
        stats = AnalyticsService.system_performance_report(
            day=request.query_params.get('day'),
            hour=request.query_params.get('hour')
        )
        return Response(list(stats))

    @action(detail=False, methods=['get'])
    def workflow_performance_chart(self, request):
        workflow_id = request.query_params.get('workflow_id')
        days = int(request.query_params.get('days', 7))
        img_base64 = AnalyticsService.workflow_performance_chart(workflow_id, days)
        return Response({'image_base64': img_base64})

    @action(detail=False, methods=['get'])
    def monthly_report(self, request):
        year = int(request.query_params.get('year'))
        month = int(request.query_params.get('month'))
        report = AnalyticsService.monthly_report(year, month)
        return Response(report)
