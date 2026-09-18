import csv
import re
from pathlib import Path
from typing import Dict, List, Tuple


def load_score_map(wordlist_path: Path) -> Dict[str, float]:
    """Load centered happiness scores from a LabMT CSV file.

    Parameters
    ----------
    wordlist_path : Path
        Path to the CSV file containing 'word' and 'happiness_score_centered'.

    Returns
    -------
    Dict[str, float]
        Dictionary mapping lowercased words to centered happiness scores.
    """
    with wordlist_path.open(newline="", encoding="utf-8") as wordlist:
        return {
            row["word"]: float(row["happiness_score_centered"])
            for row in csv.DictReader(wordlist)
            if row.get("word") and row.get("happiness_score_centered")
        }


def tokenize(text: str) -> List[str]:
    """Tokenize input text into lowercased alphabetic tokens, including contractions.

    Examples
    --------
    >>> tokenize("Great course, learned a lot!")
    ['great', 'course', 'learned', 'a', 'lot']
    >>> tokenize("Nicki's demos were sharp.")
    [\"nicki's\", 'demos', 'were', 'sharp']
    >>> tokenize("123 -- !!")
    []
    """
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())


def score_to_label(score: float) -> str:
    """Map a numerical sentiment score in [-5, 5] to a categorical label.

    Examples
    --------
    >>> score_to_label(-4.0)
    'really negative'
    >>> score_to_label(-1.5)
    'negative'
    >>> score_to_label(0.0)
    'neutral'
    >>> score_to_label(2.2)
    'positive'
    >>> score_to_label(4.5)
    'really positive'
    """
    if score <= -3:
        return "really negative"
    if score < 0:
        return "negative"
    if score == 0:
        return "neutral"
    if score < 3:
        return "positive"
    return "really positive"


def calculate_sentiment(text: str, score_map: Dict[str, float]) -> Tuple[float, str]:
    """Calculate the sentiment score and categorical label for a text using LabMT lexicon.

    The score is the mean of centered happiness scores of all recognized words,
    clipped to [-5, 5]. If no recognized words are found, the score is 0.0.

    Examples
    --------
    >>> test_map = {"great": 2.5, "awful": -3.2}
    >>> calculate_sentiment("Great course!", test_map)
    (2.5, 'positive')
    >>> calculate_sentiment("Unknown words here", test_map)
    (0.0, 'neutral')
    """
    tokens = tokenize(text)
    scores = [score_map[token] for token in tokens if token in score_map]
    raw_score = sum(scores) / len(scores) if scores else 0.0
    score = min(5.0, max(-5.0, raw_score))
    label = score_to_label(score)
    return score, label
