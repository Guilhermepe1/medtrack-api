"""
Responsável por gerar embeddings de texto.
"""

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")


def gerar_embedding(texto: str):

    embedding = model.encode(texto)

    return embedding
