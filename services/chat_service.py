"""
Service responsável pelo chat de saúde baseado no histórico de exames.
Inclui contexto médico, odontológico e perfil do usuário.
"""

import streamlit as st

from services.ai_service import client
from services.odonto_service import resumir_para_chat
from rag.vector_store import buscar_exames_semelhantes
from repositories.exame_repository import buscar_exame_por_id
from repositories.perfil_repository import perfil_para_contexto
from repositories.odonto_repository import listar_registros_odonto


def perguntar_saude(pergunta):

    usuario_id = st.session_state["usuario_id"]

    # exames médicos relevantes via RAG
    ids_relevantes = buscar_exames_semelhantes(usuario_id, pergunta, k=3)
    exames = []
    for exame_id in ids_relevantes:
        exame = buscar_exame_por_id(exame_id)
        if exame:
            exames.append(exame)

    contexto_exames = montar_contexto_exames(exames)

    # contexto odontológico
    registros_odonto  = listar_registros_odonto(usuario_id)
    contexto_odonto   = resumir_para_chat(registros_odonto)

    # perfil de saúde do usuário
    contexto_perfil = perfil_para_contexto(usuario_id)

    system_prompt = f"""
Você é um assistente de saúde que ajuda o paciente a entender seus exames médicos e odontológicos.
Explique os resultados de forma clara, empática e acessível ao leigo.
Nunca substitua uma consulta médica ou odontológica — sempre recomende buscar um profissional para decisões clínicas.

{contexto_perfil}

{contexto_odonto}
""".strip()

    user_prompt = f"""
Exames médicos relevantes:

{contexto_exames}

Pergunta:
{pergunta}
""".strip()

    historico = st.session_state.get("historico_chat", [])

    messages = [{"role": "system", "content": system_prompt}]

    for msg in historico[:-1]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_prompt})

    resposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1000
    )

    return resposta.choices[0].message.content


def montar_contexto_exames(exames):
    if not exames:
        return "Nenhum exame relevante encontrado para esta pergunta."

    contexto = ""
    for exame in exames:
        nome = getattr(exame, "nome_exame", None) or exame.arquivo
        data = getattr(exame, "data_exame", None) or exame.data_upload[:10]
        contexto += f"\nExame: {nome}\nData: {data}\n\nResumo:\n{exame.resumo}\n"

    return contexto