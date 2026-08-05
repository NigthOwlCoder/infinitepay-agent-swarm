from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
def ask(message): return client.post("/chat", json={"message": message, "user_id": "client789"})

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
    assert ask("Quando foi o último jogo do Palmeiras?").json()["agent"] == "web_search"

def test_account_question_uses_support():
    body = ask("Why am I not able to make transfers?").json()
    assert body["agent"] == "customer_support" and "customer_account" in body["sources"]

def test_validation():
    assert client.post("/chat", json={"message": "", "user_id": "x"}).status_code == 422
