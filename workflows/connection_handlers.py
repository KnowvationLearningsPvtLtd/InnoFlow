# workflows/connection_handling.py
from typing import Dict, List, Any, Optional, Union
from .models import Node, NodeConnection, Workflow
from ai_integration.models import NodePort
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manager for handling node connections in workflows"""
    
    @staticmethod
    def create_connection(source_node_id: int, target_node_id: int, 
                         source_port: str = 'output', target_port: str = 'input') -> NodeConnection:
        """
        Create a connection between two nodes
        
        Args:
            source_node_id: ID of the source node
            target_node_id: ID of the target node
            source_port: Name of the source port (default: 'output')
            target_port: Name of the target port (default: 'input')
            
        Returns:
            The created NodeConnection
        """
        source_node = Node.objects.get(id=source_node_id)
        target_node = Node.objects.get(id=target_node_id)
        
        # Validate nodes are in same workflow
        if source_node.workflow_id != target_node.workflow_id:
            raise ValueError("Cannot connect nodes from different workflows")
        
        # Check if the port exists
        source_port_obj = NodePort.objects.filter(node=source_node, name=source_port, port_type='output').first()
        if not source_port_obj:
            raise ValueError(f"Source port '{source_port}' not found on node {source_node_id}")
            
        target_port_obj = NodePort.objects.filter(node=target_node, name=target_port, port_type='input').first()
        if not target_port_obj:
            raise ValueError(f"Target port '{target_port}' not found on node {target_node_id}")
        
        # Check for existing connections to the same target port
        existing_conn = NodeConnection.objects.filter(
            target_node=target_node,
            target_port=target_port
        ).first()
        
        if existing_conn and not target_port_obj.optional:
            raise ValueError(f"Target port '{target_port}' already has a connection")
        
        # Create the connection
        connection = NodeConnection.objects.create(
            source_node=source_node,
            target_node=target_node,
            source_port=source_port,
            target_port=target_port
        )
        
        return connection
    
    @staticmethod
    def delete_connection(connection_id: int) -> None:
        """Delete a connection by ID"""
        try:
            connection = NodeConnection.objects.get(id=connection_id)
            connection.delete()
        except NodeConnection.DoesNotExist:
            raise ValueError(f"Connection {connection_id} not found")
    
    @staticmethod
    def validate_workflow_connections(workflow_id: int) -> List[str]:
        """
        Validate all connections in a workflow
        
        Args:
            workflow_id: ID of the workflow to validate
            
        Returns:
            List of error messages, empty if valid
        """
        errors = []
        workflow = Workflow.objects.get(id=workflow_id)
        nodes = Node.objects.filter(workflow=workflow)
        connections = NodeConnection.objects.filter(source_node__workflow=workflow)
        
        # Check for cycles in the workflow
        visited = set()
        path = set()
        
        def has_cycle(node_id):
            if node_id in path:
                return True
            
            if node_id in visited:
                return False
                
            visited.add(node_id)
            path.add(node_id)
            
            # Find all connections where this node is the source
            outgoing = connections.filter(source_node_id=node_id)
            for conn in outgoing:
                if has_cycle(conn.target_node_id):
                    return True
                    
            path.remove(node_id)
            return False
        
        # Check for cycles starting from each node
        for node in nodes:
            if node.id not in visited:
                if has_cycle(node.id):
                    errors.append("Workflow contains a cycle")
                    break
        
        # Check required input ports
        for node in nodes:
            input_ports = NodePort.objects.filter(node=node, port_type='input', optional=False)
            for port in input_ports:
                # Each required input port should have exactly one connection
                conn_count = connections.filter(target_node=node, target_port=port.name).count()
                if conn_count == 0:
                    errors.append(f"Node {node.id}: Required input port '{port.name}' has no connection")
                elif conn_count > 1:
                    errors.append(f"Node {node.id}: Required input port '{port.name}' has multiple connections")
        
        return errors
    
    @staticmethod
    def get_node_connections(node_id: int) -> Dict:
        """
        Get all connections for a node
        
        Args:
            node_id: ID of the node
            
        Returns:
            Dictionary with 'incoming' and 'outgoing' connections
        """
        node = Node.objects.get(id=node_id)
        
        incoming = NodeConnection.objects.filter(target_node=node).select_related('source_node')
        outgoing = NodeConnection.objects.filter(source_node=node).select_related('target_node')
        
        return {
            'incoming': [{
                'id': conn.id,
                'source_node': conn.source_node_id,
                'source_port': conn.source_port,
                'target_port': conn.target_port
            } for conn in incoming],
            'outgoing': [{
                'id': conn.id,
                'target_node': conn.target_node_id,
                'source_port': conn.source_port,
                'target_port': conn.target_port
            } for conn in outgoing]
        }