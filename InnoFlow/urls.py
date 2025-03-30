from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

# Temporary home page view
def home(request):
    return HttpResponse("Django is working!")

urlpatterns = [
    path('admin/', admin.site.urls),  
    path('', home, name='home'),  
    path('auth/', include('dj_rest_auth.urls')),
    path('accounts/', include('allauth.urls')),  
    path('users/', include('users.urls')),  # Keep 'users.urls' since it has authentication
]

