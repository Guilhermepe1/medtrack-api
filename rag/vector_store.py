import numpy as np
from database.db import get_connection, get_cursor
from services.embedding_service import gerar_embedding


def adicionar_exame(usuario_id, exame_id, texto):
    embedding = gerar_embedding(texto)
    vetor = np.array(embedding, dtype="float32").tolist()

    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO exame_embeddings (exame_id, usuario_id, embedding)
        VALUES (%s, %s, %s)
    """, (exame_id, usuario_id, vetor))

    conn.commit()
    conn.close()


def buscar_exames_semelhantes(usuario_id, pergunta, k=3):
    embedding = gerar_embedding(pergunta)
    vetor = np.array(embedding, dtype="float32").tolist()

    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT exame_id
        FROM exame_embeddings
        WHERE usuario_id = %s
        ORDER BY embedding <-> %s::vector
        LIMIT %s
    """, (usuario_id, vetor, k))

    rows = cursor.fetchall()
    conn.close()

    return [row["exame_id"] for row in rows]