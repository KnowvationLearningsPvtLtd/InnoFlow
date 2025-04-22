from django.http import HttpResponse
from analytics.models import WorkflowAnalytics
import json

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store request body before it's consumed
        if request.path.startswith('/api/workflows/') and request.method == 'POST':
            try:
                # Only attempt to decode if there's content
                if request.body:
                    body = json.loads(request.body.decode('utf-8'))
                    workflow_id = body.get('workflow_id')
                    # Store for later use
                    request._workflow_id = workflow_id
            except Exception as e:
                print(f"Middleware Body Parse Error: {e}")

        response = self.get_response(request)
        
        try:
            if request.path.startswith('/api/workflows/') and request.method == 'POST':
                # Use stored workflow_id instead of reading request.body again
                workflow_id = getattr(request, '_workflow_id', None)
                if workflow_id:
                    WorkflowAnalytics.objects.create(
                        workflow_id=workflow_id,
                        execution_time=getattr(response, 'elapsed', 0),
                        success_rate=1.0 if response.status_code == 200 else 0.0,
                        error_count=0 if response.status_code == 200 else 1
                    )
        except Exception as e:
            print(f"Middleware Analytics Error: {e}")
            
        return response