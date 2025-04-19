

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Track only workflow executions
        if request.path.startswith('/api/workflows/') and request.method == 'POST':
            WorkflowAnalytics.objects.create(
                workflow_id=request.data.get('workflow_id'),
                execution_time=response.elapsed.total_seconds(),
                success_rate=1.0 if response.status_code == 200 else 0.0,
                error_count=0 if response.status_code == 200 else 1
            )
        
        return response