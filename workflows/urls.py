# workflows/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import WorkflowViewSet, NodeViewSet, WorkflowExecutionViewSet

app_name = 'workflows'  # Set the application namespace

router = DefaultRouter()
router.register(r'', WorkflowViewSet, basename='workflow')
router.register(r'nodes', NodeViewSet, basename='node')
router.register(r'executions', WorkflowExecutionViewSet, basename='execution')

urlpatterns = router.urls

# Add custom endpoints if needed
# urlpatterns += [
#     path('<int:pk>/execute/', WorkflowViewSet.as_view({'post': 'execute'}), name='workflow-execute'),
# ]