from rest_framework import serializers
from .models import Workflow, Node, WorkflowExecution

class NodeSerializer(serializers.ModelSerializer):
    workflow = serializers.PrimaryKeyRelatedField(
        queryset=Workflow.objects.all(),
        required=True
    )
    class Meta:
        model = Node
        fields = ['id', 'type', 'config', 'order']
    
    def validate(self, data):
        # Check if user has permission for the workflow
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if data.get('workflow') and data['workflow'].user != request.user:
                raise serializers.ValidationError("You don't have permission to modify this workflow")
        return data

    def validate_workflow(self, value):
        if value.user != self.context['request'].user:
            raise serializers.ValidationError("You do not have permission to create nodes for this workflow.")
        return value

    def validate_type(self, value):
        valid_types = ["text_input", "openai_tts", "huggingface_summarization"]
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid node type: {value}")
        return value

    def validate_config(self, value):
        if self.initial_data.get('type') == "openai_tts":
            if 'voice' not in value:
                raise serializers.ValidationError("Missing 'voice' in config")
        return value

class WorkflowSerializer(serializers.ModelSerializer):
    nodes = NodeSerializer(many=True, read_only=True)  # Include nodes in workflow response

    class Meta:
        model = Workflow
        fields = ['id', 'name', 'user', 'created_at', 'updated_at', 'nodes']

class WorkflowExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowExecution
        fields = [
            'id', 'workflow', 'started_at',
            'completed_at', 'status', 'results', 'error_logs'
        ]