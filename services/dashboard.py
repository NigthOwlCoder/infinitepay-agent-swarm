# ruff: noqa: E501
import copy

MANAGEMENT = {
    "period": "Últimas 24 horas",
    "updated_at": "Atualizado agora",
    "kpis": [
        {"label": "Atendimentos", "value": "1.284", "trend": "+12%", "period": "24h"},
        {"label": "Resolução automática", "value": "78%", "trend": "+4 p.p.", "period": "24h"},
        {"label": "Handoffs humanos", "value": "86", "trend": "-9%", "period": "24h"},
        {"label": "Satisfação", "value": "4,7/5", "trend": "+0,2", "period": "mês"},
        {"label": "Tempo médio", "value": "2,1 s", "trend": "-0,4 s", "period": "24h"},
        {"label": "Respostas com fonte", "value": "96%", "trend": "+3 p.p.", "period": "24h"},
        {"label": "Sucesso das ferramentas", "value": "98,6%", "trend": "+0,8 p.p.", "period": "24h"},
        {"label": "Alertas de segurança", "value": "3", "trend": "estável", "period": "mês"},
    ],
    "run_charts": [
        {"label": "Atendimentos por hora", "values": [42, 51, 47, 63, 58, 72, 68, 81, 76, 89, 84, 96]},
        {"label": "Resolução automática (%)", "values": [71, 73, 72, 75, 74, 76, 77, 76, 78, 79, 78, 80]},
        {"label": "Handoffs por hora", "values": [9, 8, 10, 7, 8, 6, 7, 5, 6, 4, 5, 4]},
    ],
    "agents": [
        {"name": "Knowledge", "volume": 482, "success": 94},
        {"name": "Customer Support", "volume": 376, "success": 83},
        {"name": "Web Search", "volume": 174, "success": 89},
        {"name": "Conversation", "volume": 156, "success": 99},
        {"name": "Utility", "volume": 96, "success": 100},
    ],
    "handoff_reasons": [
        {"label": "Baixa confiança", "count": 31},
        {"label": "Dado do cliente necessário", "count": 24},
        {"label": "Transação recusada", "count": 18},
        {"label": "Solicitação sensível", "count": 8},
        {"label": "Falha de ferramenta", "count": 5},
    ],
    "human_resolutions": [
        {"label": "Orientação enviada", "count": 39},
        {"label": "Dado confirmado com cliente", "count": 21},
        {"label": "Procedimento corrigido", "count": 14},
        {"label": "Encaminhado à operação", "count": 8},
        {"label": "Aguardando cliente", "count": 4},
    ],
    "improvements": [
        {"date": "Hoje", "title": "Prazo de recebimento mais direto", "impact": "-18% de recontato"},
        {"date": "Ontem", "title": "Nova regra para cobrança duplicada", "impact": "+7 p.p. de resolução"},
        {"date": "Há 3 dias", "title": "Fonte oficial priorizada em taxas", "impact": "96% com fonte"},
    ],
    "topics": ["Get Clássica x Smart", "Liquidação", "Pix", "Conectividade", "Antecipação"],
}

CASES = [
    {
        "id": "GET-1042", "priority": "Alta", "status": "Novo", "waiting": "06 min",
        "merchant": "cliente1988", "reason": "Transação recusada após duas tentativas",
        "summary": "Lojista informa recusa; terminal está online e sem erro técnico.",
        "history": ["Cliente: Minha venda foi recusada duas vezes.", "Support Agent: Terminal online; evitar nova cobrança duplicada."],
        "suggested_response": "Olá! Sua maquininha está online. Oriente o cliente a confirmar a compra com o banco emissor ou tentar outra forma de pagamento. Antes de repetir, confirme no histórico se nenhuma tentativa foi aprovada, evitando cobrança duplicada.",
    },
    {
        "id": "GET-1041", "priority": "Média", "status": "Em análise", "waiting": "18 min",
        "merchant": "lojista442", "reason": "Dúvida sobre prazo de liquidação",
        "summary": "Venda no crédito realizada ontem; modalidade exata não foi identificada.",
        "history": ["Cliente: Quando vou receber a venda de ontem?", "Support Agent: Prazo depende da modalidade contratada."],
        "suggested_response": "Olá! O prazo depende da modalidade escolhida. A oferta atual informa 2 dias úteis. Confirme a previsão exata no app Getnet Brasil ou no Portal Minha Conta.",
    },
    {
        "id": "GET-1039", "priority": "Baixa", "status": "Aguardando cliente", "waiting": "31 min",
        "merchant": "comercio77", "reason": "Maquininha sem conexão",
        "summary": "Cliente ainda não informou se usa Wi-Fi ou chip.",
        "history": ["Cliente: A máquina não conecta.", "Support Agent: Solicitada informação da rede."],
        "suggested_response": "Olá! Confirme se a maquininha usa Wi-Fi ou chip de dados. Enquanto isso, reinicie o equipamento e teste outra rede disponível.",
    },
]


def management_snapshot() -> dict:
    return copy.deepcopy(MANAGEMENT)


def handoff_cases() -> list[dict]:
    return copy.deepcopy(CASES)
