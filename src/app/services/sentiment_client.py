import time
from typing import Any, Dict, Optional, Tuple

import httpx

from src.app.config import get_settings
from src.app.utils.metrics import Metrics


def _error_info(message: str, endpoint: str, latency_ms: float) -> Dict[str, Any]:
    """Format diagnostic error info dictionary."""
    return {"latency_ms": latency_ms, "error": message, "endpoint": endpoint}


async def call_external_service(
    service_url: str,
    text: str,
    metrics: Metrics,
    timeout_seconds: Optional[float] = None,
) -> Tuple[Optional[float], Dict[str, Any], Optional[str]]:
    """Asynchronously score a text via an external sentiment service with pedagogic error reporting.

    Parameters
    ----------
    service_url : str
        Base URL of the external service.
    text : str
        Text string to analyze.
    metrics : Metrics
        Metrics tracker instance.
    timeout_seconds : Optional[float]
        HTTP timeout in seconds (defaults to Settings.request_timeout_seconds).

    Returns
    -------
    Tuple[Optional[float], Dict[str, Any], Optional[str]]
        A tuple of (score, diagnostic_dict, label).
    """
    settings = get_settings()
    timeout = timeout_seconds or settings.request_timeout_seconds
    endpoint = service_url.rstrip("/") + "/v1/sentiment"
    started = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
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
        label = data.get("label", "")
        metrics.record(True, latency_ms)
        result: Dict[str, Any] = {"latency_ms": latency_ms, "endpoint": endpoint}
        if not -5 <= score <= 5:
            result["warning"] = f"Score {score} is outside expected range [-5, 5]."
        return score, result, label

    except httpx.TimeoutException:
        latency_ms = (time.perf_counter() - started) * 1000
        metrics.record(False, latency_ms)
        return None, _error_info(
            f"Timeout after {timeout:.1f}s while calling the external service. "
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

