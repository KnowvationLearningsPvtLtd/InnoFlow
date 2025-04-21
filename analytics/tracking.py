from celery import shared_task
from django.utils import timezone
import logging
from .models import ExecutionMetrics, AIModelUsage, WorkflowAnalytics, UserActivityLog

logger = logging.getLogger(__name__)

@shared_task
def track_execution(execution_id, user_id):
    from workflows.models import WorkflowExecution  # Import here to avoid circular import
    
    try:
        execution = WorkflowExecution.objects.get(id=execution_id)
        
        metrics = ExecutionMetrics.objects.create(
            execution=execution,
            user_id=user_id,
            start_time=timezone.now(),
            workflow_id=execution.workflow_id,
            status=execution.status
        )
        
        # Track AI model usage
        ai_nodes = execution.workflow.nodes.filter(type__startswith='ai_')
        for node in ai_nodes:
            AIModelUsage.objects.create(
                metrics=metrics,
                model_id=node.config.get('model_id'),
                node_id=node.id
            )
            
        return metrics.id
            
    except Exception as e:
        logger.error(f"Error tracking execution {execution_id}: {str(e)}")
        return None

def track_workflow_execution(workflow, execution):
    """Track workflow execution analytics"""
    WorkflowAnalytics.objects.create(
        workflow=workflow,
        execution_time=timezone.now(),
        status=execution.status
    )
    
    UserActivityLog.objects.create(
        user=workflow.user,
        activity_type='workflow_execution',
        workflow=workflow,
        timestamp=timezone.now()
    )
