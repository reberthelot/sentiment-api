from src.app.utils.metrics import Metrics


def test_metrics_initial_state():
    metrics = Metrics()
    snap = metrics.snapshot()
    assert snap["total_requests"] == 0
    assert snap["success_requests"] == 0
    assert snap["failed_requests"] == 0
    assert snap["last_latency_ms"] is None
    assert snap["avg_latency_ms"] is None
    assert snap["p95_latency_ms"] is None


def test_metrics_recording():
    metrics = Metrics()
    metrics.record(ok=True, latency_ms=10.0)
    metrics.record(ok=False, latency_ms=20.0)

    snap = metrics.snapshot()
    assert snap["total_requests"] == 2
    assert snap["success_requests"] == 1
    assert snap["failed_requests"] == 1
    assert snap["last_latency_ms"] == 20.0
    assert snap["avg_latency_ms"] == 15.0
    assert snap["p95_latency_ms"] is None  # Less than 20 records


def test_metrics_p95_calculation():
    metrics = Metrics()
    for latency in range(1, 101):
        metrics.record(ok=True, latency_ms=float(latency))

    snap = metrics.snapshot()
    assert snap["total_requests"] == 100
    assert snap["success_requests"] == 100
    assert snap["avg_latency_ms"] == 50.5
    # 95th percentile of 1..100
    assert snap["p95_latency_ms"] == 95.0

