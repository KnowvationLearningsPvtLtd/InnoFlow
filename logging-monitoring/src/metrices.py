from prometheus_client import Counter, Gauge

REQUEST_COUNT = Counter(
    'http_requests_total', 
    'Total HTTP requests'
)
ERROR_COUNT = Counter(
    'http_errors_total', 
    'Failed requests'
)
LATENCY = Gauge(
    'request_latency_seconds', 
    'Request processing time'
)