from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

from agents.router_agent import RouterAgent
from core.config import settings
from model.chat_request import ChatRequest
from services.auth import AuthService, SessionUser
from services.dashboard import handoff_cases, management_snapshot
from services.history import HistoryService

app = FastAPI(title=settings.app_name, version=settings.app_version)
router = RouterAgent()
auth = AuthService()
history = HistoryService()


class LoginRequest(BaseModel):
    username: str
    password: str


class SpecialistReply(BaseModel):
    response: str


def current_user(request: Request) -> SessionUser | None:
    return auth.user(request.cookies.get("getnet_session"))


def require_role(request: Request, *roles: str) -> SessionUser:
    user = current_user(request)
    if not user or user.role not in roles:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    return user


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


@app.get("/demo", response_class=FileResponse, include_in_schema=False)
def demo_page() -> FileResponse:
    return html_file("demo.html")


@app.get("/login", response_class=FileResponse, include_in_schema=False)
def login_page() -> FileResponse:
    return html_file("login.html")


@app.get("/gestao", include_in_schema=False, response_model=None)
def management_page(request: Request) -> FileResponse | RedirectResponse:
    user = current_user(request)
    if not user or user.role != "admin":
        return RedirectResponse("/login?next=/gestao", status_code=303)
    return html_file("management.html")


@app.get("/especialista", include_in_schema=False, response_model=None)
def specialist_page(request: Request) -> FileResponse | RedirectResponse:
    if not current_user(request):
        return RedirectResponse("/login?next=/especialista", status_code=303)
    return html_file("specialist.html")


@app.post("/auth/login", tags=["authentication"])
def login(credentials: LoginRequest, response: Response) -> dict[str, str]:
    token = auth.login(credentials.username, credentials.password)
    if not token:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    user = auth.user(token)
    response.set_cookie(
        "getnet_session", token, httponly=True, samesite="strict", secure=False, max_age=28800
    )
    return {"status": "ok", "role": user.role if user else ""}


@app.post("/auth/logout", tags=["authentication"])
def logout(request: Request, response: Response) -> dict[str, str]:
    auth.logout(request.cookies.get("getnet_session"))
    response.delete_cookie("getnet_session")
    return {"status": "ok"}


@app.get("/api/management", tags=["management"])
def management_data(request: Request) -> dict:
    require_role(request, "admin")
    return management_snapshot()


@app.get("/api/handoffs", tags=["management"])
def handoff_data(request: Request) -> list[dict]:
    require_role(request, "admin", "specialist")
    return handoff_cases()


@app.get("/api/history/{conversation_id}", tags=["management"])
def conversation_history(conversation_id: str, request: Request) -> list[dict]:
    require_role(request, "admin", "specialist")
    return history.list(conversation_id)


@app.post("/api/handoffs/{case_id}/reply", tags=["management"])
def specialist_reply(case_id: str, reply: SpecialistReply, request: Request) -> dict[str, str]:
    user = require_role(request, "admin", "specialist")
    history.record(case_id, user.username, "specialist_reply", reply.response)
    return {"status": "recorded", "case_id": case_id}


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.app_version}


@app.post("/chat", tags=["chat"])
def chat(request: ChatRequest) -> dict:
    history.record(request.user_id, "customer", "message", request.message)
    result = router.route(request)
    history.record(
        request.user_id,
        result["agent"],
        "agent_response",
        result["answer"],
        {"sources": result.get("sources", []), "routing": result.get("routing", {})},
    )
    return result
