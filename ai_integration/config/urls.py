# ai_integration/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ai_integration.views import AIModelConfigViewSet, ModelComparisonViewSet

router = DefaultRouter()
router.register(r'ai-models', AIModelConfigViewSet, basename='aimodelconfig')
router.register(r'model-comparisons', ModelComparisonViewSet, basename='modelcomparison')

urlpatterns = [
    path('', include(router.urls)),
    # Add a custom action URL for model comparison
    path('model-comparisons/compare/', 
         ModelComparisonViewSet.as_view({'post': 'compare_models'}),
         name='modelcomparison-compare-models'),
]