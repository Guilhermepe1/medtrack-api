"""
Serviço responsável por gerar embeddings de texto
para utilização no RAG (vector search).
"""

import os
from sentence_transformers import SentenceTransformer


# modelo leve e muito usado para RAG
model = SentenceTransformer("all-MiniLM-L6-v2")


def gerar_embedding(texto: str):
    """
    Gera o embedding de um texto.
    """

    embedding = model.encode(texto)

    return embedding.tolist()
