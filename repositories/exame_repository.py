"""
Repository responsável por todas as operações no banco
relacionadas à entidade Exame.
"""

from core.database import get_connection, get_cursor


def _row_para_dict(row):
    """Converte uma row do banco em dicionário com atributos de exame."""
    d = dict(row)
    # garante que data_upload seja string
    if d.get("data_upload"):
        d["data_upload"] = str(d["data_upload"])
    if d.get("data_exame"):
        d["data_exame"] = str(d["data_exame"])
    return d


class ExameObj:
    """
    Objeto simples para manter compatibilidade com código que usa
    atributos como exame.resumo, exame.arquivo, etc.
    """
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getattr__(self, name):
        return None


def _row_para_obj(row):
    d = dict(row)
    if d.get("data_upload"):
        d["data_upload"] = str(d["data_upload"])
    if d.get("data_exame"):
        d["data_exame"] = str(d["data_exame"])
    return ExameObj(**d)


def salvar_exame(usuario_id, arquivo, texto, resumo, categoria,
                 storage_path=None, nome_exame=None, data_exame=None,
                 medico=None, hospital=None):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO exames
            (usuario_id, arquivo, texto, resumo, categoria,
             storage_path, nome_exame, data_exame, medico, hospital)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        usuario_id, arquivo, texto, resumo, categoria,
        storage_path, nome_exame, data_exame, medico, hospital
    ))

    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return row["id"]


def listar_exames(usuario_id):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT id, arquivo, resumo, data_upload, categoria,
               nome_exame, data_exame, medico, hospital, storage_path
        FROM exames
        WHERE usuario_id = %s
        ORDER BY COALESCE(data_exame, data_upload::date) DESC
    """, (usuario_id,))

    rows = cursor.fetchall()
    conn.close()

    return [_row_para_obj(row) for row in rows]


def buscar_exame_por_id(exame_id):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT id, arquivo, texto, resumo, data_upload, categoria,
               nome_exame, data_exame, medico, hospital, storage_path
        FROM exames
        WHERE id = %s
    """, (exame_id,))

    row = cursor.fetchone()
    conn.close()

    return _row_para_obj(row) if row else None


def excluir_exame(exame_id):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("SELECT id FROM exames WHERE id = %s", (exame_id,))
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute("DELETE FROM exames WHERE id = %s", (exame_id,))
    conn.commit()
    conn.close()
    return True


def montar_historico_exames(usuario_id):
    exames   = listar_exames(usuario_id)
    historico = ""

    for e in exames:
        nome     = e.nome_exame or e.arquivo
        data     = e.data_exame or (e.data_upload[:10] if e.data_upload else "")
        medico   = f" | Dr(a). {e.medico}"   if e.medico   else ""
        hospital = f" | {e.hospital}"         if e.hospital else ""

        historico += f"""
Exame: {nome}{medico}{hospital}
Data: {data}
Categoria: {e.categoria}

Resumo:
{e.resumo}

"""
    return historico


def buscar_exames_relevantes(usuario_id, pergunta):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT id, arquivo, texto, resumo, data_upload, categoria,
               nome_exame, data_exame, medico, hospital
        FROM exames
        WHERE usuario_id = %s
    """, (usuario_id,))

    rows = cursor.fetchall()
    conn.close()

    pergunta_lower = pergunta.lower()
    relevantes     = []

    for row in rows:
        texto  = (row["texto"]  or "").lower()
        resumo = (row["resumo"] or "").lower()
        if any(p in texto or p in resumo for p in pergunta_lower.split()):
            relevantes.append(_row_para_obj(row))

    return relevantes


def buscar_exame_por_nome(usuario_id, nome):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT id, arquivo, texto, resumo, data_upload, categoria,
               nome_exame, data_exame, medico, hospital
        FROM exames
        WHERE usuario_id = %s AND arquivo = %s
    """, (usuario_id, nome))

    row = cursor.fetchone()
    conn.close()

    return _row_para_obj(row) if row else None


def montar_timeline_exames(usuario_id):
    exames   = listar_exames(usuario_id)
    timeline = {}

    for e in exames:
        categoria = e.categoria or "Outros"
        data_ref  = e.data_exame or e.data_upload
        ano       = str(data_ref)[:4] if data_ref else "?"

        if categoria not in timeline:
            timeline[categoria] = {}
        if ano not in timeline[categoria]:
            timeline[categoria][ano] = []

        timeline[categoria][ano].append(e)

    return timeline