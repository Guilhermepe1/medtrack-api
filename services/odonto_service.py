"""
Service responsável pelo processamento de documentos odontológicos.
"""

import json
from groq import Groq
from core.config import settings

client = Groq(api_key=settings.GROQ_API_KEY)

PROMPT_ODONTO = """
Você é um especialista em laudos radiográficos odontológicos.
Analise o texto do laudo e retorne APENAS um JSON válido, sem texto adicional.

Formato esperado:
{
  "tipo": "radiografia" | "laudo" | "plano_tratamento" | "foto",
  "subtipo": "panoramica" | "periapical" | "bite-wing" | null,
  "data_registro": "YYYY-MM-DD ou null",
  "dentista": "nome do dentista/doutor ou null",
  "clinica": "nome da clínica/laboratório ou null",
  "resumo": "resumo em linguagem acessível para o paciente, máximo 3 frases",
  "dentes_afetados": [
    {
      "numero": número inteiro FDI do dente,
      "status": um dos valores abaixo,
      "observacao": "descrição breve do achado"
    }
  ],
  "tratamentos_realizados": [],
  "tratamentos_planejados": [],
  "observacoes_gerais": "achados gerais não relacionados a dentes específicos ou null"
}

Mapeamento de achados para status (use EXATAMENTE esses valores):
- "carie"            → cárie, lesão cariosa, imagem radiolúcida na coroa, imagem sugestiva de cárie
- "tratamento_canal" → tratamento de canal, rarefação óssea periapical, arredondamento apical, imagem radiolúcida periapical
- "ausente"          → ausente, extraído, não presente
- "implante"         → implante, fixture
- "coroa"            → coroa, prótese, reabilitação protética
- "restaurado"       → restauração, obturação, amálgama, resina
- "saudavel"         → sem achados patológicos relevantes

Regras importantes:
- Extraia TODOS os dentes mencionados no laudo, um por um
- Se um dente tiver múltiplos achados, use o status mais grave seguindo a ordem:
  tratamento_canal > carie > coroa > implante > restaurado > ausente > saudavel
- "Imagem radiolúcida na coroa" = carie
- "Rarefação óssea periapical" = tratamento_canal
- "Arredondamento apical" = tratamento_canal
- "Semi incluso" ou "impactado" = use status "ausente" com observação descritiva
- Anomalia de raiz, giroversão, desgaste incisal = "saudavel" com observacao descritiva
- numero deve ser inteiro, nunca string
- Não invente dentes que não estão no laudo
"""


def extrair_dados_odonto(texto: str) -> dict:
    """
    Usa IA para extrair dados estruturados de documento odontológico.
    """
    try:
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": PROMPT_ODONTO},
                {"role": "user", "content": f"Laudo odontológico:\n\n{texto}"}
            ],
            temperature=0.0
        )

        conteudo = resposta.choices[0].message.content.strip()

        if conteudo.startswith("```"):
            conteudo = conteudo.split("```")[1]
            if conteudo.startswith("json"):
                conteudo = conteudo[4:]

        return json.loads(conteudo)

    except Exception as e:
        print(f"Erro ao extrair dados odonto: {e}")
        return {
            "tipo": "laudo",
            "subtipo": None,
            "data_registro": None,
            "dentista": None,
            "clinica": None,
            "resumo": "Não foi possível extrair automaticamente. Revise manualmente.",
            "dentes_afetados": [],
            "tratamentos_realizados": [],
            "tratamentos_planejados": [],
            "observacoes_gerais": None
        }


def resumir_para_chat(registros) -> str:
    """
    Formata registros odontológicos como contexto para o chat de IA.
    """
    if not registros:
        return ""

    linhas = ["=== Histórico odontológico ==="]

    for r in registros:
        data  = str(r.get("data_registro") or r.get("created_at", ""))[:10]
        tipo  = r.get("tipo", "registro").replace("_", " ").title()
        linhas.append(f"\n{tipo} — {data}")
        if r.get("dentista"):
            linhas.append(f"Dentista: {r['dentista']}")
        if r.get("resumo"):
            linhas.append(f"Resumo: {r['resumo']}")

    linhas.append("=============================")
    return "\n".join(linhas)