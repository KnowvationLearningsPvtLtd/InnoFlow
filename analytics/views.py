from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Sum
from .models import WorkflowAnalytics, UserActivityLog, PerformanceMetrics, WorkflowUsageStats
from analytics.serializers import WorkflowAnalyticsSerializer
from analytics.services import AnalyticsService

# Create your views here.

class AnalyticsViewSet(viewsets.ModelViewSet):
    queryset = WorkflowAnalytics.objects.all()
    serializer_class = WorkflowAnalyticsSerializer

    @action(detail=False, methods=['get'])
    def workflow_performance(self, request):
        # Aggregate workflow performance metrics
        performance_data = list(WorkflowAnalytics.objects.values('workflow') \
            .annotate(
                avg_execution_time=Avg('execution_time'),
                total_errors=Sum('error_count'),
                success_rate=Avg('success_rate')
            ))
        return Response(performance_data)

    @action(detail=False, methods=['get'])
    def system_performance(self, request):
        """Get overall system performance metrics"""
        performance_data = list(PerformanceMetrics.objects.values('workflow') \
            .annotate(
                avg_response_time=Avg('average_response_time'),
                avg_throughput=Avg('throughput'),
                avg_memory=Avg('memory_usage'),
                avg_cpu=Avg('cpu_usage')
            ))
        return Response(performance_data)

    @action(detail=False, methods=['get'])
    def usage_statistics(self, request):
        """Get workflow usage statistics"""
        usage_data = list(WorkflowUsageStats.objects.values('workflow') \
            .annotate(
                total_runs=Sum('total_executions'),
                total_users=Sum('unique_users')
            ))
        return Response(usage_data)

    @action(detail=False, methods=['get'])
    def workflow_execution_stats(self, request):
        # Query params: start_date, end_date, workflow_id, user_id
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        workflow_id = request.query_params.get('workflow_id')
        user_id = request.query_params.get('user_id')
        if not start_date or not end_date:
            return Response({"error": "start_date and end_date are required"}, status=400)
        stats = AnalyticsService.workflow_execution_stats(
            start_date=start_date,
            end_date=end_date,
            workflow_id=workflow_id,
            user_id=user_id
        )
        return Response(list(stats))

    @action(detail=False, methods=['get'])
    def node_performance_stats(self, request):
        workflow_id = request.query_params.get('workflow_id')
        if not workflow_id:
            return Response({"error": "workflow_id is required"}, status=400)
        stats = AnalyticsService.node_performance_stats(
            workflow_id=workflow_id
        )
        return Response(list(stats))

    @action(detail=False, methods=['get'])
    def user_activity_report(self, request):
        activity_type = request.query_params.get('activity_type')
        user_id = request.query_params.get('user_id')
        day = request.query_params.get('day')
        hour = request.query_params.get('hour')
        if not activity_type or not user_id:
            return Response({"error": "activity_type and user_id are required"}, status=400)
        stats = AnalyticsService.user_activity_report(
            activity_type=activity_type,
            user_id=user_id,
            day=day,
            hour=hour
        )
        return Response(list(stats))

    @action(detail=False, methods=['get'])
    def system_performance_report(self, request):
        day = request.query_params.get('day')
        hour = request.query_params.get('hour')
        if not day or not hour:
            return Response({"error": "day and hour are required"}, status=400)
        stats = AnalyticsService.system_performance_report(
            day=day,
            hour=hour
        )
        return Response(list(stats))

    @action(detail=False, methods=['get'])
    def workflow_performance_chart(self, request):
        workflow_id = request.query_params.get('workflow_id')
        days = int(request.query_params.get('days', 7))
        if not workflow_id:
            return Response({"error": "workflow_id is required"}, status=400)
        img_base64 = AnalyticsService.workflow_performance_chart(workflow_id, days)
        return Response({'image_base64': img_base64})

    @action(detail=False, methods=['get'])
    def monthly_report(self, request):
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        if not year or not month:
            return Response({"error": "year and month are required"}, status=400)
        report = AnalyticsService.monthly_report(int(year), int(month))
        return Response(report)
