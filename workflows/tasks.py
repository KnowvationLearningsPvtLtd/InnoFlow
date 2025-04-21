from celery import shared_task
from workflows.execution import WorkflowExecutor
from analytics.models import WorkflowAnalytics, UserActivityLog
from workflows.models import WorkflowExecution, Workflow
import logging

logger = logging.getLogger(__name__)

@shared_task
def run_workflow(workflow_id, execution_id=None):
    execution = None
    try:
        executor = WorkflowExecutor(workflow_id)
        if execution_id:
            executor.set_execution(execution_id)
        result = executor.execute_workflow()
        execution = executor.execution

        # Log user activity
        UserActivityLog.objects.create(
            user=executor.workflow.user,
            activity_type='workflow_execution',
            details={
                'workflow_id': workflow_id,
                'execution_id': execution.id,
                'status': execution.status
            }
        )

        return result

    except Exception as e:
        logger.critical(f"Critical workflow error: {str(e)}", exc_info=True)

        if execution_id:
            try:
                WorkflowExecution.objects.filter(id=execution_id).update(
                    status='failed',
                    error_message=str(e)
                )
            except Exception as update_e:
                logger.error(f"Failed to update execution status: {update_e}")
        raise

    finally:
        if execution_id:
            try:
                execution = WorkflowExecution.objects.get(id=execution_id)
                workflow = Workflow.objects.get(id=workflow_id)

                # Log analytics (always)
                WorkflowAnalytics.objects.create(
                    workflow=workflow,
                    execution_time=execution.calculate_execution_time() or 0,  # Default to 0 if None
                    status=execution.status,
                    error_count=1 if execution.status == 'failed' else 0
                )
            except Exception as log_error:
                logger.error(f"Failed to log analytics: {log_error}")
