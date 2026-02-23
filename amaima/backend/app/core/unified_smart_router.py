"""
AMAIMA Part V - Unified Smart Router Engine
Consolidates routing intelligence from Parts I-IV
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime
import re
import psutil
import socket
import json
import hashlib
import logging
from collections import defaultdict
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """Query complexity taxonomy with 5 levels"""
    TRIVIAL = 1
    SIMPLE = 2
    MODERATE = 3
    COMPLEX = 4
    EXPERT = 5


class ExecutionMode(Enum):
    """Routing strategies for query execution"""
    OFFLINE_LOCAL = "offline_local"
    HYBRID_LOCAL_FIRST = "hybrid_local_first"
    HYBRID_CLOUD_FIRST = "hybrid_cloud_first"
    CLOUD_ONLY = "cloud_only"


class ModelSize(Enum):
    """Model size variants with resource requirements"""
    NANO_1B = {"ram_gb": 2, "vram_gb": 0.5, "parameters": "1B"}
    SMALL_3B = {"ram_gb": 6, "vram_gb": 2, "parameters": "3B"}
    MEDIUM_7B = {"ram_gb": 14, "vram_gb": 4, "parameters": "7B"}
    LARGE_13B = {"ram_gb": 26, "vram_gb": 8, "parameters": "13B"}
    XL_34B = {"ram_gb": 68, "vram_gb": 16, "parameters": "34B"}
    ULTRA_200B = {"ram_gb": 400, "vram_gb": 80, "parameters": "200B"}


class SecurityLevel(Enum):
    """Security tiers for operations"""
    STANDARD = "standard"
    ELEVATED = "elevated"
    CRITICAL = "critical"


@dataclass
class DeviceCapability:
    """Device hardware specifications"""
    cpu_cores: int
    cpu_percent: float
    ram_total_gb: float
    ram_available_gb: float
    vram_total_gb: float
    vram_available_gb: float
    has_gpu: bool
    battery_percent: Optional[float]
    is_metered: bool = False
    thermal_throttling: bool = False
    
    @staticmethod
    def detect() -> 'DeviceCapability':
        """Factory method for dynamic capability detection"""
        has_gpu = False
        vram_total = 0
        vram_available = 0
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            has_gpu = len(gpus) > 0
            vram_total = sum(gpu.memoryTotal for gpu in gpus) / 1024 if has_gpu else 0
            vram_available = sum(gpu.memoryFree for gpu in gpus) / 1024 if has_gpu else 0
        except (ImportError, Exception):
            pass
        
        battery = None
        try:
            battery = psutil.sensors_battery()
            battery_percent = battery.percent if battery else None
        except Exception:
            battery_percent = None
        
        return DeviceCapability(
            cpu_cores=psutil.cpu_count(),
            cpu_percent=psutil.cpu_percent(),
            ram_total_gb=psutil.virtual_memory().total / (1024**3),
            ram_available_gb=psutil.virtual_memory().available / (1024**3),
            vram_total_gb=vram_total,
            vram_available_gb=vram_available,
            has_gpu=has_gpu,
            battery_percent=battery_percent,
            is_metered=False,
            thermal_throttling=False
        )


@dataclass
class ConnectivityStatus:
    """Network connectivity assessment"""
    is_available: bool
    connection_type: str
    latency_ms: float
    bandwidth_mbps: float
    last_check: datetime
    
    @staticmethod
    def check() -> 'ConnectivityStatus':
        """Check network availability and quality"""
        is_available = False
        connection_type = "unknown"
        latency_ms = 0.0
        bandwidth_mbps = 0.0
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            is_available = sock.connect_ex(("8.8.8.8", 53)) == 0
            sock.close()
            
            if is_available:
                connection_type = "broadband"
                try:
                    import speedtest
                    st = speedtest.Speedtest()
                    st.get_best_server()
                    latency_ms = st.results.ping
                    bandwidth_mbps = st.download() / 1e6
                except ImportError:
                    latency_ms = 50.0
                    bandwidth_mbps = 100.0
        except Exception as e:
            logger.warning(f"Connectivity check failed: {e}")
        
        return ConnectivityStatus(
            is_available=is_available,
            connection_type=connection_type,
            latency_ms=latency_ms,
            bandwidth_mbps=bandwidth_mbps,
            last_check=datetime.now()
        )


@dataclass
class RoutingDecision:
    """Complete routing decision with rationale"""
    execution_mode: ExecutionMode
    model_size: ModelSize
    complexity: QueryComplexity
    security_level: SecurityLevel
    confidence: float
    estimated_latency_ms: float
    estimated_cost: float
    fallback_chain: List[ExecutionMode]
    reasoning: Dict[str, Any]
    timestamp: datetime


class ComplexityAnalyzer:
    """Multi-pattern query complexity assessment"""
    
    def __init__(self):
        self.patterns = {
            QueryComplexity.TRIVIAL: [
                r"^(what|who|when|where|how)\s+(is|are|do|does)\s+",
                r"^define\s+",
                r"^[a-z]+\s+means?\s*",
            ],
            QueryComplexity.SIMPLE: [
                r"explain\s+(the\s+)?",
                r"describe\s+",
                r"compare\s+",
                r"summarize\s+",
            ],
            QueryComplexity.MODERATE: [
                r"analyze\s+",
                r"evaluate\s+",
                r"why\s+does\s+",
                r"how\s+to\s+",
                r"implement\s+",
            ],
            QueryComplexity.COMPLEX: [
                r"design\s+(a\s+)?(system|architecture|protocol)",
                r"compare\s+(and\s+contrast|vs\.?)\s+",
                r"optimize\s+(for|performance|scalability)",
                r"explain\s+(the\s+)?(relationship|difference)\s+between",
            ],
            QueryComplexity.EXPERT: [
                r"prove\s+",
                r"derive\s+",
                r"given\s+(the\s+)?(following|conditions|constraints)",
                r"develop\s+(a\s+)?(novel|new|original)",
            ]
        }
        
        self.history: Dict[str, Tuple[QueryComplexity, datetime]] = {}
        self.max_history = 1000
        self.history_ttl_days = 30
    
    def analyze(self, query: str) -> Tuple[QueryComplexity, float]:
        """
        Analyze query complexity with confidence scoring
        
        Args:
            query: The user's query text
            
        Returns:
            Tuple of (complexity level, confidence score)
        """
        query_lower = query.lower().strip()
        word_count = len(query_lower.split())
        
        hash_key = hashlib.md5(query_lower.encode()).hexdigest()
        if hash_key in self.history:
            stored_complexity, timestamp = self.history[hash_key]
            if (datetime.now() - timestamp).days < self.history_ttl_days:
                return stored_complexity, 0.95
        
        confidence = 0.5
        matched_complexity = QueryComplexity.MODERATE
        
        for complexity, patterns in reversed(list(self.patterns.items())):
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    matched_complexity = complexity
                    confidence = 0.85 if complexity != QueryComplexity.MODERATE else 0.7
                    break
            else:
                continue
            break
        
        if word_count < 5 and matched_complexity.value >= QueryComplexity.MODERATE.value:
            matched_complexity = QueryComplexity(max(1, matched_complexity.value - 1))
            confidence *= 0.8
        elif word_count > 50 and matched_complexity.value <= QueryComplexity.MODERATE.value:
            matched_complexity = QueryComplexity(min(5, matched_complexity.value + 1))
            confidence *= 0.9
        
        self.history[hash_key] = (matched_complexity, datetime.now())
        if len(self.history) > self.max_history:
            oldest_keys = list(self.history.keys())[:100]
            for key in oldest_keys:
                del self.history[key]
        
        return matched_complexity, confidence


class DARPAToolIntegrator:
    """Integration with DARPA AIxCC tools for security operations"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.tool_status = {
            "buttercup": False,
            "sweetbaby": False,
            "xbow": False,
            "ludushound": False
        }
        self.vulnerability_history: List[Dict] = []
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize DARPA tool connections"""
        if not self.enabled:
            logger.info("DARPA tools integration disabled")
            return
        
        try:
            from darpa_tools import buttercup, sweetbaby
            self.tool_status["buttercup"] = True
            self.tool_status["sweetbaby"] = True
            logger.info("DARPA tools initialized successfully")
        except ImportError:
            logger.warning("DARPA tools not available, using fallback security")
    
    def assess_security_level(self, operation: str, query: str) -> SecurityLevel:
        """
        Determine security level based on operation type and query content
        
        Args:
            operation: Type of operation (code_generation, system_command, etc.)
            query: The query content
            
        Returns:
            Security level recommendation
        """
        if not self.enabled:
            return SecurityLevel.STANDARD
        
        critical_patterns = [
            r"sudo\s+",
            r"rm\s+-rf",
            r"chmod\s+777",
            r"drop\s+database",
            r"delete\s+from\s+\w+",
            r"eval\s*\(",
            r"exec\s*\(",
            r"subprocess",
        ]
        
        elevated_patterns = [
            r"import\s+os",
            r"import\s+sys",
            r"file\s+(read|write|create)",
            r"connect\s+to\s+(database|server|api)",
            r"http\s*(request|get|post)",
        ]
        
        query_lower = query.lower()
        
        for pattern in critical_patterns:
            if re.search(pattern, query_lower):
                self._log_security_event("critical", operation, pattern)
                return SecurityLevel.CRITICAL
        
        for pattern in elevated_patterns:
            if re.search(pattern, query_lower):
                self._log_security_event("elevated", operation, pattern)
                return SecurityLevel.ELEVATED
        
        return SecurityLevel.STANDARD
    
    def _log_security_event(self, level: str, operation: str, pattern: str):
        """Log security-relevant events"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "operation": operation,
            "pattern": pattern
        }
        self.vulnerability_history.append(event)
        logger.warning(f"Security event: {level} - {operation}")


class SmartRouter:
    """
    Main routing engine coordinating query routing decisions
    """
    
    # Model requirements matrix
    MODEL_REQUIREMENTS = {
        QueryComplexity.TRIVIAL: ModelSize.NANO_1B,
        QueryComplexity.SIMPLE: ModelSize.SMALL_3B,
        QueryComplexity.MODERATE: ModelSize.MEDIUM_7B,
        QueryComplexity.COMPLEX: ModelSize.LARGE_13B,
        QueryComplexity.EXPERT: ModelSize.XL_34B,
    }
    
    # Cost estimation (per 1K tokens)
    COST_PER_MODEL = {
        ModelSize.NANO_1B: 0.30,
        ModelSize.SMALL_3B: 0.45,
        ModelSize.MEDIUM_7B: 0.60,
        ModelSize.LARGE_13B: 0.90,
        ModelSize.XL_34B: 1.20,
        ModelSize.ULTRA_200B: 1.50,
    }

    # Domain Detection Keywords
    DOMAIN_KEYWORDS = {
        "biology": [r"protein", r"molecule", r"drug", r"smiles", r"docking", r"biomedical", r"gene", r"sequence"],
        "robotics": [r"robot", r"arm", r"navigation", r"path", r"grasp", r"manipulation", r"actuator", r"ros2", r"isaac"],
        "vision": [r"image", r"picture", r"photo", r"video", r"scene", r"detect", r"segment", r"visual"],
        "audio": [r"audio", r"speech", r"voice", r"listen", r"transcript", r"stt", r"tts", r"sound"],
        "image_gen": [r"generate image", r"create image", r"make a picture", r"draw", r"illustrate"],
    }
    
    # Latency estimates (baseline ms + per token)
    LATENCY_BASELINE = {
        ExecutionMode.OFFLINE_LOCAL: 15,
        ExecutionMode.HYBRID_LOCAL_FIRST: 25,
        ExecutionMode.HYBRID_CLOUD_FIRST: 80,
        ExecutionMode.CLOUD_ONLY: 120,
    }
    
    def __init__(self, darpa_enabled: bool = True, cache_ttl: int = 5):
        self.complexity_analyzer = ComplexityAnalyzer()
        self.darpa_integrator = DARPAToolIntegrator(enabled=darpa_enabled)
        self.device_cache: Optional[DeviceCapability] = None
        self.connectivity_cache: Optional[ConnectivityStatus] = None
        self.cache_ttl = cache_ttl
        self._last_device_check = None
        self._last_connectivity_check = None
        
        # Weighted Confidence Aggregation
        self.confidence_weights = {
            "complexity": 0.4,
            "model_fit": 0.35,
            "execution_fit": 0.25
        }
        
        logger.info("Smart Router initialized")
    
    def _calculate_overall_confidence(self, comp_conf: float, model_fit: float, exec_fit: float) -> float:
        """Calculate weighted confidence aggregate"""
        return (
            comp_conf * self.confidence_weights.get("complexity", 0.4) +
            model_fit * self.confidence_weights.get("model_fit", 0.35) +
            exec_fit * self.confidence_weights.get("execution_fit", 0.25)
        )
    
    def _get_device_capability(self) -> DeviceCapability:
        """Get cached device capabilities"""
        if (self.device_cache is None or 
            self._last_device_check is None or
            (datetime.now() - self._last_device_check).seconds > self.cache_ttl):
            self.device_cache = DeviceCapability.detect()
            self._last_device_check = datetime.now()
        return self.device_cache
    
    def _get_connectivity_status(self) -> ConnectivityStatus:
        """Get cached connectivity status"""
        if (self.connectivity_cache is None or
            self._last_connectivity_check is None or
            (datetime.now() - self._last_connectivity_check).seconds > self.cache_ttl):
            self.connectivity_cache = ConnectivityStatus.check()
            self._last_connectivity_check = datetime.now()
        return self.connectivity_cache
    
    def route(self, query: str, operation: str = "general",
              user_preference: Optional[ExecutionMode] = None) -> RoutingDecision:
        """
        Main routing decision method
        
        Args:
            query: The user's query
            operation: Type of operation (code_generation, analysis, etc.)
            user_preference: Optional user-specified execution mode
            
        Returns:
            Complete routing decision with rationale
        """
        query_lower = query.lower()
        detected_domain = "general"
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if any(re.search(kw, query_lower) for kw in keywords):
                detected_domain = domain
                break
        
        device = self._get_device_capability()
        connectivity = self._get_connectivity_status()
        complexity, confidence = self.complexity_analyzer.analyze(query)
        security_level = self.darpa_integrator.assess_security_level(operation, query)
        
        if user_preference:
            mode = user_preference
            reasoning = {"source": "user_preference", "value": mode.value}
        else:
            mode = self._determine_execution_mode(
                complexity, device, connectivity, security_level
            )
            reasoning = self._build_reasoning(complexity, device, connectivity, security_level)
        
        reasoning["detected_domain"] = detected_domain
        
        model_size = self._select_model(complexity, device, security_level)
        fallback_chain = self._build_fallback_chain(mode, device, connectivity)
        estimated_latency = self._estimate_latency(mode, complexity, query)
        estimated_cost = self._estimate_cost(model_size, query)
        
        return RoutingDecision(
            execution_mode=mode,
            model_size=model_size,
            complexity=complexity,
            security_level=security_level,
            confidence=confidence,
            estimated_latency_ms=estimated_latency,
            estimated_cost=estimated_cost,
            fallback_chain=fallback_chain,
            reasoning=reasoning,
            timestamp=datetime.now()
        )
    
    def _determine_execution_mode(self, complexity: QueryComplexity,
                                   device: DeviceCapability,
                                   connectivity: ConnectivityStatus,
                                   security_level: SecurityLevel) -> ExecutionMode:
        """Determine optimal execution mode based on conditions"""
        
        if not connectivity.is_available:
            return ExecutionMode.OFFLINE_LOCAL
        
        if device.battery_percent and device.battery_percent < 20:
            return ExecutionMode.HYBRID_LOCAL_FIRST
        
        if device.is_metered:
            return ExecutionMode.HYBRID_LOCAL_FIRST
        
        if security_level == SecurityLevel.CRITICAL and not device.has_gpu:
            return ExecutionMode.CLOUD_ONLY
        
        if complexity.value >= QueryComplexity.EXPERT.value:
            if device.ram_available_gb < 26 or not device.has_gpu:
                return ExecutionMode.CLOUD_ONLY
            return ExecutionMode.HYBRID_LOCAL_FIRST
        
        return ExecutionMode.HYBRID_LOCAL_FIRST
    
    def _select_model(self, complexity: QueryComplexity,
                      device: DeviceCapability,
                      security_level: SecurityLevel) -> ModelSize:
        """Select optimal model size based on conditions"""
        
        base_model = self.MODEL_REQUIREMENTS[complexity]
        
        if security_level == SecurityLevel.CRITICAL:
            if device.ram_available_gb >= 68:
                return ModelSize.XL_34B
        
        if device.ram_available_gb < base_model.value["ram_gb"]:
            for model in ModelSize:
                if device.ram_available_gb >= model.value["ram_gb"]:
                    return model
            return ModelSize.NANO_1B
        
        if device.has_gpu and device.vram_available_gb >= base_model.value["vram_gb"]:
            return base_model
        
        if not device.has_gpu and base_model.value["vram_gb"] > 0:
            smaller_models = [
                ModelSize.NANO_1B, ModelSize.SMALL_3B, ModelSize.MEDIUM_7B
            ]
            for model in smaller_models:
                if device.ram_available_gb >= model.value["ram_gb"]:
                    return model
        
        return base_model
    
    def _build_fallback_chain(self, primary: ExecutionMode,
                               device: DeviceCapability,
                               connectivity: ConnectivityStatus) -> List[ExecutionMode]:
        """Build fallback chain for failure scenarios"""
        
        fallbacks = []
        
        if primary == ExecutionMode.CLOUD_ONLY:
            if connectivity.is_available:
                fallbacks.extend([ExecutionMode.HYBRID_CLOUD_FIRST, ExecutionMode.HYBRID_LOCAL_FIRST])
            else:
                fallbacks.append(ExecutionMode.OFFLINE_LOCAL)
        
        elif primary == ExecutionMode.HYBRID_CLOUD_FIRST:
            fallbacks.extend([ExecutionMode.HYBRID_LOCAL_FIRST, ExecutionMode.OFFLINE_LOCAL])
        
        elif primary == ExecutionMode.HYBRID_LOCAL_FIRST:
            fallbacks.extend([ExecutionMode.OFFLINE_LOCAL])
        
        else:
            fallbacks = [ExecutionMode.OFFLINE_LOCAL]
        
        return fallbacks
    
    def _estimate_latency(self, mode: ExecutionMode,
                          complexity: QueryComplexity,
                          query: str) -> float:
        """Estimate response latency in milliseconds"""
        
        token_count = len(query.split()) * 1.3
        baseline = self.LATENCY_BASELINE[mode]
        
        if mode == ExecutionMode.OFFLINE_LOCAL:
            per_token_ms = 0.5
        elif mode == ExecutionMode.HYBRID_LOCAL_FIRST:
            per_token_ms = 0.8
        elif mode == ExecutionMode.HYBRID_CLOUD_FIRST:
            per_token_ms = 1.5
        else:
            per_token_ms = 2.0
        
        complexity_multiplier = 1 + (complexity.value - 1) * 0.2
        
        return baseline + (token_count * per_token_ms * complexity_multiplier)
    
    def _estimate_cost(self, model: ModelSize, query: str) -> float:
        """Estimate cost per query in USD"""
        
        token_count = len(query.split()) * 1.3
        base_cost = self.COST_PER_MODEL[model]
        
        return base_cost * (token_count / 1000)
    
    def _build_reasoning(self, complexity: QueryComplexity,
                         device: DeviceCapability,
                         connectivity: ConnectivityStatus,
                         security_level: SecurityLevel) -> Dict[str, Any]:
        """Build detailed reasoning for routing decision"""
        
        return {
            "complexity_level": complexity.name,
            "complexity_value": complexity.value,
            "device_has_gpu": device.has_gpu,
            "device_ram_gb": round(device.ram_available_gb, 2),
            "network_available": connectivity.is_available,
            "network_type": connectivity.connection_type,
            "latency_ms": round(connectivity.latency_ms, 2),
            "security_level": security_level.name,
            "battery_percent": device.battery_percent,
            "is_metered": device.is_metered,
        }
