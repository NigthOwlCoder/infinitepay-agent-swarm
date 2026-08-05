# Agent Swarm

API multiagente para perguntas sobre produtos InfinitePay, criada para o coding challenge.

## Arquitetura

O `RouterAgent` coordena três agentes por chamadas diretas:

1. `KnowledgeAgent`: responde produtos com o índice RAG local.
2. `WebSearchAgent`: trata perguntas gerais/atuais sem inventar fatos e fornece uma busca.
3. `CustomerSupportAgent`: usa `get_account_status` e `get_recent_activity` e pode sinalizar atendimento humano.

Fluxo: `POST /chat -> RouterAgent -> agente especialista -> JSON`. A decisão e a justificativa são incluídas para observabilidade. As políticas são explícitas e testáveis: conhecimento só usa contexto recuperado, busca não fabrica fatos atuais e suporte não expõe segredos.

## RAG

Na inicialização, os `.txt` de `data/` são divididos em parágrafos, tokenizados e indexados em memória. A recuperação usa BM25 e retorna até três trechos com caminhos como citações.

Em produção, um job deve baixar e limpar as páginas indicadas no desafio (`infinitepay.io`, `/maquininha`, `/maquininha-celular`, `/tap-to-pay`, `/pdv`, `/receba-na-hora`, `/gestao-de-cobranca-2`, `/link-de-pagamento`, `/loja-online`, `/boleto`, `/conta-digital`, `/pix`, `/emprestimo`, `/cartao` e `/rendimento`), versionar os documentos e reconstruir o índice. Essa separação torna testes independentes da rede e permite revisão editorial.

## Executar

Requer Python 3.12+.

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/uvicorn app.main:app --reload
```

Interface de chat: `http://localhost:8000/`. Apresentação executiva: `http://localhost:8000/apresentacao`. Swagger: `http://localhost:8000/docs`.

```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message":"What are the fees of the Maquininha Smart?","user_id":"client789"}'
```

## Docker

```bash
docker build -t agent-swarm .
docker run --rm -p 8000:8000 agent-swarm
```

## Testes

```bash
pytest -q
```

A suíte cobre roteamento de produto, pergunta atual, suporte com ferramentas e validação. Em produção, acrescentaria contratos de provedores, avaliação offline do RAG, prompt injection, carga, timeouts e integração.

## Decisões e evolução

- Chamadas diretas deixam a comunicação clara, rápida e testável; as fronteiras podem migrar para filas/eventos sem mudar o contrato HTTP.
- Nenhuma chave de LLM é obrigatória: a execução é reprodutível e dados de clientes não saem do serviço.
- Guardrails: limites de entrada, respostas fundamentadas, nenhuma credencial em texto e `needs_human`. Em produção, a flag deve abrir um ticket autenticado.
- As ferramentas de suporte são mocks intencionais; devem virar APIs autorizadas, auditadas e com minimização de dados.

Ferramentas de assistência de código foram usadas para estruturar arquitetura, componentes e testes; as decisões permanecem verificáveis no código e na suíte.
