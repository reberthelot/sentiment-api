import json
import statistics
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from dataset import DATASET
from frontend_service import Metrics, call_external_service

DEFAULT_SERVICE_URL = "http://localhost:8000"
HTML_FILE = Path(__file__).parent / "template" / "index.html"
metrics = Metrics()


class ScoreRequest(BaseModel):
    """Request payload for scoring a single text.

    Parameters
    ----------
    service_url : str
        Base URL for the external sentiment service, e.g. "http://localhost:8000".
        The app will call "{service_url}/v1/sentiment".
    text : str
        Input text to score.

    Notes
    -----
    We route external calls via the backend to avoid CORS issues and keep JS simple.
    """

    service_url: str = Field(..., description="Base URL of external service, e.g. http://localhost:8000")
    text: str = Field(..., min_length=1, description="Text to score")
class BatchRequest(BaseModel):
    """Request payload for batch evaluation on a dataset.

    Parameters
    ----------
    service_url : str
        Base URL for the external sentiment service.
    dataset : list
        List of [text, gold_label] pairs.

    Examples
    --------
    >>> req = BatchRequest(service_url="http://localhost:8000", dataset=[["Good course", "positive"]])
    >>> req.dataset[0][1]
    'positive'
    """

    service_url: str
    dataset: List[List[str]] = Field(..., description='List like [["text", "positive"], ...]')


app = FastAPI(title="DTU Sentiment Demo Frontend", version="1.0.0")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    dataset_js = json.dumps(DATASET, ensure_ascii=False)
    template = HTML_FILE.read_text(encoding="utf-8")

    return template.replace("__DATASET_JSON__", dataset_js).replace(
        "__DEFAULT_SERVICE_URL__", DEFAULT_SERVICE_URL
    )

@app.post("/api/score")
async def api_score(req: ScoreRequest) -> JSONResponse:
    """Score a single text via the external service."""
    score, info, label = await call_external_service(str(req.service_url), req.text, metrics)
    if score is None:
        # Pedagogic error messages come from call_external_service()
        return JSONResponse(status_code=502, content={"detail": info.get("error", "Unknown error.")})

    payload: Dict[str, Any] = {
        "score": score,
        "label": label,
        "latency_ms": info.get("latency_ms", None),
    }
    if "warning" in info:
        payload["warning"] = info["warning"]
    return JSONResponse(content=payload)


@app.post("/api/batch")
async def api_batch(req: BatchRequest) -> JSONResponse:
    """Run a batch evaluation on a [text, gold_label] dataset.

    Notes
    -----
    This runs requests sequentially for clarity (teaching). The student-built
    service should still be capable of handling concurrent clients; you can
    trivially parallelize this later if desired.
    """
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
            # Count as incorrect but keep going; useful for demos.
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


@app.get("/api/metrics")
def api_metrics() -> JSONResponse:
    """Return a snapshot of in-memory metrics."""
    return JSONResponse(content=metrics.snapshot())
