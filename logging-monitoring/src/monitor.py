import logging
from logging.handlers import RotatingFileHandler
from prometheus_client import start_http_server, Counter, Gauge
import time
import random

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    
    
    fh = RotatingFileHandler(
        'app.log',
        maxBytes=1_000_000,
        backupCount=3,
        encoding='utf-8'
    )
    fh.setFormatter(formatter)
    
    logger.addHandler(ch)
    logger.addHandler(fh)


REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests')
ERROR_COUNT = Counter('http_errors_total', 'Failed requests')
LATENCY = Gauge('request_latency_seconds', 'Processing time in seconds')

def process_request():
    """Simulate and monitor a request"""
    start = time.time()
    try:
        time.sleep(0.5)
        if random.random() < 0.2:
            raise ValueError("Simulated error")
        
        REQUEST_COUNT.inc()
        LATENCY.set(time.time() - start)
        logging.info("Request processed")  
        return True
        
    except Exception as e:
        ERROR_COUNT.inc()
        logging.error(f"Error: {e}", exc_info=True)  
        return False

def main():
    setup_logging()  
    start_http_server(9000)
    logging.info("Metrics available at http://localhost:9000/metrics")

    try:
        while True:
            process_request()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully...")
    finally:
        logging.info("Server stopped")

if __name__ == "__main__":
    main()