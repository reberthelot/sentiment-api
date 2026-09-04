from fastapi import FastAPI
import csv
from pathlib import Path
import re

from pydantic import BaseModel, Field


WORDLIST_FILE = Path(__file__).parent / "word_sentiment.csv"


def load_score_map() -> dict[str, float]:
    with WORDLIST_FILE.open(newline="", encoding="utf-8") as wordlist:
        return {
            row["word"]: float(row["happiness_score_centered"])
            for row in csv.DictReader(wordlist)
            if row["word"] and row["happiness_score_centered"]
        }


score_map = load_score_map()

app = FastAPI(
    title="LabMT wordlist Sentiment API",
    description="""A sentiment analysis API powered by the LabMT word sentiment list.

The service calculates a score by converting the input text to lowercase,
extracting word tokens, and looking up each recognized word in
`word_sentiment.csv`. The corresponding `happiness_score_centered` values are
averaged. Words that are not in the list do not contribute to the average; if
no words are recognized, the score is `0.0`.

The result is clipped to the range `-5` to `5` and mapped to a label. Scores
less than or equal to `-3` are `really negative`, scores below `0` are
`negative`, `0` is `neutral`, scores below `3` are `positive`, and scores
greater than or equal to `3` are `really positive`.

This lightweight dictionary-based approach does not account for context,
negation, irony, or relationships between words.""",
    version="1.0.0"
)



class TextInput(BaseModel):
    text: str = Field(..., description="The text to analyze for sentiment.")


class SentimentResponse(BaseModel):
    score: float
    label: str

@app.post("/v1/sentiment", response_model=SentimentResponse)
def sentiment_calculation(payload: TextInput) -> SentimentResponse:
    """Calculate sentiment from the LabMT wordlist.

    The returned score is the mean of the centered happiness scores for the
    recognized words, clipped to `[-5, 5]`, together with its corresponding
    sentiment label.
    """
    tokens = re.findall(r"[a-z]+(?:'[a-z]+)?", payload.text.lower())
    scores = [
        score_map[token]
        for token in tokens
        if token in score_map
    ]
    score = sum(scores) / len(scores) if scores else 0.0
    score = min(5, max(-5, score))
    # Determine the label based on the score
    if score <= -3:
        label = "really negative"
    elif score < 0:
        label = "negative"
    elif score == 0:
        label = "neutral"
    elif score < 3:
        label = "positive"
    else:
        label = "really positive"
    return SentimentResponse(score=score, label=label)
