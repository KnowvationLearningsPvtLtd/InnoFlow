from prometheus_client import Counter, Gauge

# Workflow metrics
WORKFLOW_EXECUTIONS = Counter(
    'workflow_executions_total',
    'Total number of workflow executions'
)

WORKFLOW_ERRORS = Counter(
    'workflow_errors_total',
    'Number of workflow execution errors'
)

WORKFLOW_LATENCY = Gauge(
    'workflow_execution_latency_seconds',
    'Workflow execution time in seconds'
)

# API metrics
API_REQUEST_COUNT = Counter(
    'api_requests_total',
    'Total API requests',
    ['endpoint', 'method']
)

API_ERROR_COUNT = Counter(
    'api_errors_total',
    'Failed API requests',
    ['endpoint', 'status_code']
)

API_LATENCY = Gauge(
    'api_request_latency_seconds',
    'API request processing time',
    ['endpoint']
)
