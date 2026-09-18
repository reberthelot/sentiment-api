"""DTU Sentiment Analysis API package.

This package implements the requirements for the DTU NLP & LLM course assignment:
- REST-based web service built with FastAPI running on port 8000.
- Sentiment scoring using the LabMT centered happiness lexicon (`word_sentiment.csv`).
- Endpoints:
    - `POST /v1/sentiment`: Text sentiment scoring clipped to [-5, 5] with labels.
    - `POST /api/score`: Client scoring proxy with error diagnostics.
    - `POST /api/batch`: Batch evaluation over course evaluation benchmark dataset.
    - `GET /api/metrics`: Operational request and latency metrics.
    - `GET /`: Interactive web frontend interface.
"""

__version__ = "1.0.0"
