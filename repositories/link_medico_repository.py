"""
Repository para links temporários de compartilhamento com médico.
"""

import secrets
from datetime import datetime, timedelta
from database.db import get_connection, get_cursor


def gerar_token():
    return secrets.token_urlsafe(32)


def criar_link(usuario_id, horas=24):
    """
    Cria um novo link temporário para o usuário.
    Invalida links anteriores do mesmo usuário.
    Retorna o token gerado.
    """
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        DELETE FROM links_medico WHERE usuario_id = %s
    """, (usuario_id,))

    token     = gerar_token()
    expira_em = datetime.now() + timedelta(hours=horas)

    cursor.execute("""
        INSERT INTO links_medico (usuario_id, token, expira_em)
        VALUES (%s, %s, %s)
    """, (usuario_id, token, expira_em))

    conn.commit()
    conn.close()

    return token


def buscar_link_valido(token):
    """
    Busca um link pelo token e verifica se ainda é válido.
    """
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT id, usuario_id, expira_em, acessado_em
        FROM links_medico
        WHERE token = %s AND expira_em > NOW()
    """, (token,))

    row = cursor.fetchone()
    conn.close()

    return row


def registrar_acesso(token):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        UPDATE links_medico SET acessado_em = NOW() WHERE token = %s
    """, (token,))

    conn.commit()
    conn.close()


def listar_links_usuario(usuario_id):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT token, expira_em, acessado_em, created_at
        FROM links_medico
        WHERE usuario_id = %s
        ORDER BY created_at DESC
        LIMIT 5
    """, (usuario_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows


def revogar_links(usuario_id):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute(
        "DELETE FROM links_medico WHERE usuario_id = %s", (usuario_id,)
    )

    conn.commit()
    conn.close()
