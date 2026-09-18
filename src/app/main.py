from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.app.config import get_settings
from src.app.routes.api import router as api_router
from src.app.routes.frontend import router as frontend_router

DESCRIPTION = """A sentiment analysis API powered by the LabMT word sentiment list.

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
negation, irony, or relationships between words."""


def create_app() -> FastAPI:
    """Create and configure the unified FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title="LabMT wordlist Sentiment API",
        description=DESCRIPTION,
        version="1.0.0",
    )

    # Mount static assets (CSS, JS)
    app.mount(
        "/static",
        StaticFiles(directory=settings.static_dir),
        name="static",
    )

    # Register decoupled route groups
    app.include_router(frontend_router, tags=["frontend"])
    app.include_router(api_router, tags=["api"])

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)

