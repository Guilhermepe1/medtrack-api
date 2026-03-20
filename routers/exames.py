"""
Router de exames médicos.
"""

import os
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Request, Header
from typing import Optional, List

from core.security import get_usuario_atual
from core.database import get_connection, get_cursor
from models.schemas import ExameResponse

router = APIRouter(prefix="/exames", tags=["Exames"])


@router.get("/", response_model=List[ExameResponse])
def listar_exames(usuario_id: int = Depends(get_usuario_atual)):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT id, arquivo, resumo, categoria, nome_exame,
               data_exame, data_upload, medico, hospital, storage_path
        FROM exames
        WHERE usuario_id = %s
        ORDER BY COALESCE(data_exame, data_upload::date) DESC
    """, (usuario_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@router.post("/upload/debug")
async def upload_debug(request: Request):
    """Endpoint temporário para debugar o upload."""
    form    = await request.form()
    headers = dict(request.headers)
    return {
        "form_keys":    list(form.keys()),
        "content_type": headers.get("content-type", ""),
        "auth":         headers.get("authorization", "")[:30],
    }


@router.post("/upload")
async def upload_exame(
    payload:    dict,
    usuario_id: int = Depends(get_usuario_atual),
):
    import base64, os, tempfile
    from services.ai_service import resumir_exame
    from services.extracao_service import extrair_metadados_e_valores
    from services.exame_classifier import classificar_exame
    from services.storage_service import upload_arquivo
    from repositories.valores_repository import salvar_valores
    from repositories.alertas_repository import salvar_alertas
    from services.document_reader import extrair_texto_documento

    arquivo_nome = payload.get("arquivo_nome", "exame.pdf")
    arquivo_b64  = payload.get("arquivo_b64", "")
    nome_exame   = payload.get("nome_exame")
    data_exame   = payload.get("data_exame")
    medico       = payload.get("medico")
    hospital     = payload.get("hospital")

    # decodifica base64
    try:
        conteudo = base64.b64decode(arquivo_b64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao decodificar arquivo: {e}")

    # extrai texto
    ext = os.path.splitext(arquivo_nome)[1].lower() or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(conteudo)
        tmp_path = tmp.name

    class FakeFile:
        name = arquivo_nome
        def read(self): return conteudo
        def seek(self, x): pass

    try:
        texto = extrair_texto_documento(FakeFile())
    except Exception as e:
        texto = f"Erro ao extrair texto: {e}"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    try:
        resumo = resumir_exame(texto)
    except Exception:
        resumo = "Resumo não disponível."

    try:
        categoria = classificar_exame(texto)
    except Exception:
        categoria = "Outros"

    try:
        resultado = extrair_metadados_e_valores(texto)
        valores   = resultado.get("valores", [])
    except Exception:
        resultado = {}
        valores   = []

    nome_final = nome_exame or resultado.get("nome_exame")
    data_final = data_exame or resultado.get("data_exame")
    med_final  = medico     or resultado.get("medico")
    hosp_final = hospital   or resultado.get("hospital")

    try:
        storage_path = upload_arquivo(usuario_id, arquivo_nome, conteudo)
    except Exception:
        storage_path = None

    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO exames (
            usuario_id, arquivo, texto, resumo, categoria,
            storage_path, nome_exame, data_exame, medico, hospital
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (
        usuario_id, arquivo_nome, texto, resumo, categoria,
        storage_path, nome_final, data_final, med_final, hosp_final
    ))

    exame_id = cursor.fetchone()["id"]
    conn.commit()

    if valores:
        try:
            salvar_valores(exame_id, usuario_id, data_final, valores)
            salvar_alertas(usuario_id, exame_id, valores)
        except Exception:
            pass

    conn.close()

    # retorna imediatamente — embedding é gerado em background
    import threading

    def gerar_embedding_background(exame_id, usuario_id, texto):
        try:
            from services.embedding_service import gerar_embedding
            from core.database import get_connection, get_cursor
            embedding = gerar_embedding(texto)
            conn2   = get_connection()
            cursor2 = get_cursor(conn2)
            cursor2.execute("""
                INSERT INTO exame_embeddings (exame_id, usuario_id, embedding)
                VALUES (%s, %s, %s)
                ON CONFLICT (exame_id) DO UPDATE SET embedding = EXCLUDED.embedding
            """, (exame_id, usuario_id, embedding.tolist()))
            conn2.commit()
            conn2.close()
        except Exception:
            pass

    thread = threading.Thread(
        target=gerar_embedding_background,
        args=(exame_id, usuario_id, texto),
        daemon=True
    )
    thread.start()

    return {
        "exame_id":   exame_id,
        "nome_exame": nome_final or arquivo_nome,
        "categoria":  categoria,
        "resumo":     resumo,
        "alertas":    len([v for v in valores if v.get("status") in ("alto", "baixo")])
    }

@router.delete("/{exame_id}")
def excluir_exame(
    exame_id:   int,
    usuario_id: int = Depends(get_usuario_atual)
):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute(
        "SELECT id FROM exames WHERE id = %s AND usuario_id = %s",
        (exame_id, usuario_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Exame não encontrado.")

    cursor.execute("DELETE FROM exames WHERE id = %s", (exame_id,))
    conn.commit()
    conn.close()

    return {"message": "Exame excluído com sucesso."}


@router.get("/{exame_id}", response_model=ExameResponse)
def buscar_exame(
    exame_id:   int,
    usuario_id: int = Depends(get_usuario_atual)
):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT id, arquivo, resumo, categoria, nome_exame,
               data_exame, data_upload, medico, hospital, storage_path
        FROM exames
        WHERE id = %s AND usuario_id = %s
    """, (exame_id, usuario_id))

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Exame não encontrado.")

    return dict(row)
