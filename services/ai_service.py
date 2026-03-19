"""
Service responsável por interagir com o modelo de IA.
"""

import os
from groq import Groq
from core.config import settings


def _get_groq_client():
    api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
    return Groq(api_key=api_key)


client = _get_groq_client()


def resumir_exame(texto):
    """
    Envia o texto do exame para a IA e retorna um resumo estruturado.
    """

    resposta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Você é um assistente médico que analisa exames."
            },
            {
                "role": "user",
                "content": f"""
Analise este exame médico.

Retorne:

Tipo do exame:
Principais resultados:
Pontos de atenção:
Explicação simples para paciente:

Exame:
{texto}
"""
            }
        ]
    )

    return resposta.choices[0].message.content