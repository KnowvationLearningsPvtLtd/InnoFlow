from django.shortcuts import render
from rest_framework import viewsets, serializers, permissions
from rest_framework.permissions import IsAuthenticated
from .models import Workflow, Node, WorkflowExecution
from .serializers import WorkflowSerializer, NodeSerializer, WorkflowExecutionSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from .tasks import run_workflow
from django.db.models import Q

class IsWorkflowOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a workflow to access it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return obj.user == request.user
        # Write permissions are only allowed to the owner
        return obj.user == request.user

class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated, IsWorkflowOwner]  # Only logged-in users can access

    def get_queryset(self):
        return Workflow.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def execute(self, request, pk=None):
        workflow = self.get_object()
        if workflow.user != request.user:
            return Response({"error": "Permission denied"}, status=403)
        
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            status='pending'
        )
        run_workflow.delay(workflow.id, execution.id)
        return Response({
            "status": "Workflow execution started",
            "execution_id": execution.id
        })

class NodeViewSet(viewsets.ModelViewSet):
    serializer_class = NodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_workflows = Workflow.objects.filter(user=self.request.user)
        return Node.objects.filter(workflow__in=user_workflows)

    def perform_create(self, serializer):
        workflow = serializer.validated_data['workflow']
        if workflow.user != self.request.user:
            raise serializers.ValidationError("Cannot create nodes for a workflow you do not own.")
        serializer.save()

class WorkflowExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowExecution.objects.all()
    serializer_class = WorkflowExecutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_workflows = Workflow.objects.filter(user=self.request.user)
        return self.queryset.filter(workflow__in=user_workflows)
