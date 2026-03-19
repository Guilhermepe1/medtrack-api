"""
Repository responsável pelos valores estruturados extraídos dos exames.
"""

from core.database import get_connection, get_cursor


def salvar_valores(exame_id, usuario_id, data_coleta, valores):
    """
    Salva os valores extraídos de um exame na tabela exame_valores.
    """
    if not valores:
        return

    conn = get_connection()
    cursor = get_cursor(conn)

    for v in valores:
        cursor.execute("""
            INSERT INTO exame_valores
                (exame_id, usuario_id, parametro, valor, unidade,
                 referencia_min, referencia_max, status, data_coleta)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            exame_id,
            usuario_id,
            v.get("parametro"),
            v.get("valor"),
            v.get("unidade"),
            v.get("referencia_min"),
            v.get("referencia_max"),
            v.get("status", "normal"),
            data_coleta
        ))

    conn.commit()
    conn.close()


def buscar_valores_por_exame(exame_id):
    """
    Retorna todos os valores de um exame específico.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT parametro, valor, unidade, referencia_min, referencia_max, status, data_coleta
        FROM exame_valores
        WHERE exame_id = %s
        ORDER BY parametro
    """, (exame_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def buscar_evolucao_parametro(usuario_id, parametro):
    """
    Retorna a evolução de um parâmetro ao longo do tempo para um usuário.
    Usado para montar gráficos de tendência.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT data_coleta, valor, unidade, referencia_min, referencia_max, status
        FROM exame_valores
        WHERE usuario_id = %s AND parametro ILIKE %s
        ORDER BY data_coleta ASC
    """, (usuario_id, f"%{parametro}%"))

    rows = cursor.fetchall()
    conn.close()

    return rows


def buscar_parametros_disponiveis(usuario_id):
    """
    Lista todos os parâmetros que o usuário tem registrado.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT DISTINCT parametro
        FROM exame_valores
        WHERE usuario_id = %s
        ORDER BY parametro
    """, (usuario_id,))

    rows = cursor.fetchall()
    conn.close()

    return [row["parametro"] for row in rows]