# workflows/validators.py
from typing import List
from .models import Workflow, WorkflowExecution, Node

class WorkflowValidator:
    @staticmethod
    def validate_workflow(workflow: Workflow) -> List[str]:
        errors = []
        
        # Validate workflow structure
        if not workflow.nodes.exists():
            errors.append("Workflow has no nodes")
            return errors

        # Validate execution order
        orders = list(workflow.nodes.values_list('order', flat=True))
        if len(set(orders)) != len(orders):
            errors.append("Duplicate node execution orders found")

        return errors

    @staticmethod
    def validate_execution(execution: WorkflowExecution) -> List[str]:
        errors = []
        
        # Check if workflow exists
        if not execution.workflow:
            errors.append("Execution must be linked to a workflow")
            return errors
        
        # Check if required config exists in workflow
        required_config = execution.workflow.config.get('required_config', {})
        execution_results = execution.results or {}
        
        # Check for missing required values in results
        if required_config:
            for key, config in required_config.items():
                if config.get('required', False) and key not in execution_results:
                    errors.append(f"Required result '{key}' is missing from execution results")

        return errors

class NodeValidator:
    @staticmethod
    def validate_node(node: Node) -> List[str]:
        errors = []
        
        # Basic validation
        if not node.type:
            errors.append("Node must have a type")
            
        # Validate node config against its type requirements
        try:
            from workflows.node_types import NodeTypeRegistry
            node_type = NodeTypeRegistry.get_node_type(node.type)
            config_errors = node_type.validate_config(node.config or {})
            errors.extend(config_errors)
        except Exception as e:
            errors.append(f"Error validating node type: {str(e)}")
            
        return errors