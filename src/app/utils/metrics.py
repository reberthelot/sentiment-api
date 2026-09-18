import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Metrics:
    """In-memory operational metrics collector for request counts and latencies."""

    total_requests: int = 0
    success_requests: int = 0
    failed_requests: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    last_latency_ms: Optional[float] = None

    def record(self, ok: bool, latency_ms: float) -> None:
        """Record the outcome and latency of an operational request."""
        self.total_requests += 1
        self.success_requests += int(ok)
        self.failed_requests += int(not ok)
        self.last_latency_ms = latency_ms
        self.latencies_ms.append(latency_ms)

    def snapshot(self) -> Dict[str, Any]:
        """Generate a summary snapshot of collected operational metrics."""
        average = statistics.mean(self.latencies_ms) if self.latencies_ms else None
        p95 = None
        if len(self.latencies_ms) >= 20:
            latencies = sorted(self.latencies_ms)
            p95 = latencies[int(0.95 * (len(latencies) - 1))]
        return {
            "total_requests": self.total_requests,
            "success_requests": self.success_requests,
            "failed_requests": self.failed_requests,
            "last_latency_ms": self.last_latency_ms,
            "avg_latency_ms": average,
            "p95_latency_ms": p95,
        }
