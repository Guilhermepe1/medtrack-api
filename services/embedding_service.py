"""
Serviço responsável por gerar embeddings de texto
para utilização no RAG (vector search).
Modelo carregado de forma lazy para não travar o startup.
"""

import os

os.environ["TRANSFORMERS_CACHE"] = os.path.expanduser("~/.cache/huggingface")
os.environ["HF_HOME"]            = os.path.expanduser("~/.cache/huggingface")

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def gerar_embedding(texto: str):
    """
    Gera o embedding de um texto.
    Carrega o modelo na primeira chamada.
    """
    model     = _get_model()
    embedding = model.encode(texto)
    return embedding.tolist()
