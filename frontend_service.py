import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import httpx


REQUEST_TIMEOUT_SECONDS = 4.0


@dataclass
class Metrics:
    total_requests: int = 0
    success_requests: int = 0
    failed_requests: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    last_latency_ms: Optional[float] = None

    def record(self, ok: bool, latency_ms: float) -> None:
        self.total_requests += 1
        self.success_requests += int(ok)
        self.failed_requests += int(not ok)
        self.last_latency_ms = latency_ms
        self.latencies_ms.append(latency_ms)

    def snapshot(self) -> Dict[str, Any]:
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


def _error_info(message: str, endpoint: str, latency_ms: float) -> Dict[str, Any]:
    return {"latency_ms": latency_ms, "error": message, "endpoint": endpoint}


async def call_external_service(
    service_url: str, text: str, metrics: Metrics
) -> Tuple[Optional[float], Dict[str, Any], Optional[str]]:
    endpoint = service_url.rstrip("/") + "/v1/sentiment"
    started = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(endpoint, json={"text": text})
        latency_ms = (time.perf_counter() - started) * 1000

        if response.status_code != 200:
            metrics.record(False, latency_ms)
            return None, _error_info(
                f"External service responded with HTTP {response.status_code}. "
                f"Expected 200. Response body (truncated): {response.text[:200]!r}",
                endpoint,
                latency_ms, 
            ), None

        data = response.json()
        if "score" not in data:
            metrics.record(False, latency_ms)
            return None, _error_info(
                "External service returned JSON without the required field 'score'. "
                f"Got keys: {list(data.keys())!r}",
                endpoint,
                latency_ms,
            ), None

        score = float(data["score"])
        label = data["label"]
        metrics.record(True, latency_ms)
        result: Dict[str, Any] = {"latency_ms": latency_ms, "endpoint": endpoint}
        if not -5 <= score <= 5:
            result["warning"] = f"Score {score} is outside expected range [-5, 5]."
        return score, result, label

    except httpx.TimeoutException:
        latency_ms = (time.perf_counter() - started) * 1000
        metrics.record(False, latency_ms)
        return None, _error_info(
            f"Timeout after {REQUEST_TIMEOUT_SECONDS:.1f}s while calling the external service. "
            "Check that the service is running and exposes /v1/sentiment.",
            endpoint,
            latency_ms,
        ), None
    except httpx.RequestError as error:
        latency_ms = (time.perf_counter() - started) * 1000
        metrics.record(False, latency_ms)
        return None, _error_info(
            "Could not reach the external service. Check the base URL and whether the service is running. "
            f"Details: {type(error).__name__}: {error}",
            endpoint,
            latency_ms,
        ), None
    except (ValueError, TypeError, KeyError) as error:
        latency_ms = (time.perf_counter() - started) * 1000
        metrics.record(False, latency_ms)
        return None, _error_info(
            f"Could not parse the external service response. Details: {type(error).__name__}: {error}",
            endpoint,
            latency_ms,
        ), None
