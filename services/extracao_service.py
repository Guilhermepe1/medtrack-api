
# Service responsável por extrair valores estruturados de exames laboratoriais.


import json
from groq import Groq
from core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

PROMPT_EXTRACAO = """
Você é um especialista em laudos médicos e laboratoriais.
Analise o texto do exame e extraia todas as informações disponíveis.

Retorne APENAS um JSON válido, sem texto adicional, no seguinte formato:
{
  "nome_exame": "nome do tipo de exame (ex: Hemograma Completo, Ressonância Magnética) ou null",
  "data_exame": "YYYY-MM-DD ou null se não encontrar",
  "medico": "nome do médico solicitante ou responsável ou null",
  "hospital": "nome do laboratório, clínica ou hospital ou null",
  "valores": [
    {
      "parametro": "nome do parâmetro",
      "valor": número ou null,
      "unidade": "unidade de medida",
      "referencia_min": número ou null,
      "referencia_max": número ou null,
      "status": "normal", "alto" ou "baixo"
    }
  ]
}

Parâmetros comuns para extrair (quando presentes):
- Hemograma: Hemoglobina, Hematócrito, Eritrócitos, VCM, HCM, CHCM, RDW,
  Leucócitos, Neutrófilos, Linfócitos, Monócitos, Eosinófilos, Basófilos, Plaquetas
- Bioquímica: Glicose, Creatinina, Ureia, Ácido Úrico, TGO, TGP
- Lipidograma: Colesterol Total, HDL, LDL, VLDL, Triglicerídeos
- Tireoide: TSH, T3, T4 Livre
- Outros: Vitamina D, Vitamina B12, Ferritina, Hemoglobina Glicada

Regras:
- valor deve ser sempre número (float), nunca string
- Se o parâmetro não tiver valor numérico identificável, omita-o da lista
- status deve ser "normal", "alto" ou "baixo" baseado nos valores de referência
- Se não houver referência, defina status como "normal"
- Para nome_exame, prefira o nome oficial do exame, não a marca do laboratório
- Para medico, inclua apenas o nome, sem CRM
"""


def extrair_metadados_e_valores(texto: str) -> dict:
    """
    Usa a IA para extrair metadados e valores estruturados do exame.
    Retorna dicionário com nome_exame, data_exame, medico, hospital e valores.
    """
    try:
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": PROMPT_EXTRACAO},
                {"role": "user", "content": f"Texto do exame:\n\n{texto}"}
            ],
            temperature=0.1
        )

        conteudo = resposta.choices[0].message.content.strip()

        # remove possíveis blocos de markdown
        if conteudo.startswith("```"):
            conteudo = conteudo.split("```")[1]
            if conteudo.startswith("json"):
                conteudo = conteudo[4:]

        return json.loads(conteudo)

    except Exception as e:
        print(f"Erro ao extrair metadados: {e}")
        return {
            "nome_exame": None,
            "data_exame": None,
            "medico": None,
            "hospital": None,
            "valores": []
        }


# mantém compatibilidade com chamadas antigas
def extrair_valores(texto: str) -> dict:
    resultado = extrair_metadados_e_valores(texto)
    return {
        "data_coleta": resultado.get("data_exame"),
        "valores": resultado.get("valores", [])
    }