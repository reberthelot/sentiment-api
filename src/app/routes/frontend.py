import json
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.app.config import get_settings
from src.app.utils.dataset import DATASET

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index() -> str:
    """Render the semantic HTML5 frontend demo page with embedded dataset and default service URL."""
    settings = get_settings()
    template_path = settings.templates_dir / "index.html"
    dataset_js = json.dumps(DATASET, ensure_ascii=False)
    template = template_path.read_text(encoding="utf-8")

    return template.replace("__DATASET_JSON__", dataset_js).replace(
        "__DEFAULT_SERVICE_URL__", settings.default_service_url
    )

