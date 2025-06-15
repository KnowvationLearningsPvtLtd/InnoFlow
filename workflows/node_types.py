# workflows/node_types.py
from typing import Dict, List, Any, Optional, Union
import json

class NodeTypeRegistry:
    """Registry for available node types in the system"""
    _node_types = {}
    
    @classmethod
    def register(cls, node_type):
        """Register a node type"""
        cls._node_types[node_type.type_name] = node_type
        return node_type
    
    @classmethod
    def get_node_type(cls, type_name: str):
        """Get a node type by name"""
        if type_name not in cls._node_types:
            raise ValueError(f"Unknown node type: {type_name}")
        return cls._node_types[type_name]
    
    @classmethod
    def get_all_node_types(cls):
        """Get all registered node types"""
        return cls._node_types

class PortDefinition:
    """Definition of a node port"""
    def __init__(self, 
                 name: str, 
                 port_type: str, 
                 data_type: str = "any",
                 optional: bool = False,
                 description: str = ""):
        self.name = name
        self.port_type = port_type  # 'input' or 'output'
        self.data_type = data_type
        self.optional = optional
        self.description = description
    
    def to_dict(self):
        return {
            "name": self.name,
            "port_type": self.port_type,
            "data_type": self.data_type,
            "optional": self.optional,
            "description": self.description
        }

class ConfigParam:
    """Definition of a configuration parameter for a node"""
    def __init__(self, 
                 name: str, 
                 param_type: str, 
                 default: Any = None,
                 required: bool = False,
                 description: str = "",
                 options: Optional[List] = None):
        self.name = name
        self.param_type = param_type  # 'string', 'number', 'boolean', 'select'
        self.default = default
        self.required = required
        self.description = description
        self.options = options or []
    
    def to_dict(self):
        return {
            "name": self.name,
            "param_type": self.param_type,
            "default": self.default,
            "required": self.required,
            "description": self.description,
            "options": self.options
        }

class NodeType:
    """Base class for all node types"""
    type_name = None
    category = None
    description = None
    icon = None
    config_params = []
    ports = []
    
    @classmethod
    def get_definition(cls):
        """Get the definition of this node type"""
        return {
            "type_name": cls.type_name,
            "category": cls.category,
            "description": cls.description,
            "icon": cls.icon,
            "config_params": [param.to_dict() for param in cls.config_params],
            "ports": [port.to_dict() for port in cls.ports]
        }
    
    @classmethod
    def create_node_config(cls, **params):
        """Create a node configuration with the given parameters"""
        config = {}
        
        # Start with defaults
        for param in cls.config_params:
            if param.default is not None:
                config[param.name] = param.default
        
        # Override with provided values
        for name, value in params.items():
            param_def = next((p for p in cls.config_params if p.name == name), None)
            if param_def:
                config[name] = value
        
        return config
    
    @classmethod
    def validate_config(cls, config: Dict) -> List[str]:
        """Validate a node configuration against this node type"""
        errors = []
        
        # Check required parameters
        for param in cls.config_params:
            if param.required and (param.name not in config or config[param.name] is None):
                errors.append(f"Required parameter '{param.name}' is missing")
        
        return errors

# Register basic node types
@NodeTypeRegistry.register
class TextInputNode(NodeType):
    type_name = "text_input"
    category = "Input"
    description = "Provides text input for the workflow"
    icon = "text"
    
    config_params = [
        ConfigParam("text", "string", "", False, "Default text value")
    ]
    
    ports = [
        PortDefinition("output", "output", "string", False, "The text output")
    ]

@NodeTypeRegistry.register
class ParameterInputNode(NodeType):
    type_name = "parameter_input"
    category = "Input"
    description = "Provides parameter input for the workflow"
    icon = "settings"
    
    config_params = [
        ConfigParam("param_name", "string", "", True, "Parameter name"),
        ConfigParam("param_type", "select", "string", True, "Parameter type", 
                    ["string", "number", "boolean"]),
        ConfigParam("default_value", "string", "", False, "Default value")
    ]
    
    ports = [
        PortDefinition("output", "output", "any", False, "The parameter value")
    ]

@NodeTypeRegistry.register
class OpenAICompletionNode(NodeType):
    type_name = "openai_completion"
    category = "AI"
    description = "Generate text using OpenAI"
    icon = "brain"
    
    config_params = [
        ConfigParam("model", "string", "gpt-3.5-turbo", True, "Model name"),
        ConfigParam("max_tokens", "number", 100, False, "Maximum tokens"),
        ConfigParam("temperature", "number", 0.7, False, "Temperature")
    ]
    
    ports = [
        PortDefinition("input", "input", "string", False, "The prompt text"),
        PortDefinition("output", "output", "string", False, "Generated completion")
    ]

@NodeTypeRegistry.register
class TextTransformationNode(NodeType):
    type_name = "text_transformation"
    category = "Processing"
    description = "Transform text with various operations"
    icon = "edit"
    
    config_params = [
        ConfigParam("operation", "select", "to_uppercase", True, "Operation to perform", 
                    ["to_uppercase", "to_lowercase", "trim", "replace"])
    ]
    
    ports = [
        PortDefinition("input", "input", "string", False, "Input text"),
        PortDefinition("output", "output", "string", False, "Transformed text")
    ]

@NodeTypeRegistry.register
class TextOutputNode(NodeType):
    type_name = "text_output"
    category = "Output"
    description = "Display text output"
    icon = "message"
    
    config_params = []
    
    ports = [
        PortDefinition("input", "input", "string", False, "Text to display")
    ]

# Function to validate a workflow structure
def validate_workflow_structure(nodes, connections):
    """
    Validate a complete workflow structure
    
    Args:
        nodes: List of nodes in the workflow
        connections: List of connections between nodes
        
    Returns:
        List of error messages, empty if valid
    """
    errors = []
    
    # Check for cycles
    # This is a simple implementation - for a production system,
    # you would want a more sophisticated cycle detection algorithm
    visited = set()
    
    def has_cycle(node_id, path=None):
        if path is None:
            path = []
        
        if node_id in path:
            return True
        
        path = path + [node_id]
        visited.add(node_id)
        
        for conn in connections:
            if conn['source_node'] == node_id:
                if has_cycle(conn['target_node'], path):
                    return True
        
        return False
    
    # Check each node
    for node in nodes:
        node_id = node['id']
        if node_id not in visited:
            if has_cycle(node_id):
                errors.append(f"Workflow contains a cycle")
                break
    
    # Validate node configurations
    for node in nodes:
        node_type_name = node['type']
        try:
            node_type = NodeTypeRegistry.get_node_type(node_type_name)
            config_errors = node_type.validate_config(node.get('config', {}))
            if config_errors:
                errors.extend([f"Node {node['id']}: {err}" for err in config_errors])
        except ValueError as e:
            errors.append(str(e))
    
    # Validate connections
    for conn in connections:
        source_node = next((n for n in nodes if n['id'] == conn['source_node']), None)
        target_node = next((n for n in nodes if n['id'] == conn['target_node']), None)
        
        if not source_node:
            errors.append(f"Connection references non-existent source node {conn['source_node']}")
            continue
            
        if not target_node:
            errors.append(f"Connection references non-existent target node {conn['target_node']}")
            continue
        
        # Validate port existence
        source_type = NodeTypeRegistry.get_node_type(source_node['type'])
        target_type = NodeTypeRegistry.get_node_type(target_node['type'])
        
        source_port = next((p for p in source_type.ports if p.name == conn['source_port']), None)
        target_port = next((p for p in target_type.ports if p.name == conn['target_port']), None)
        
        if not source_port:
            errors.append(f"Connection references non-existent port {conn['source_port']} on source node")
        elif source_port.port_type != 'output':
            errors.append(f"Connection source port {conn['source_port']} is not an output port")
            
        if not target_port:
            errors.append(f"Connection references non-existent port {conn['target_port']} on target node")
        elif target_port.port_type != 'input':
            errors.append(f"Connection target port {conn['target_port']} is not an input port")
    
    return errors