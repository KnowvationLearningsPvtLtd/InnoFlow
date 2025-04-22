from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import json
from django.core.exceptions import ValidationError

User = get_user_model()

class Workflow(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    config = models.JSONField(default=dict)

    def __str__(self):
        return self.name

class Node(models.Model):
    VALID_NODE_TYPES = [
        'text_input',
        'openai_tts',
        'huggingface_summarization'
    ]

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='nodes')
    type = models.CharField(max_length=50)
    config = models.JSONField(default=dict)
    order = models.IntegerField()
    is_enabled = models.BooleanField(default=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)

    def __str__(self):
        return f'{self.type} (Workflow: {self.workflow.name})'
    
    def clean(self):
        if self.type not in self.VALID_NODE_TYPES:
            raise ValidationError(f"Invalid node type: {self.type}")
        
        if not self.config:
            raise ValidationError("Config field cannot be blank")
            
        # Validate required config fields based on node type
        if self.type == 'openai_tts' and 'voice' not in self.config:
            raise ValidationError("TTS nodes require a voice configuration")
            
        if self.type == 'text_input' and 'text' not in self.config:
            raise ValidationError("Text input nodes require a text configuration")
        
        if Node.objects.exclude(id=self.id).filter(
            workflow=self.workflow,
            order=self.order
        ).exists():
            raise ValidationError("Duplicate node order in workflow")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class WorkflowExecution(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='executions')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    results = models.JSONField(null=True, blank=True)
    error_logs = models.TextField(null=True, blank=True)
    execution_context = models.JSONField(default=dict)  # Add this field
    variables = models.JSONField(default=dict)  # Add this field
    
    def __str__(self):
        return f"Execution of {self.workflow.name} ({self.status.capitalize()})"

class NodeConnection(models.Model):
    source_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='outputs')
    target_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='inputs')
    source_port = models.CharField(max_length=50, default='output')
    target_port = models.CharField(max_length=50, default='input')

