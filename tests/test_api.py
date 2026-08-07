from fastapi.testclient import TestClient

from app.main import app
from core.config import settings
from model.chat_request import ChatRequest
from tools.web_search import WebResult

client = TestClient(app)


def ask(message: str):
    return client.post("/chat", json={"message": message, "user_id": "cliente1988"})


def test_get_classica_vs_smart():
    body = ask("What's the difference between the Get Clássica and the Get Smart?").json()
    assert body["agent"] == "knowledge"
    assert "aplicativos de gestão" in body["answer"]
    assert body["sources"]


def test_best_rate_answer_is_helpful_and_links_official_site():
    body = ask("Qual a melhor taxa da Getnet?").json()
    assert body["agent"] == "knowledge"
    assert "funcionalidades digitais" in body["answer"]
    assert "conferir os detalhes" in body["answer"]
    assert body["sources"] == ["https://site.getnet.com.br/"]


def test_same_day_payment_answer_starts_with_no_and_explains_deadlines():
    body = ask("A Getnet paga no dia?").json()
    assert body["agent"] == "knowledge"
    assert body["answer"].startswith("Não há garantia")
    assert "até um dia corrido" in body["answer"]
    assert "2 dias úteis" in body["answer"]
    assert all(source.startswith("https://") for source in body["sources"])


def test_pix_does_not_require_specific_bank():
    body = ask("Do I need a bank account to receive my sales via Pix?").json()
    assert body["agent"] == "knowledge"
    assert "Não necessariamente" in body["answer"]


def test_receivables_advance():
    body = ask("How does receivables advance (antecipação) work with Getnet?").json()
    assert "R$ 50" in body["answer"]


def test_payment_link_on_whatsapp():
    body = ask("Can I sell through WhatsApp using the Payment Link?").json()
    assert body["agent"] == "knowledge"
    assert "WhatsApp" in body["answer"]


def test_installment_limit():
    body = ask("How many installments can I split a sale into with the crediário?").json()
    assert "12 vezes" in body["answer"]


def test_terminal_connectivity_uses_support_tools():
    body = ask("My card machine won't connect to the internet, what should I do?").json()
    assert body["agent"] == "customer_support"
    assert "terminal_diagnostics" in body["sources"]


def test_declined_transaction_uses_support():
    body = ask("My card machine is showing a transaction decline error.").json()
    assert body["agent"] == "customer_support"
    assert "emissor" in body["answer"]


def test_settlement_question_uses_customer_context():
    body = ask("When will the money from yesterday's sales be deposited?").json()
    assert body["agent"] == "customer_support"
    assert "2 dias úteis" in body["answer"]


def test_general_current_question_routes_to_web():
    from agents.router_agent import RouterAgent

    assert RouterAgent().decide("What's the euro exchange rate today?").agent == "web_search"
    assert RouterAgent().decide("Weather forecast in Porto Alegre tomorrow?").agent == "web_search"


def test_web_agent_returns_cited_result():
    from agents.web_search_agent import WebSearchAgent

    class FakeSearchTool:
        def search(self, query: str) -> WebResult:
            return WebResult("Resposta atual verificada", "https://example.com/source")

    body = WebSearchAgent(FakeSearchTool()).handle(ChatRequest(message="câmbio", user_id="x"))
    assert body["answer"] == "Resposta atual verificada"
    assert body["sources"] == ["https://example.com/source"]


def test_greeting_and_math_bonus_agents():
    assert ask("Bom dia!").json()["agent"] == "conversation"
    assert ask("Quanto é 25x4?").json()["answer"] == "O resultado é 100."


def test_validation_and_public_pages():
    assert client.post("/chat", json={"message": "", "user_id": "x"}).status_code == 422
    for path, marker in (("/", "Getnet Agent Swarm"), ("/apresentacao", "Getnet")):
        response = client.get(path)
        assert response.status_code == 200
        assert marker in response.text


def test_health_version():
    assert client.get("/health").json() == {"status": "ok", "version": "1.0.0"}


def test_protected_dashboards_redirect_to_login():
    anonymous = TestClient(app)
    assert anonymous.get("/gestao", follow_redirects=False).status_code == 303
    assert anonymous.get("/especialista", follow_redirects=False).status_code == 303
    assert anonymous.get("/api/management").status_code == 401


def test_admin_login_can_read_management_metrics():
    admin = TestClient(app)
    response = admin.post(
        "/auth/login", json={"username": "admin", "password": "getnet-demo-admin"}
    )
    assert response.status_code == 200 and response.json()["role"] == "admin"
    metrics = admin.get("/api/management").json()
    assert len(metrics["kpis"]) == 8
    assert metrics["agents"][0]["name"] == "Knowledge"


def test_specialist_sees_handoffs_and_suggested_reply_but_not_management():
    specialist = TestClient(app)
    response = specialist.post(
        "/auth/login",
        json={"username": "especialista", "password": "getnet-demo-specialist"},
    )
    assert response.status_code == 200
    assert specialist.get("/api/management").status_code == 401
    cases = specialist.get("/api/handoffs").json()
    assert cases[0]["priority"] == "Alta"
    assert "suggested_response" in cases[0]
    assert "cobrança duplicada" in cases[0]["suggested_response"]


def test_demo_offers_customer_and_attendant_paths():
    page = client.get("/demo")
    assert page.status_code == 200
    assert "Sou cliente" in page.text
    assert "Sou atendente" in page.text


def test_specialist_reply_is_persisted_in_conversation_history():
    specialist = TestClient(app)
    specialist.post(
        "/auth/login",
        json={"username": "especialista", "password": "getnet-demo-specialist"},
    )
    reply = "Resposta revisada pelo especialista para o teste."
    saved = specialist.post("/api/handoffs/GET-TEST/reply", json={"response": reply})
    assert saved.status_code == 200
    events = specialist.get("/api/history/GET-TEST").json()
    assert events[-1]["actor"] == "especialista"
    assert events[-1]["content"] == reply


def test_prompts_define_role_and_output():
    for name in (
        "router", "conversation", "utility", "knowledge", "web_search", "customer_support"
    ):
        text = (settings.project_root / "prompts" / f"{name}.md").read_text(encoding="utf-8")
        assert "## Role" in text and "## Output" in text
