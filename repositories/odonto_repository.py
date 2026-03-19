"""
Repository para registros odontológicos e odontograma.
"""

from core.database import get_connection, get_cursor


def salvar_registro_odonto(usuario_id, dados, storage_path=None):
    """
    Salva um novo registro odontológico no banco.
    Retorna o id do registro criado.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO registros_odonto (
            usuario_id, tipo, subtipo, nome_arquivo, storage_path,
            texto_extraido, resumo, dentista, clinica, data_registro
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        usuario_id,
        dados.get("tipo"),
        dados.get("subtipo"),
        dados.get("nome_arquivo"),
        storage_path,
        dados.get("texto_extraido"),
        dados.get("resumo"),
        dados.get("dentista"),
        dados.get("clinica"),
        dados.get("data_registro"),
    ))

    row = cursor.fetchone()
    conn.commit()
    conn.close()

    return row["id"]


def listar_registros_odonto(usuario_id):
    """
    Lista todos os registros odontológicos do usuário.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT id, tipo, subtipo, nome_arquivo, resumo,
               dentista, clinica, data_registro, created_at
        FROM registros_odonto
        WHERE usuario_id = %s
        ORDER BY COALESCE(data_registro, created_at::date) DESC
    """, (usuario_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def buscar_registro_por_id(registro_id):
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT * FROM registros_odonto WHERE id = %s
    """, (registro_id,))

    row = cursor.fetchone()
    conn.close()

    return row


def excluir_registro_odonto(registro_id):
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute(
        "DELETE FROM registros_odonto WHERE id = %s", (registro_id,)
    )

    conn.commit()
    conn.close()


# ── Odontograma ──

def buscar_odontograma(usuario_id):
    """
    Retorna dict {numero_dente: {status, observacao}} do usuário.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT numero_dente, status, observacao
        FROM odontograma
        WHERE usuario_id = %s
    """, (usuario_id,))

    rows = cursor.fetchall()
    conn.close()

    return {row["numero_dente"]: row for row in rows}


def atualizar_dente(usuario_id, numero_dente, status, observacao=None):
    """
    Cria ou atualiza o status de um dente no odontograma.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO odontograma (usuario_id, numero_dente, status, observacao, updated_at)
        VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT (usuario_id, numero_dente) DO UPDATE SET
            status      = EXCLUDED.status,
            observacao  = EXCLUDED.observacao,
            updated_at  = NOW()
    """, (usuario_id, numero_dente, status, observacao))

    conn.commit()
    conn.close()


def atualizar_odontograma_em_lote(usuario_id, dentes):
    """
    Atualiza múltiplos dentes de uma vez.
    dentes: lista de dicts com {numero, status, observacao}
    """
    if not dentes:
        return

    conn = get_connection()
    cursor = get_cursor(conn)

    for dente in dentes:
        cursor.execute("""
            INSERT INTO odontograma (usuario_id, numero_dente, status, observacao, updated_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (usuario_id, numero_dente) DO UPDATE SET
                status     = EXCLUDED.status,
                observacao = EXCLUDED.observacao,
                updated_at = NOW()
        """, (
            usuario_id,
            dente.get("numero"),
            dente.get("status", "saudavel"),
            dente.get("observacao"),
        ))

    conn.commit()
    conn.close()