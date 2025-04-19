# ai_integration/node_port_integration.py
from typing import List, Dict, Any
from ai_integration.models import NodePort
from workflows.models import Node
from workflows.node_types import NodeTypeRegistry

def create_ports_for_node(node: Node) -> List[NodePort]:
    """
    Create NodePort objects for a node based on its type definition
    
    Args:
        node: The Node object
        
    Returns:
        List of created NodePort objects
    """
    try:
        # Get node type definition
        node_type = NodeTypeRegistry.get_node_type(node.type)
        
        created_ports = []
        
        # Delete existing ports
        NodePort.objects.filter(node=node).delete()
        
        # Create ports based on the definition
        for port_def in node_type.ports:
            port = NodePort.objects.create(
                node=node,
                name=port_def.name,
                port_type=port_def.port_type,
                data_type=port_def.data_type,
                optional=port_def.optional
            )
            created_ports.append(port)
            
        return created_ports
        
    except Exception as e:
        raise ValueError(f"Failed to create ports for node {node.id}: {str(e)}")

def update_workflow_ports(workflow_id: int) -> Dict[str, Any]:
    """
    Update all node ports in a workflow
    
    Args:
        workflow_id: ID of the workflow
        
    Returns:
        Dictionary with counts of created ports by node
    """
    from workflows.models import Workflow
    
    workflow = Workflow.objects.get(id=workflow_id)
    nodes = Node.objects.filter(workflow=workflow)
    
    results = {}
    
    for node in nodes:
        try:
            ports = create_ports_for_node(node)
            results[node.id] = len(ports)
        except Exception as e:
            results[node.id] = str(e)
            
    return {
        'workflow_id': workflow_id,
        'node_results': results,
        'total_nodes': len(nodes)
    }

def validate_node_ports(node: Node) -> List[str]:
    """
    Validate that a node has the correct ports based on its type
    
    Args:
        node: The Node object
        
    Returns:
        List of error messages, empty if valid
    """
    errors = []
    
    try:
        # Get node type definition
        node_type = NodeTypeRegistry.get_node_type(node.type)
        
        # Get existing ports
        existing_ports = {
            (p.name, p.port_type): p for p in NodePort.objects.filter(node=node)
        }
        
        # Check that all defined ports exist
        for port_def in node_type.ports:
            port_key = (port_def.name, port_def.port_type)
            if port_key not in existing_ports:
                errors.append(f"Node {node.id} is missing port '{port_def.name}' of type '{port_def.port_type}'")
                continue
                
            port = existing_ports[port_key]
            if port.data_type != port_def.data_type:
                errors.append(f"Port '{port_def.name}' has incorrect data type: {port.data_type} vs {port_def.data_type}")
            if port.optional != port_def.optional:
                errors.append(f"Port '{port_def.name}' has incorrect optional setting: {port.optional} vs {port_def.optional}")
        
        # Check for extra ports
        for (name, port_type), port in existing_ports.items():
            if not any(p.name == name and p.port_type == port_type for p in node_type.ports):
                errors.append(f"Node {node.id} has extra port '{name}' of type '{port_type}'")
                
    except Exception as e:
        errors.append(f"Error validating node ports: {str(e)}")
        
    return errors