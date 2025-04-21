from celery import shared_task
from django.utils import timezone
from workflows.models import Workflow, WorkflowExecution
from analytics.models import WorkflowAnalytics
from workflows.utils import execute_node
import logging

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    def __init__(self, workflow_id):
        """Initialize with just workflow_id, execution will be created/fetched as needed"""
        self.workflow = Workflow.objects.get(id=workflow_id)
        self.execution = None

    def set_execution(self, execution_id=None):
        """Set or create execution"""
        if execution_id:
            self.execution = WorkflowExecution.objects.get(id=execution_id)
        else:
            self.execution = WorkflowExecution.objects.create(
                workflow=self.workflow,
                status='pending'
            )
        return self.execution

    def execute_workflow(self):
        """Execute the workflow"""
        if not self.execution:
            self.set_execution()

        try:
            nodes = self.workflow.nodes.all().order_by('order')
            if not nodes.exists():
                raise ValueError("No nodes in workflow")
            
            for node in nodes:
                if not node.config:
                    raise ValueError(f"Missing configuration for node {node.id}")
                
                # For AI completion nodes, verify model config
                if node.type == 'ai_completion':
                    if 'model_config_id' not in node.config:
                        raise ValueError(f"Missing model_config_id for AI node {node.id}")
            
            input_data = None
            
            for node in nodes:
                try:
                    result = self.execute_node(node, input_data)
                    input_data = result
                except Exception as e:
                    logger.error(f"Node execution failed: {str(e)}", exc_info=True)
                    self.execution.status = 'failed'
                    self.execution.error_message = str(e)
                    self.execution.save()
                    raise

            self.execution.status = 'completed'
            self.execution.results = input_data

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
            self.execution.status = 'failed'
            self.execution.error_message = str(e)
            
        finally:
            self.execution.end_time = timezone.now()
            self.execution.calculate_execution_time()
            self.execution.save()
            
            # Create analytics entry
            WorkflowAnalytics.objects.create(
                workflow=self.workflow,
                execution_time=timezone.now(),
                status=self.execution.status
            )
            
            return input_data

    def execute_node(self, node, input_data):
        """Execute a single node"""
        try:
            return execute_node(node, input_data)
        except Exception as e:
            logger.error(f"Node execution failed: {str(e)}", exc_info=True)
            if not self.workflow.continue_on_error:
                raise
            return None
