import statistics
from typing import Any, Dict, List

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.app.config import get_settings
from src.app.models import BatchRequest, ScoreRequest, SentimentResponse, TextInput
from src.app.services.sentiment_client import call_external_service
from src.app.utils.metrics import Metrics
from src.app.utils.normalization import calculate_sentiment, load_score_map

router = APIRouter()
metrics = Metrics()
_score_map: Dict[str, float] = {}


def get_or_load_score_map() -> Dict[str, float]:
    """Retrieve or lazily initialize the LabMT score map."""
    global _score_map
    if not _score_map:
        settings = get_settings()
        _score_map = load_score_map(settings.wordlist_file)
    return _score_map


@router.post("/v1/sentiment", response_model=SentimentResponse)
def sentiment_calculation(payload: TextInput) -> SentimentResponse:
    """Calculate sentiment from the LabMT wordlist.

    The returned score is the mean of the centered happiness scores for the
    recognized words, clipped to `[-5, 5]`, together with its corresponding
    sentiment label.
    """
    score_map = get_or_load_score_map()
    score, label = calculate_sentiment(payload.text, score_map)
    return SentimentResponse(score=score, label=label)


@router.post("/api/score")
async def api_score(req: ScoreRequest) -> JSONResponse:
    """Score a single text via the external service with diagnostic info."""
    score, info, label = await call_external_service(str(req.service_url), req.text, metrics)
    if score is None:
        return JSONResponse(status_code=502, content={"detail": info.get("error", "Unknown error.")})

    payload: Dict[str, Any] = {
        "score": score,
        "label": label,
        "latency_ms": info.get("latency_ms", None),
    }
    if "warning" in info:
        payload["warning"] = info["warning"]
    return JSONResponse(content=payload)


@router.post("/api/batch")
async def api_batch(req: BatchRequest) -> JSONResponse:
    """Run a batch evaluation on a [text, gold_label] dataset."""
    rows_out: List[Dict[str, Any]] = []
    latencies: List[float] = []
    correct = 0
    n = 0

    for item in req.dataset:
        if not (isinstance(item, list) and len(item) == 2):
            return JSONResponse(
                status_code=400,
                content={"detail": "Dataset must contain [text, gold_label] rows."},
            )

        text, gold = item[0], item[1]
        if gold not in ("positive", "neutral", "negative"):
            return JSONResponse(
                status_code=400,
                content={"detail": f"Gold label must be positive/neutral/negative. Got: {gold!r}"},
            )

        score, info, label = await call_external_service(
            str(req.service_url), text, metrics
        )
        latency_ms = float(info.get("latency_ms", 0.0))
        latencies.append(latency_ms)

        if score is None:
            rows_out.append(
                {
                    "text": text,
                    "gold": gold,
                    "score": None,
                    "pred": None,
                    "ok": False,
                    "latency_ms": latency_ms,
                    "error": info.get("error"),
                }
            )
            n += 1
            continue

        pred = label
        gold_polarity = 1 if gold == "positive" else -1 if gold == "negative" else 0
        predicted_polarity = (
            1 if pred in ("positive", "really positive")
            else -1 if pred in ("negative", "really negative")
            else 0
        )
        ok = predicted_polarity == gold_polarity
        correct += int(ok)
        n += 1
        rows_out.append(
            {
                "text": text,
                "gold": gold,
                "score": score,
                "pred": pred,
                "ok": ok,
                "latency_ms": latency_ms,
            }
        )

    accuracy = (correct / n) if n else 0.0
    avg_latency = statistics.mean(latencies) if latencies else 0.0

    return JSONResponse(
        content={
            "n": n,
            "correct": correct,
            "accuracy": accuracy,
            "avg_latency_ms": avg_latency,
            "rows": rows_out,
        }
    )


@router.get("/api/metrics")
def api_metrics() -> JSONResponse:
    """Return a snapshot of in-memory operational metrics."""
    return JSONResponse(content=metrics.snapshot())

