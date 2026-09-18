import doctest
import pytest

from src.app.utils import normalization
from src.app.utils.normalization import (
    calculate_sentiment,
    score_to_label,
    tokenize,
)


def test_doctests():
    """Verify that all embedded doctests in normalization pass."""
    results = doctest.testmod(normalization)
    assert results.failed == 0, f"{results.failed} doctests failed"


def test_tokenize_basic():
    text = "Hello World! This is a test."
    expected = ["hello", "world", "this", "is", "a", "test"]
    assert tokenize(text) == expected


def test_tokenize_contractions():
    text = "Nicki's demos weren't boring."
    expected = ["nicki's", "demos", "weren't", "boring"]
    assert tokenize(text) == expected


def test_tokenize_empty_and_symbols():
    assert tokenize("12345 @#$%") == []
    assert tokenize("") == []


@pytest.mark.parametrize(
    "score, expected_label",
    [
        (-5.0, "really negative"),
        (-3.0, "really negative"),
        (-2.99, "negative"),
        (-0.01, "negative"),
        (0.0, "neutral"),
        (0.01, "positive"),
        (2.99, "positive"),
        (3.0, "really positive"),
        (5.0, "really positive"),
    ],
)
def test_score_to_label(score: float, expected_label: str):
    assert score_to_label(score) == expected_label


def test_calculate_sentiment_with_mock_lexicon():
    mock_score_map = {
        "great": 3.2,
        "good": 1.5,
        "terrible": -4.0,
    }

    # All recognized words
    score, label = calculate_sentiment("Great good", mock_score_map)
    assert pytest.approx(score, 0.01) == (3.2 + 1.5) / 2
    assert label == "positive"

    # Single negative word
    score, label = calculate_sentiment("This is terrible!", mock_score_map)
    assert score == -4.0
    assert label == "really negative"

    # Unknown words only -> 0.0, neutral
    score, label = calculate_sentiment("Unknown words only", mock_score_map)
    assert score == 0.0
    assert label == "neutral"


def test_calculate_sentiment_clipping():
    mock_score_map = {
        "fantastic": 10.0,
        "abysmal": -10.0,
    }
    score_pos, label_pos = calculate_sentiment("fantastic", mock_score_map)
    assert score_pos == 5.0
    assert label_pos == "really positive"

    score_neg, label_neg = calculate_sentiment("abysmal", mock_score_map)
    assert score_neg == -5.0
    assert label_neg == "really negative"
