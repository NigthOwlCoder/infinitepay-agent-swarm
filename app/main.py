from fastapi import FastAPI
from fastapi.responses import FileResponse

from agents.router_agent import RouterAgent
from core.config import settings
from model.chat_request import ChatRequest

app = FastAPI(title=settings.app_name, version=settings.app_version)
router = RouterAgent()


def html_file(filename: str) -> FileResponse:
    """Return a versioned HTML asset from the application directory."""
    return FileResponse(settings.app_dir / filename)


@app.get("/", response_class=FileResponse, include_in_schema=False)
def home() -> FileResponse:
    return html_file("home.html")


@app.get("/apresentacao", response_class=FileResponse, include_in_schema=False)
def presentation() -> FileResponse:
    return html_file("presentation.html")


@app.get("/avaliacao", response_class=FileResponse, include_in_schema=False)
def evaluation() -> FileResponse:
    return html_file("evaluation.html")


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version}


@app.post("/chat", tags=["chat"])
def chat(request: ChatRequest) -> dict:
    return router.route(request)
