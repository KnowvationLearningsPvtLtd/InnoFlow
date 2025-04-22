from django.urls import path
from .views import AnalyticsViewSet

app_name = 'analytics'

urlpatterns = [
    # Explicitly define each action URL
    path('workflow_performance/', AnalyticsViewSet.as_view({'get': 'workflow_performance'}), name='workflow_performance'),
    path('system_performance/', AnalyticsViewSet.as_view({'get': 'system_performance'}), name='system_performance'),
    path('usage_statistics/', AnalyticsViewSet.as_view({'get': 'usage_statistics'}), name='usage_statistics'),
    path('workflow_execution_stats/', AnalyticsViewSet.as_view({'get': 'workflow_execution_stats'}), name='workflow_execution_stats'),
    path('node_performance_stats/', AnalyticsViewSet.as_view({'get': 'node_performance_stats'}), name='node_performance_stats'),
    path('user_activity_report/', AnalyticsViewSet.as_view({'get': 'user_activity_report'}), name='user_activity_report'),
    path('system_performance_report/', AnalyticsViewSet.as_view({'get': 'system_performance_report'}), name='system_performance_report'),
    path('workflow_performance_chart/', AnalyticsViewSet.as_view({'get': 'workflow_performance_chart'}), name='workflow_performance_chart'),
    path('monthly_report/', AnalyticsViewSet.as_view({'get': 'monthly_report'}), name='monthly_report'),
    
    # Include standard CRUD operations
    path('', AnalyticsViewSet.as_view({'get': 'list', 'post': 'create'}), name='analytics-list'),
    path('<int:pk>/', AnalyticsViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='analytics-detail'),
]