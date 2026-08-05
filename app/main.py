from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from agents.router_agent import RouterAgent
from model.chat_request import ChatRequest

app = FastAPI(title="Agent Swarm", version="1.0.0")
router = RouterAgent()

@app.get("/apresentacao", response_class=FileResponse, include_in_schema=False)
def presentation():
    return FileResponse("app/presentation.html")

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home():
    return """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>InfinitePay Agent Swarm</title>
  <style>
    :root { color-scheme: dark; --bg:#08111f; --panel:#101c2e; --line:#263750; --accent:#50e3c2; --muted:#9caec7; }
    * { box-sizing:border-box }
    body { margin:0; min-height:100vh; font-family:Inter,Segoe UI,sans-serif; background:radial-gradient(circle at top,#17304d,var(--bg) 50%); color:#f5f8ff; display:grid; place-items:center; padding:24px }
    main { width:min(920px,100%); height:min(760px,calc(100vh - 48px)); background:rgba(16,28,46,.96); border:1px solid var(--line); border-radius:24px; overflow:hidden; display:flex; flex-direction:column; box-shadow:0 24px 80px #0008 }
    header { padding:22px 26px; border-bottom:1px solid var(--line); display:flex; align-items:center; gap:14px }
    .logo { width:44px; height:44px; border-radius:14px; display:grid; place-items:center; background:var(--accent); color:#05251f; font-weight:900 }
    h1 { font-size:18px; margin:0 } header p { margin:4px 0 0; font-size:13px; color:var(--muted) }
    #messages { flex:1; overflow:auto; padding:26px; display:flex; flex-direction:column; gap:16px }
    .message { max-width:78%; padding:14px 16px; border-radius:18px; line-height:1.5; white-space:pre-wrap }
    .user { align-self:flex-end; background:#276e63; border-bottom-right-radius:5px }
    .bot { align-self:flex-start; background:#182941; border:1px solid var(--line); border-bottom-left-radius:5px }
    .meta { display:block; color:var(--accent); font-size:11px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; margin-bottom:6px }
    .sources { margin-top:8px; color:var(--muted); font-size:12px }
    form { display:flex; gap:12px; padding:18px; border-top:1px solid var(--line); background:#0c1728 }
    input { flex:1; min-width:0; border:1px solid var(--line); background:#14233a; color:white; border-radius:14px; padding:15px; font-size:15px; outline:none }
    input:focus { border-color:var(--accent) }
    button { border:0; border-radius:14px; padding:0 24px; background:var(--accent); color:#05251f; font-weight:800; cursor:pointer }
    button:disabled { opacity:.55; cursor:wait }
    footer { padding:0 20px 14px; background:#0c1728; color:var(--muted); font-size:11px; text-align:center }
    footer a { color:var(--accent) }
  </style>
</head>
<body><main>
  <header><div class="logo">AI</div><div><h1>InfinitePay Agent Swarm</h1><p>Produtos, informações atuais e suporte ao cliente</p></div></header>
  <section id="messages"><div class="message bot"><span class="meta">Assistente</span>Olá! Como posso ajudar? Experimente perguntar sobre a Maquininha Smart, Pix ou sua conta.</div></section>
  <form id="form"><input id="input" maxlength="4000" autocomplete="off" placeholder="Digite sua pergunta..." required><button id="send">Enviar</button></form>
  <footer>Agent Swarm • <a href="/docs">Documentação da API</a></footer>
</main><script>
const form=document.querySelector('#form'), input=document.querySelector('#input'), messages=document.querySelector('#messages'), send=document.querySelector('#send');
function add(text,type,agent='',sources=[]){const el=document.createElement('div'); el.className='message '+type; const meta=document.createElement('span'); meta.className='meta'; meta.textContent=agent||type; el.append(meta,document.createTextNode(text)); if(sources.length){const s=document.createElement('div'); s.className='sources'; s.textContent='Fontes: '+sources.join(' • '); el.append(s)} messages.append(el); messages.scrollTop=messages.scrollHeight}
form.addEventListener('submit',async e=>{e.preventDefault(); const message=input.value.trim(); if(!message)return; add(message,'user','Você'); input.value=''; send.disabled=true; try{const res=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,user_id:'web-user'})}); const data=await res.json(); if(!res.ok)throw Error('Não foi possível processar a solicitação.'); add(data.answer,'bot',data.agent.replaceAll('_',' '),data.sources||[])}catch(err){add(err.message,'bot','Erro')}finally{send.disabled=false; input.focus()}});
</script></body></html>"""

@app.get("/health")
def health(): return {"status": "ok"}

@app.post("/chat")
def chat(request: ChatRequest): return router.route(request)
