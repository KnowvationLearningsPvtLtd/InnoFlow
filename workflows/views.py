from django.shortcuts import render
from rest_framework import viewsets, serializers, status
from rest_framework.permissions import IsAuthenticated
from .models import Workflow, Node, WorkflowExecution
from .serializers import WorkflowSerializer, NodeSerializer, WorkflowExecutionSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from .tasks import run_workflow
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from analytics.tracking import track_execution, track_workflow_execution
from ai_integration.models import AIModel
from analytics.models import WorkflowAnalytics, UserActivityLog
from django.utils import timezone

class WorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated]
    queryset = Workflow.objects.all()

    def get_queryset(self):
        return Workflow.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        workflow = self.get_object()
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            status='pending'
        )
        return Response({
            'status': 'Workflow execution started',
            'execution_id': execution.id
        }, status=status.HTTP_200_OK)

class NodeViewSet(viewsets.ModelViewSet):
    serializer_class = NodeSerializer
    permission_classes = [IsAuthenticated]
    queryset = Node.objects.all()

    def get_queryset(self):
        user_workflows = Workflow.objects.filter(user=self.request.user)
        return Node.objects.filter(workflow__in=user_workflows)

    def perform_create(self, serializer):
        workflow = serializer.validated_data['workflow']
        if workflow.user != self.request.user:
            raise serializers.ValidationError("Cannot create nodes for a workflow you do not own.")
        serializer.save()


class WorkflowExecutionViewSet(viewsets.ModelViewSet):
    queryset = WorkflowExecution.objects.all()
    serializer_class = WorkflowExecutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_workflows = Workflow.objects.filter(user=self.request.user)
        return self.queryset.filter(workflow__in=user_workflows)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        workflow = self.get_object()
        executor = WorkflowExecutor(workflow.id)
        execution = executor.execute_workflow()
        
        # Create analytics entries
        WorkflowAnalytics.objects.create(
            workflow=workflow,
            execution_time=timezone.now(),
            status=execution.status
        )
        
        UserActivityLog.objects.create(
            user=request.user,
            activity_type='workflow_execution',
            details={
                'workflow_id': workflow.id,
                'execution_id': execution.id,
                'status': execution.status
            }
        )
        
        return Response({
            'execution_id': execution.id,
            'status': execution.status
        })

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        execution = self.get_object()
        perf_data = get_execution_performance(execution.id)
        return Response(perf_data)