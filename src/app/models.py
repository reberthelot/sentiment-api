from typing import List
from pydantic import BaseModel, Field


class TextInput(BaseModel):
    """Input payload for sentiment analysis."""

    text: str = Field(..., description="The text to analyze for sentiment.")


class SentimentResponse(BaseModel):
    """Sentiment scoring response payload."""

    score: float = Field(..., description="Sentiment score clipped to the [-5, 5] range.")
    label: str = Field(..., description="Categorical sentiment label.")


class ScoreRequest(BaseModel):
    """Request payload for proxy scoring a single text via an external service."""

    service_url: str = Field(..., description="Base URL of external service, e.g. http://localhost:8000")
    text: str = Field(..., min_length=1, description="Text to score")


class BatchRequest(BaseModel):
    """Request payload for batch evaluation on a dataset."""

    service_url: str = Field(..., description="Base URL for the external sentiment service.")
    dataset: List[List[str]] = Field(..., description='List like [["text", "positive"], ...]')
