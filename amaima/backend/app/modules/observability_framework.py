"""
AMAIMA Part V - Observability and Monitoring Framework
Comprehensive logging, metrics, and tracing
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager
import threading

try:
    from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False


class StructuredLogger:
    """Structured JSON logging with context"""
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(handler)
        
        self.context: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def set_context(self, **kwargs):
        """Set logging context"""
        with self._lock:
            self.context.update(kwargs)
    
    def clear_context(self):
        """Clear logging context"""
        with self._lock:
            self.context.clear()
    
    def _format_message(self, message: str, **extra) -> str:
        """Format log message with context"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context": self.context.copy()
        }
        log_data["context"].update(extra)
        return json.dumps(log_data)
    
    def info(self, message: str, **extra):
        self.logger.info(self._format_message(message, **extra))
    
    def error(self, message: str, **extra):
        self.logger.error(self._format_message(message, **extra))
    
    def warning(self, message: str, **extra):
        self.logger.warning(self._format_message(message, **extra))
    
    def debug(self, message: str, **extra):
        self.logger.debug(self._format_message(message, **extra))


class MetricsCollector:
    """Prometheus metrics collection"""
    
    def __init__(self, service_name: str = "amaima"):
        self.service_name = service_name
        self._initialized = False
        
        if PROMETHEUS_AVAILABLE:
            self._setup_metrics()
    
    def _setup_metrics(self):
        """Initialize Prometheus metrics"""
        self.query_counter = Counter(
            f'{self.service_name}_queries_total',
            'Total number of queries processed',
            ['complexity', 'mode', 'status']
        )
        
        self.query_latency = Histogram(
            f'{self.service_name}_query_latency_seconds',
            'Query processing latency',
            ['complexity', 'mode'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.model_load_counter = Counter(
            f'{self.service_name}_model_loads_total',
            'Total model loads',
            ['model_name', 'status']
        )
        
        self.model_load_latency = Histogram(
            f'{self.service_name}_model_load_latency_seconds',
            'Model loading latency',
            ['model_name'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.memory_usage = Gauge(
            f'{self.service_name}_memory_usage_bytes',
            'Current memory usage',
            ['component']
        )
        
        self.verification_confidence = Histogram(
            f'{self.service_name}_verification_confidence',
            'Verification confidence scores',
            ['level'],
            buckets=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )
        
        self.routing_decisions = Counter(
            f'{self.service_name}_routing_decisions_total',
            'Total routing decisions',
            ['complexity', 'model_size', 'execution_mode']
        )
        
        self.error_counter = Counter(
            f'{self.service_name}_errors_total',
            'Total errors',
            ['component', 'error_type']
        )
        
        self._initialized = True
    
    def record_query(self, complexity: str, mode: str, status: str, latency: float):
        """Record query metrics"""
        if not self._initialized:
            return
        
        self.query_counter.labels(complexity=complexity, mode=mode, status=status).inc()
        self.query_latency.labels(complexity=complexity, mode=mode).observe(latency)
    
    def record_model_load(self, model_name: str, status: str, latency: float):
        """Record model load metrics"""
        if not self._initialized:
            return
        
        self.model_load_counter.labels(model_name=model_name, status=status).inc()
        self.model_load_latency.labels(model_name=model_name).observe(latency)
    
    def record_verification(self, level: str, confidence: float):
        """Record verification metrics"""
        if not self._initialized:
            return
        
        self.verification_confidence.labels(level=level).observe(confidence)
    
    def record_routing_decision(self, complexity: str, model_size: str, execution_mode: str):
        """Record routing decision"""
        if not self._initialized:
            return
        
        self.routing_decisions.labels(
            complexity=complexity,
            model_size=model_size,
            execution_mode=execution_mode
        ).inc()
    
    def record_error(self, component: str, error_type: str):
        """Record error"""
        if not self._initialized:
            return
        
        self.error_counter.labels(component=component, error_type=error_type).inc()
    
    def set_memory_usage(self, component: str, bytes_used: float):
        """Set memory usage gauge"""
        if not self._initialized:
            return
        
        self.memory_usage.labels(component=component).set(bytes_used)
    
    def start_metrics_server(self, port: int = 9090):
        """Start Prometheus metrics server"""
        if PROMETHEUS_AVAILABLE:
            start_http_server(port)
            logging.info(f"Metrics server started on port {port}")


class DistributedTracer:
    """OpenTelemetry distributed tracing"""
    
    def __init__(self, service_name: str = "amaima"):
        self.service_name = service_name
        self.tracer = None
        self.meter = None
        self._initialized = False
        
        if OPENTELEMETRY_AVAILABLE:
            self._setup_telemetry()
    
    def _setup_telemetry(self):
        """Initialize OpenTelemetry"""
        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer(self.service_name)
        
        reader = PeriodicExportingMetricReader(
            ConsoleMetricExporter(),
            export_interval_millis=60000
        )
        provider = MeterProvider(metric_readers=[reader])
        metrics.set_meter_provider(provider)
        self.meter = metrics.get_meter(self.service_name)
        
        self._initialized = True
    
    @contextmanager
    def span(self, name: str, attributes: Optional[Dict] = None):
        """Create a trace span"""
        if not self._initialized or not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield span
    
    def record_duration(self, name: str, duration_seconds: float, attributes: Optional[Dict] = None):
        """Record duration metric"""
        if not self._initialized or not self.meter:
            return
        
        counter = self.meter.create_counter(
            name=f"{self.service_name}_{name}_duration",
            description=f"Duration of {name} operations"
        )
        counter.add(1, attributes or {})


def trace_function(name: Optional[str] = None):
    """Decorator to trace function execution"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or func.__name__
            
            with tracer.span(span_name, {"function": span_name}):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start
                    tracer.record_duration(span_name, duration, {"status": "success"})
        
        return wrapper
    return decorator


class PerformanceProfiler:
    """Performance profiling utilities"""
    
    def __init__(self):
        self.profiles: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
    
    def profile(self, operation_name: str) -> Callable:
        """Decorator to profile function execution time"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.time() - start
                    with self._lock:
                        if operation_name not in self.profiles:
                            self.profiles[operation_name] = []
                        self.profiles[operation_name].append(duration)
            
            return wrapper
        return decorator
    
    def get_statistics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Get profiling statistics"""
        with self._lock:
            if operation_name:
                durations = self.profiles.get(operation_name, [])
            else:
                durations = [d for durations in self.profiles.values() for d in durations]
        
        if not durations:
            return {}
        
        return {
            "operation": operation_name or "all",
            "count": len(durations),
            "total_seconds": sum(durations),
            "average_seconds": sum(durations) / len(durations),
            "min_seconds": min(durations),
            "max_seconds": max(durations),
            "p50_seconds": sorted(durations)[len(durations) // 2] if durations else 0,
            "p95_seconds": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "p99_seconds": sorted(durations)[int(len(durations) * 0.99)] if durations else 0
        }
    
    def reset(self, operation_name: Optional[str] = None):
        """Reset profiling data"""
        with self._lock:
            if operation_name:
                self.profiles.pop(operation_name, None)
            else:
                self.profiles.clear()


_global_logger = None
_global_metrics = None
_global_tracer = None


def get_logger(name: str = "amaima") -> StructuredLogger:
    """Get or create global logger"""
    global _global_logger
    if _global_logger is None:
        _global_logger = StructuredLogger(name)
    return _global_logger


def get_metrics(service_name: str = "amaima") -> MetricsCollector:
    """Get or create global metrics collector"""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector(service_name)
    return _global_metrics


def get_tracer(service_name: str = "amaima") -> DistributedTracer:
    """Get or create global tracer"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = DistributedTracer(service_name)
    return _global_tracer

async def log_decision_to_db(query: str, decision: dict):
    """
    Logs a routing decision to the database with correct session management.
    """
    from ..database import get_session_local, DecisionTelemetry
    import uuid
    import hashlib
    from datetime import datetime

    session_factory = get_session_local()
    if session_factory is None:
        return
    db = session_factory()
    try:
        telemetry_entry = DecisionTelemetry(
            decision_id=str(uuid.uuid4()),
            query_hash=hashlib.sha256(query.encode()).hexdigest(),
            timestamp=datetime.utcnow(),
            complexity_level=decision.get("complexity_level"),
            model=decision.get("model"),
            execution_mode=decision.get("execution_mode"),
            latency_estimate_ms=decision.get("latency_estimate_ms"),
            cost_estimate_usd=decision.get("cost_estimate_usd"),
            confidence=decision.get("confidence"),
            reason_codes={
                "complexity": [
                    r["code"]
                    for r in decision.get("reasons", {}).get("complexity_reason", [])
                ],
                "model": [
                    r["code"] for r in decision.get("reasons", {}).get("model_reason", [])
                ],
                "execution": [
                    r["code"]
                    for r in decision.get("reasons", {}).get("execution_reason", [])
                ],
            },
            version="1.0",
        )
        db.add(telemetry_entry)
        db.commit()
    except Exception as e:
        get_logger().error(f"Failed to log decision telemetry to DB: {e}")
        db.rollback()
    finally:
        db.close()
