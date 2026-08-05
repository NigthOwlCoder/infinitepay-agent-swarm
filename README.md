# Agent Swarm

API multiagente para perguntas sobre produtos InfinitePay, criada para o coding challenge.

## Arquitetura

O `RouterAgent` coordena cinco agentes por chamadas diretas:

1. `KnowledgeAgent`: responde produtos com o índice RAG local.
2. `WebSearchAgent`: trata perguntas gerais/atuais sem inventar fatos e fornece uma busca.
3. `CustomerSupportAgent`: usa `get_account_status` e `get_recent_activity` e pode sinalizar atendimento humano.
4. `ConversationAgent`: trata saudações e feedback sem consultar o RAG.
5. `UtilityAgent`: resolve aritmética com uma árvore sintática segura, sem executar código arbitrário.

Fluxo: `POST /chat -> RouterAgent -> agente especialista -> JSON`. A decisão e a justificativa são
incluídas para observabilidade. Depois de tratar saudações, suporte e cálculos, o Router consulta a
capacidade do RAG: perguntas fundamentáveis na base seguem para Knowledge; qualquer pergunta fora
do corpus segue automaticamente para Web Search. Assim, temas gerais inéditos não dependem de uma
lista de palavras cadastradas. As políticas são explícitas e testáveis: conhecimento só usa contexto
recuperado, busca não fabrica fatos atuais e suporte não expõe segredos.

## RAG

Na inicialização, os `.txt` de `data/` são divididos em parágrafos, tokenizados e indexados em memória. A recuperação usa BM25 e retorna até três trechos com caminhos como citações.

Em produção, um job deve baixar e limpar as páginas indicadas no desafio (`infinitepay.io`, `/maquininha`, `/maquininha-celular`, `/tap-to-pay`, `/pdv`, `/receba-na-hora`, `/gestao-de-cobranca-2`, `/link-de-pagamento`, `/loja-online`, `/boleto`, `/conta-digital`, `/pix`, `/emprestimo`, `/cartao` e `/rendimento`), versionar os documentos e reconstruir o índice. Essa separação torna testes independentes da rede e permite revisão editorial.

## Prompts e políticas dos agentes

Os prompts de produção estão versionados em `prompts/`. Cada um declara papel, escopo, ferramentas,
regras de grounding e segurança, condições de escalonamento e contrato de saída. A implementação
demonstrativa aplica essas políticas de forma determinística, tornando o roteamento e os testes
reprodutíveis; os mesmos prompts podem ser conectados a um LLM sem alterar o contrato HTTP.

## Executar

Requer Python 3.12+.

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/uvicorn app.main:app --reload
```

Interface de chat: `http://localhost:8000/`. Apresentação executiva: `http://localhost:8000/apresentacao`. Painel de avaliação técnica: `http://localhost:8000/avaliacao`. Swagger: `http://localhost:8000/docs`.

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

Para instalar as ferramentas de desenvolvimento e verificar estilo, imports e erros comuns:

```bash
pip install -r requirements-dev.txt
ruff check .
pytest
```

A suíte cobre roteamento de produto, pergunta atual, suporte com ferramentas e validação. Em produção, acrescentaria contratos de provedores, avaliação offline do RAG, prompt injection, carga, timeouts e integração.

## Decisões e evolução

- Chamadas diretas deixam a comunicação clara, rápida e testável; as fronteiras podem migrar para filas/eventos sem mudar o contrato HTTP.
- Todos os agentes implementam o mesmo contrato estrutural (`Agent`) e podem ser injetados no Router em testes ou integrações.
- Caminhos e metadados da aplicação ficam centralizados em `core/config.py`, evitando dependência do diretório de execução.
- A interface, a apresentação e a página de avaliação são arquivos independentes da API.
- Nenhuma chave de LLM é obrigatória: a execução é reprodutível e dados de clientes não saem do serviço.
- Guardrails: limites de entrada, respostas fundamentadas, nenhuma credencial em texto e `needs_human`. Em produção, a flag deve abrir um ticket autenticado.
- As ferramentas de suporte são mocks intencionais; devem virar APIs autorizadas, auditadas e com minimização de dados.

Ferramentas de assistência de código foram usadas para estruturar arquitetura, componentes e testes; as decisões permanecem verificáveis no código e na suíte.
