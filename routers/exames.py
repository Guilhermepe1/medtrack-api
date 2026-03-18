"""
Router de exames médicos.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import Optional, List
from datetime import date

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


@router.post("/upload")
async def upload_exame(
    arquivo: UploadFile = File(...),
    nome_exame: Optional[str] = Form(None),
    data_exame: Optional[str] = Form(None),
    medico: Optional[str] = Form(None),
    hospital: Optional[str] = Form(None),
    usuario_id: int = Depends(get_usuario_atual)
):
    """
    Recebe o arquivo, extrai texto, gera resumo via IA,
    salva no banco e indexa no pgvector.
    """
    import io
    from services.ai_service import resumir_exame
    from services.extracao_service import extrair_metadados_e_valores
    from services.exame_classifier import classificar_exame
    from services.storage_service import upload_arquivo
    from services.embedding_service import gerar_embedding
    from repositories.valores_repository import salvar_valores
    from repositories.alertas_repository import salvar_alertas

    conteudo = await arquivo.read()

    # extrai texto
    from services.document_reader import extrair_texto_documento
    import tempfile, os

    ext = os.path.splitext(arquivo.filename)[1].lower()
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(conteudo)
        tmp_path = tmp.name

    with open(tmp_path, "rb") as f:
        class FakeFile:
            name = arquivo.filename
            def read(self): return conteudo
            def seek(self, x): pass
        texto = extrair_texto_documento(FakeFile())

    os.unlink(tmp_path)

    resumo    = resumir_exame(texto)
    categoria = classificar_exame(texto)
    resultado = extrair_metadados_e_valores(texto)
    valores   = resultado.get("valores", [])

    # usa metadados confirmados pelo usuário ou extraídos pela IA
    nome_final  = nome_exame or resultado.get("nome_exame")
    data_final  = data_exame or resultado.get("data_exame")
    med_final   = medico    or resultado.get("medico")
    hosp_final  = hospital  or resultado.get("hospital")

    storage_path = upload_arquivo(usuario_id, arquivo.filename, conteudo)

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

    # salva valores e alertas
    if valores:
        salvar_valores(exame_id, usuario_id, data_final, valores)
        salvar_alertas(usuario_id, exame_id, valores)

    # indexa embedding
    embedding = gerar_embedding(texto)
    cursor.execute("""
        INSERT INTO exame_embeddings (exame_id, usuario_id, embedding)
        VALUES (%s, %s, %s)
    """, (exame_id, usuario_id, embedding.tolist()))

    conn.commit()
    conn.close()

    return {
        "exame_id":  exame_id,
        "nome_exame": nome_final or arquivo.filename,
        "categoria":  categoria,
        "resumo":     resumo,
        "alertas":    len([v for v in valores if v.get("status") in ("alto","baixo")])
    }


@router.delete("/{exame_id}")
def excluir_exame(
    exame_id: int,
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
    exame_id: int,
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
