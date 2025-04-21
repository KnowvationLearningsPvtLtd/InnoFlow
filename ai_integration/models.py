from django.db import models
from django.core.exceptions import ValidationError
from django.core.cache import cache

class AIModelConfig(models.Model):
    MODEL_CHOICES = [
        ('OPENAI', 'OpenAI'),
        ('ANTHROPIC', 'Anthropic (Claude)'),
        ('DEEPSEEK', 'DeepSeek'),
        ('OLLAMA', 'Ollama'),
        ('HUGGINGFACE', 'Hugging Face'),
    ]
    
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=20, choices=MODEL_CHOICES)
    model_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    base_url = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parameters = models.JSONField(default=dict)
    model_type = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.provider}: {self.model_name}"
    
    class Meta:
        verbose_name = "AI Model Configuration"
        verbose_name_plural = "AI Model Configurations"
    
    def clean(self):
        if self.provider in ['OPENAI', 'ANTHROPIC', 'DEEPSEEK'] and not self.api_key:
            raise ValidationError(f"API key is required for {self.get_provider_display()} models")

class ModelComparison(models.Model):
    prompt = models.TextField()
    compared_models = models.ManyToManyField(AIModelConfig, related_name='comparisons')  # Changed from 'models' to 'compared_models'
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comparison for: {self.prompt[:50]}..."

class ModelResponse(models.Model):
    comparison = models.ForeignKey(ModelComparison, on_delete=models.CASCADE, related_name='responses')
    model_config = models.ForeignKey(AIModelConfig, on_delete=models.CASCADE)
    response = models.TextField()
    latency = models.FloatField(help_text="Response time in seconds")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['latency']
    
    def __str__(self):
        return f"{self.model_config}: {self.response[:50]}..."
    

class TaskStatus(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    result = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.task_id} - {self.status}"
    
# Add to ai_integration/models.py
class NodePort(models.Model):
    PORT_TYPES = [
        ('input', 'Input'),
        ('output', 'Output'),
    ]
    
    node = models.ForeignKey('workflows.Node', on_delete=models.CASCADE, related_name='ports')
    name = models.CharField(max_length=100)
    port_type = models.CharField(max_length=10, choices=PORT_TYPES)
    data_type = models.CharField(max_length=50, default='any')
    optional = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['node', 'name', 'port_type']
        
    def __str__(self):
        return f"{self.node} - {self.port_type}:{self.name}"

class AIModel(models.Model):
    name = models.CharField(max_length=200)
    provider = models.CharField(max_length=100)
    model_type = models.CharField(max_length=100)
    config = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    
    def to_dict(self):
        cache_key = f"ai_model_{self.id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
            
        data = {
            'id': self.id,
            'name': self.name,
            'provider': self.provider,
            'type': self.model_type,
            'config': self.config
        }
        cache.set(cache_key, data, timeout=3600)
        return data