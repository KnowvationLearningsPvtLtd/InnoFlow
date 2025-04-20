import time
from .metrics import API_REQUEST_COUNT, API_ERROR_COUNT, API_LATENCY

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Record metrics
        endpoint = request.path
        API_REQUEST_COUNT.labels(
            endpoint=endpoint,
            method=request.method
        ).inc()
        
        if response.status_code >= 400:
            API_ERROR_COUNT.labels(
                endpoint=endpoint,
                status_code=response.status_code
            ).inc()
            
        API_LATENCY.labels(endpoint=endpoint).set(
            time.time() - start_time
        )
        
        return response