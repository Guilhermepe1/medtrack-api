"""
Script de migração — substitui imports do Streamlit pelos equivalentes FastAPI.
Execute na raiz do projeto medtrack-api:
    python migrar_imports.py
"""

import os
import re

SUBSTITUICOES = [
    # database
    ("from database.db import get_connection, get_cursor",
     "from core.database import get_connection, get_cursor"),
    ("from database.db import get_connection",
     "from core.database import get_connection"),

    # st.secrets → settings
    ("import streamlit as st\n", ""),
    ("from groq import Groq\nimport streamlit as st\n",
     "from groq import Groq\n"),

    # secrets individuais
    ('st.secrets.get("GROQ_API_KEY")',   'settings.GROQ_API_KEY'),
    ('st.secrets["GROQ_API_KEY"]',       'settings.GROQ_API_KEY'),
    ('st.secrets.get("SUPABASE_URL")',    'settings.SUPABASE_URL'),
    ('st.secrets["SUPABASE_URL"]',        'settings.SUPABASE_URL'),
    ('st.secrets.get("SUPABASE_SERVICE_KEY")', 'settings.SUPABASE_SERVICE_KEY'),
    ('st.secrets["SUPABASE_SERVICE_KEY"]',     'settings.SUPABASE_SERVICE_KEY'),
    ('st.secrets["DB_HOST"]',            'settings.DB_HOST'),
    ('st.secrets["DB_USER"]',            'settings.DB_USER'),
    ('st.secrets["DB_PASSWORD"]',        'settings.DB_PASSWORD'),

    # st.error / st.info / st.success → print (não quebram mas não fazem nada)
    ('st.error(',   'print('),
    ('st.info(',    'print('),
    ('st.success(', 'print('),
    ('st.warning(', 'print('),
]

# adiciona import de settings onde necessário
PRECISA_SETTINGS = [
    'settings.GROQ_API_KEY',
    'settings.SUPABASE_URL',
    'settings.SUPABASE_SERVICE_KEY',
    'settings.DB_HOST',
    'settings.DB_USER',
    'settings.DB_PASSWORD',
]

IMPORT_SETTINGS = "from core.config import settings\n"

PASTAS = ["services", "repositories", "rag"]
EXTENSAO = ".py"


def migrar_arquivo(caminho: str):
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.read()

    original = conteudo
    alterado = False

    for antigo, novo in SUBSTITUICOES:
        if antigo in conteudo:
            conteudo = conteudo.replace(antigo, novo)
            alterado = True

    # adiciona import de settings se necessário e ainda não existe
    precisa = any(s in conteudo for s in PRECISA_SETTINGS)
    ja_tem  = IMPORT_SETTINGS.strip() in conteudo

    if precisa and not ja_tem:
        # insere após a última linha de import
        linhas = conteudo.split("\n")
        ultimo_import = 0
        for i, linha in enumerate(linhas):
            if linha.startswith("import ") or linha.startswith("from "):
                ultimo_import = i
        linhas.insert(ultimo_import + 1, IMPORT_SETTINGS.strip())
        conteudo = "\n".join(linhas)
        alterado = True

    if alterado:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        print(f"✅ Migrado: {caminho}")
    else:
        print(f"⏭️  Sem alterações: {caminho}")


def main():
    raiz = os.path.dirname(os.path.abspath(__file__))
    total = 0

    for pasta in PASTAS:
        caminho_pasta = os.path.join(raiz, pasta)
        if not os.path.exists(caminho_pasta):
            print(f"⚠️  Pasta não encontrada: {pasta}")
            continue

        for nome in os.listdir(caminho_pasta):
            if nome.endswith(EXTENSAO):
                migrar_arquivo(os.path.join(caminho_pasta, nome))
                total += 1

    print(f"\n✅ {total} arquivo(s) verificado(s).")
    print("\nPróximos passos:")
    print("  git add services/ repositories/ rag/")
    print('  git commit -m "fix: migra imports do Streamlit para FastAPI"')
    print("  git push")


if __name__ == "__main__":
    main()
