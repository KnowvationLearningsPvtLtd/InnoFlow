from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AIModelConfig, ModelComparison
from .serializers import AIModelConfigSerializer, ModelComparisonSerializer
from .utils.openai_utils import generate_completion
from .models import TaskStatus
from .serializers import TaskStatusSerializer

class TaskStatusViewSet(viewsets.ModelViewSet):
    queryset = TaskStatus.objects.all()
    serializer_class = TaskStatusSerializer
    
class AIModelConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AI model configurations
    """
    queryset = AIModelConfig.objects.all()
    serializer_class = AIModelConfigSerializer


class ModelComparisonViewSet(viewsets.ModelViewSet):
    """
    ViewSet for comparing different AI models
    """
    queryset = ModelComparison.objects.all()
    serializer_class = ModelComparisonSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new model comparison by sending the same prompt to multiple models
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get validated data
        prompt = serializer.validated_data['prompt']
        models = serializer.validated_data['models']
        
        # Generate results for each model
        results = {}
        for model in models:
            # Use the model configuration to generate a completion
            model_response = generate_completion(
                prompt=prompt,
                model=model.model_type,
                **model.parameters
            )
            results[model.name] = model_response
            
        # Save the results to the comparison object
        comparison = serializer.save()
        comparison.results = results
        comparison.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """
        Get the results of a specific comparison
        """
        comparison = self.get_object()
        return Response({
            'prompt': comparison.prompt,
            'models': [model.name for model in comparison.models.all()],
            'results': comparison.results
        })