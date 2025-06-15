from typing import List, Set
from ai_integration.models import NodePort
from workflows.models import Node, NodeConnection

def validate_node_connections(node: Node) -> List[str]:
    """Validate that a node's connections are valid"""
    errors = []
    
    # Get all input and output ports for this node
    input_ports = NodePort.objects.filter(node=node, port_type='input')
    
    # Check that all required input ports have connections
    for port in input_ports:
        if not port.optional:
            connections = NodeConnection.objects.filter(target_node=node, target_port=port.name)
            if not connections.exists():
                errors.append(f"Required input port '{port.name}' has no connection")
                
    return errors