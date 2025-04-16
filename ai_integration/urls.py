from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import (
    AIModelConfigViewSet,
    ModelComparisonViewSet,
    TaskStatusViewSet
)

router = DefaultRouter()
router.register(r'aimodelconfig', AIModelConfigViewSet, basename='aimodelconfig')
router.register(r'modelcomparisons', ModelComparisonViewSet, basename='modelcomparison')
router.register(r'tasks', TaskStatusViewSet, basename='taskstatus')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('', include(router.urls)),
      path('compare-models/', 
         ModelComparisonViewSet.as_view({'post': 'compare_models'}),
         name='modelcomparison-compare-models'),
]