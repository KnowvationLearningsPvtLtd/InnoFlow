# workflows/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkflowViewSet, NodeViewSet, WorkflowExecutionViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'workflows', WorkflowViewSet)
router.register(r'nodes', NodeViewSet)
router.register(r'workflow_executions', WorkflowExecutionViewSet)

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]