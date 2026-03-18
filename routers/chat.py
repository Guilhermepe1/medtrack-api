"""
Router do chat inteligente de saúde.
"""

from fastapi import APIRouter, Depends
from core.security import get_usuario_atual
from models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def perguntar(
    dados: ChatRequest,
    usuario_id: int = Depends(get_usuario_atual)
):
    from groq import Groq
    from core.config import settings
    from rag.vector_store import buscar_exames_semelhantes
    from repositories.exame_repository import buscar_exame_por_id
    from repositories.perfil_repository import perfil_para_contexto
    from repositories.odonto_repository import listar_registros_odonto
    from services.odonto_service import resumir_para_chat

    client = Groq(api_key=settings.GROQ_API_KEY)

    # busca exames relevantes via RAG
    ids = buscar_exames_semelhantes(usuario_id, dados.pergunta, k=3)
    exames = []
    for eid in ids:
        e = buscar_exame_por_id(eid)
        if e:
            exames.append(e)

    contexto_exames = "\n\n".join([
        f"Exame: {getattr(e,'nome_exame',None) or e.arquivo}\n"
        f"Data: {getattr(e,'data_exame',None) or e.data_upload[:10]}\n"
        f"Resumo: {e.resumo}"
        for e in exames
    ]) or "Nenhum exame relevante encontrado."

    contexto_perfil = perfil_para_contexto(usuario_id)
    registros_odonto = listar_registros_odonto(usuario_id)
    contexto_odonto  = resumir_para_chat(registros_odonto)

    system_prompt = f"""
Você é um assistente de saúde que ajuda o paciente a entender seus exames.
Explique de forma clara e empática. Nunca substitua consulta médica.

{contexto_perfil}
{contexto_odonto}
""".strip()

    messages = [{"role": "system", "content": system_prompt}]

    # adiciona histórico
    for msg in (dados.historico or []):
        if msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({
        "role": "user",
        "content": f"Exames relevantes:\n{contexto_exames}\n\nPergunta: {dados.pergunta}"
    })

    resposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1000
    )

    return ChatResponse(resposta=resposta.choices[0].message.content)
