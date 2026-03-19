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
    arquivo:    UploadFile = File(...),
    nome_exame: Optional[str] = Form(None),
    data_exame: Optional[str] = Form(None),
    medico:     Optional[str] = Form(None),
    hospital:   Optional[str] = Form(None),
    token:      Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
):
    # extrai usuario_id do token JWT manualmente
    from core.security import decodificar_token
    from fastapi import HTTPException

    raw_token = token or (authorization.split(" ")[1] if authorization and " " in authorization else None)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Token não fornecido.")
    payload    = decodificar_token(raw_token)
    usuario_id = int(payload.get("sub"))
    from services.ai_service import resumir_exame
    from services.extracao_service import extrair_metadados_e_valores
    from services.exame_classifier import classificar_exame
    from services.storage_service import upload_arquivo
    from repositories.valores_repository import salvar_valores
    from repositories.alertas_repository import salvar_alertas
    from services.document_reader import extrair_texto_documento

    conteudo = await arquivo.read()

    # ── Extrai texto ──
    ext = os.path.splitext(arquivo.filename)[1].lower()
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(conteudo)
        tmp_path = tmp.name

    class FakeFile:
        name = arquivo.filename
        def read(self): return conteudo
        def seek(self, x): pass

    try:
        texto = extrair_texto_documento(FakeFile())
    except Exception as e:
        texto = f"Erro ao extrair texto: {e}"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # ── Processa com IA ──
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

    # ── Storage ──
    try:
        storage_path = upload_arquivo(usuario_id, arquivo.filename, conteudo)
    except Exception:
        storage_path = None

    # ── Salva no banco ──
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO exames (
            usuario_id, arquivo, texto, resumo, categoria,
            storage_path, nome_exame, data_exame, medico, hospital
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (
        usuario_id, arquivo.filename, texto, resumo, categoria,
        storage_path, nome_final, data_final, med_final, hosp_final
    ))

    exame_id = cursor.fetchone()["id"]
    conn.commit()

    # ── Valores e alertas ──
    if valores:
        try:
            salvar_valores(exame_id, usuario_id, data_final, valores)
            salvar_alertas(usuario_id, exame_id, valores)
        except Exception:
            pass

    # ── Embedding (não bloqueia se falhar) ──
    try:
        from services.embedding_service import gerar_embedding
        embedding = gerar_embedding(texto)
        cursor.execute("""
            INSERT INTO exame_embeddings (exame_id, usuario_id, embedding)
            VALUES (%s, %s, %s)
        """, (exame_id, usuario_id, embedding.tolist()))
        conn.commit()
    except Exception:
        pass

    conn.close()

    return {
        "exame_id":   exame_id,
        "nome_exame": nome_final or arquivo.filename,
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
