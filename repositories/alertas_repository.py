"""
Repository responsável pelos alertas clínicos.
"""

from database.db import get_connection, get_cursor


def salvar_alertas(usuario_id, exame_id, valores):
    """
    Salva alertas para valores fora da referência.
    Só cria alerta se status for 'alto' ou 'baixo'.
    """
    alertas = [v for v in valores if v.get("status") in ("alto", "baixo")]

    if not alertas:
        return

    conn = get_connection()
    cursor = get_cursor(conn)

    for v in alertas:
        # evita duplicar alerta para o mesmo exame e parâmetro
        cursor.execute("""
            SELECT id FROM alertas_clinicos
            WHERE exame_id = %s AND parametro = %s
        """, (exame_id, v.get("parametro")))

        if cursor.fetchone():
            continue

        cursor.execute("""
            INSERT INTO alertas_clinicos
                (usuario_id, exame_id, parametro, valor, unidade,
                 referencia_min, referencia_max, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            usuario_id,
            exame_id,
            v.get("parametro"),
            v.get("valor"),
            v.get("unidade"),
            v.get("referencia_min"),
            v.get("referencia_max"),
            v.get("status"),
        ))

    conn.commit()
    conn.close()


def buscar_alertas_nao_lidos(usuario_id):
    """
    Retorna alertas ainda não lidos do usuário.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT
            a.id, a.parametro, a.valor, a.unidade,
            a.referencia_min, a.referencia_max, a.status,
            a.created_at, e.arquivo
        FROM alertas_clinicos a
        JOIN exames e ON e.id = a.exame_id
        WHERE a.usuario_id = %s AND a.lido = FALSE
        ORDER BY a.created_at DESC
    """, (usuario_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def buscar_todos_alertas(usuario_id):
    """
    Retorna todos os alertas do usuário, lidos e não lidos.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT
            a.id, a.parametro, a.valor, a.unidade,
            a.referencia_min, a.referencia_max, a.status,
            a.lido, a.created_at, e.arquivo
        FROM alertas_clinicos a
        JOIN exames e ON e.id = a.exame_id
        WHERE a.usuario_id = %s
        ORDER BY a.lido ASC, a.created_at DESC
    """, (usuario_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def marcar_alerta_lido(alerta_id):
    """
    Marca um alerta específico como lido.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        UPDATE alertas_clinicos
        SET lido = TRUE
        WHERE id = %s
    """, (alerta_id,))

    conn.commit()
    conn.close()


def marcar_todos_lidos(usuario_id):
    """
    Marca todos os alertas do usuário como lidos.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        UPDATE alertas_clinicos
        SET lido = TRUE
        WHERE usuario_id = %s AND lido = FALSE
    """, (usuario_id,))

    conn.commit()
    conn.close()