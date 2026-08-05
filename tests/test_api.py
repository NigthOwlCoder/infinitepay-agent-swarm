from fastapi.testclient import TestClient

from app.main import app
from core.config import settings
from model.chat_request import ChatRequest
from tools.web_search import WebResult

client = TestClient(app)


def ask(message: str):
    return client.post(
        "/chat",
        json={"message": message, "user_id": "client789"},
    )

def test_product_question_uses_knowledge():
    body = ask("What is the cost of the Maquininha Smart?").json()
    assert body["agent"] == "knowledge" and body["sources"]

def test_fee_question_returns_specific_example():
    body = ask("Pode me dar um exemplo de tarifa no débito e crédito?").json()
    assert "1,37%" in body["answer"]
    assert "3,15%" in body["answer"]
    assert body["sources"] == ["https://www.infinitepay.io/taxas"]

def test_english_fee_question_is_understood():
    body = ask("What are the fees for debit and credit card transactions?").json()
    assert "Pix grátis" in body["answer"]

def test_machine_has_no_rent_or_monthly_fee():
    body = ask("Preciso pagar aluguel pela maquininha?").json()
    assert body["answer"].startswith("Não.")
    assert "mensalidade" in body["answer"]

def test_current_question_uses_search():
    from agents.router_agent import RouterAgent

    decision = RouterAgent().decide("Quando foi o último jogo do Palmeiras?")
    assert decision.agent == "web_search"


def test_unseen_general_questions_route_to_web_without_keyword_rules():
    from agents.router_agent import RouterAgent

    router = RouterAgent()
    questions = (
        "Quem ganhou a Copa do Mundo?",
        "Qual a previsão meteorológica para amanhã?",
        "Quem venceu a partida?",
        "Qual o valor do câmbio entre real e dólar?",
    )
    assert all(router.decide(question).agent == "web_search" for question in questions)


def test_web_agent_returns_answer_and_source_from_tool():
    from agents.web_search_agent import WebSearchAgent

    class FakeSearchTool:
        def search(self, query: str) -> WebResult:
            return WebResult(
                answer="Resposta verificada",
                source="https://example.com/source",
            )

    agent = WebSearchAgent(search_tool=FakeSearchTool())
    request = ChatRequest(message="Pergunta geral inédita", user_id="client789")
    body = agent.handle(request)
    assert body["answer"] == "Resposta verificada"
    assert body["sources"] == ["https://example.com/source"]

def test_today_question_returns_server_date():
    body = ask("Que dia é hoje?").json()
    assert body["agent"] == "web_search"
    assert body["answer"].startswith("Hoje é")
    assert "America/Sao_Paulo" in body["sources"][0]

def test_account_question_uses_support():
    body = ask("Why am I not able to make transfers?").json()
    assert body["agent"] == "customer_support" and "customer_account" in body["sources"]

def test_validation():
    response = client.post("/chat", json={"message": "", "user_id": "x"})
    assert response.status_code == 422

def test_greeting_uses_conversation_agent():
    body = ask("Bom dia!").json()
    assert body["agent"] == "conversation"
    assert body["answer"].startswith("Bom dia! Posso te ajudar?")
    assert "Maquininha Smart" in body["answer"]
    assert body["sources"] == []


def test_arithmetic_uses_utility_agent():
    body = ask("Quanto é 2x3?").json()
    assert body["agent"] == "utility"
    assert body["answer"] == "O resultado é 6."


def test_insult_receives_constructive_response():
    body = ask("Você é inútil").json()
    assert body["agent"] == "conversation"
    assert body["answer"].startswith("Desculpe. Vou procurar aprender e melhorar.")


def test_public_pages_are_available():
    for path, marker in (
        ("/", "InfinitePay Agent Swarm"),
        ("/apresentacao", "Apresentação Executiva"),
        ("/avaliacao", "Evidências técnicas"),
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert marker in response.text


def test_health_exposes_version():
    body = client.get("/health").json()
    assert body == {"status": "ok", "version": "1.2.0"}


def test_agent_prompts_define_capabilities_and_output_contracts():
    for name in ("router", "knowledge", "web_search", "customer_support"):
        prompt = (settings.project_root / "prompts" / f"{name}.md").read_text(
            encoding="utf-8"
        )
        assert "## Role" in prompt
        assert "## Output" in prompt
