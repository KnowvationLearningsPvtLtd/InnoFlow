import logging
from celery import shared_task
from django.utils import timezone
from .models import WorkflowExecution, Node, NodeConnection
from .utils import execute_node as execute_node_util
from typing import Any, Dict

logger = logging.getLogger(__name__)

class WorkflowExecutor:
    def __init__(self, execution: WorkflowExecution):
        self.execution = execution
        self.workflow = execution.workflow
        self.results = {}
        self.error_logs = []

    def get_node_input(self, node: Node) -> dict:
        """Get input data for a node from its connections"""
        input_data = {}
        input_connections = node.inputs.all()
        
        if input_connections.exists():
            for conn in input_connections:
                if conn.source_node.id in self.results:
                    input_data[conn.target_port] = self.results[conn.source_node.id]
        
        # Add variables to input data
        if self.execution.variables:
            input_data['variables'] = self.execution.variables
            
        return input_data or None

    def execute_node(self, node: Node, input_data=None, retry_count=0):
        """Execute a single node with retry mechanism"""
        try:
            result = execute_node_util(node, input_data)
            self.results[node.id] = result
            return result
        except Exception as e:
            if retry_count < node.max_retries:
                logger.info(f"Retrying node {node.id}, attempt {retry_count + 1}")
                node.retry_count = retry_count + 1
                node.save()
                return self.execute_node(node, input_data, retry_count + 1)
            
            error_msg = f"Error executing node {node.id}: {str(e)}"
            self.error_logs.append(error_msg)
            self.execution.status = 'failed'
            self.execution.error_logs = self.error_logs
            self.execution.save()
            raise

    def execute_workflow(self):
        """Execute the entire workflow"""
        try:
            sorted_nodes = self.workflow.nodes.order_by('order')
            self.execution.status = 'running'
            self.execution.save()
            
            for node in sorted_nodes:
                input_data = self.get_node_input(node)
                result = self.execute_node(node, input_data)
                self.results[node.id] = result
            
            self.execution.status = 'completed'
            self.execution.results = self.results
            self.execution.completed_at = timezone.now()
            self.execution.save()
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            self.execution.status = 'failed'
            self.execution.error_logs = self.error_logs
            self.execution.save()
            raise
