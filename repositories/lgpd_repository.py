"""
Repository responsável pela conformidade LGPD:
consentimentos, logs de acesso e direito ao esquecimento.
"""

from database.db import get_connection, get_cursor

VERSAO_ATUAL = "1.0"


# ── Consentimento ──

def buscar_consentimento(usuario_id):
    """
    Retorna o consentimento mais recente do usuário para a versão atual.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT id, versao, aceito, created_at
        FROM consentimentos
        WHERE usuario_id = %s AND versao = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (usuario_id, VERSAO_ATUAL))

    row = cursor.fetchone()
    conn.close()

    return row


def registrar_consentimento(usuario_id, aceito, ip=None, user_agent=None):
    """
    Registra o aceite ou recusa do termo de consentimento.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO consentimentos
            (usuario_id, versao, aceito, ip, user_agent)
        VALUES (%s, %s, %s, %s, %s)
    """, (usuario_id, VERSAO_ATUAL, aceito, ip, user_agent))

    conn.commit()
    conn.close()


def usuario_consentiu(usuario_id):
    """
    Verifica se o usuário já aceitou o termo na versão atual.
    """
    consentimento = buscar_consentimento(usuario_id)
    return consentimento is not None and consentimento["aceito"]


# ── Logs de acesso ──

def registrar_log(usuario_id, acao, descricao=None, ip=None):
    """
    Registra uma ação do usuário para fins de auditoria LGPD.
    Ações sugeridas: login, logout, upload_exame, visualizou_exame,
                     exportou_dados, deletou_exame, solicitou_exclusao
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO logs_acesso (usuario_id, acao, descricao, ip)
        VALUES (%s, %s, %s, %s)
    """, (usuario_id, acao, descricao, ip))

    conn.commit()
    conn.close()


def buscar_logs(usuario_id, limite=50):
    """
    Retorna os logs de acesso do usuário.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT acao, descricao, ip, created_at
        FROM logs_acesso
        WHERE usuario_id = %s
        ORDER BY created_at DESC
        LIMIT %s
    """, (usuario_id, limite))

    rows = cursor.fetchall()
    conn.close()

    return rows


# ── Direito ao esquecimento ──

def excluir_todos_dados_usuario(usuario_id):
    """
    Remove todos os dados do usuário do banco (direito ao esquecimento).
    A exclusão em cascata cuida das tabelas relacionadas:
    exames, exame_embeddings, exame_valores, alertas_clinicos,
    perfil_saude, registros_odonto, odontograma, consentimentos, logs_acesso.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    # registra o log antes de deletar
    cursor.execute("""
        INSERT INTO logs_acesso (usuario_id, acao, descricao)
        VALUES (%s, 'solicitou_exclusao_conta',
                'Usuário solicitou exclusão completa de dados (LGPD)')
    """, (usuario_id,))

    # deleta o usuário — cascade remove tudo mais
    cursor.execute("""
        DELETE FROM usuarios WHERE id = %s
    """, (usuario_id,))

    conn.commit()
    conn.close()
