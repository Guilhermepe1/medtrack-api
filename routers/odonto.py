"""
Router odontológico — odontograma e documentos.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import Optional, List
from core.security import get_usuario_atual
from core.database import get_connection, get_cursor
from models.schemas import DenteStatusRequest, RegistroOdontoResponse

router = APIRouter(prefix="/odonto", tags=["Odontologia"])


# ── Odontograma ──

@router.get("/odontograma")
def get_odontograma(usuario_id: int = Depends(get_usuario_atual)):
    """Retorna o estado de todos os dentes do usuário."""
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT numero_dente, status, observacao
        FROM odontograma
        WHERE usuario_id = %s
        ORDER BY numero_dente
    """, (usuario_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


@router.post("/dente")
def salvar_dente(
    dados: DenteStatusRequest,
    usuario_id: int = Depends(get_usuario_atual)
):
    """Cria ou atualiza o status de um dente no odontograma."""
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO odontograma (usuario_id, numero_dente, status, observacao, updated_at)
        VALUES (%s, %s, %s, %s, NOW())
        ON CONFLICT (usuario_id, numero_dente) DO UPDATE SET
            status      = EXCLUDED.status,
            observacao  = EXCLUDED.observacao,
            updated_at  = NOW()
    """, (usuario_id, dados.numero_dente, dados.status, dados.observacao))

    conn.commit()
    conn.close()

    return {"message": "Dente atualizado com sucesso."}


# ── Documentos odontológicos ──

@router.get("/registros", response_model=List[RegistroOdontoResponse])
def listar_registros(usuario_id: int = Depends(get_usuario_atual)):
    """Lista todos os documentos odontológicos do usuário."""
    conn   = get_connection()
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

    return [dict(r) for r in rows]


@router.post("/upload")
async def upload_documento(
    arquivo:        UploadFile = File(...),
    tipo:           str        = Form("radiografia"),
    dentista:       Optional[str] = Form(None),
    clinica:        Optional[str] = Form(None),
    data_registro:  Optional[str] = Form(None),
    usuario_id:     int           = Depends(get_usuario_atual)
):
    """
    Recebe um documento odontológico, extrai texto via OCR,
    analisa com IA e atualiza o odontograma automaticamente.
    """
    from services.odonto_service import extrair_dados_odonto
    from services.storage_service import upload_arquivo
    from repositories.odonto_repository import (
        salvar_registro_odonto,
        atualizar_odontograma_em_lote,
    )
    import os

    conteudo = await arquivo.read()

    # extrai texto
    from services.document_reader import extrair_texto_documento
    import tempfile

    ext = os.path.splitext(arquivo.filename)[1].lower()
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(conteudo)
        tmp_path = tmp.name

    class FakeFile:
        name = arquivo.filename
        def read(self): return conteudo
        def seek(self, x): pass

    texto   = extrair_texto_documento(FakeFile())
    os.unlink(tmp_path)

    # analisa com IA
    resultado = extrair_dados_odonto(texto)

    # usa metadados do usuário ou extraídos pela IA
    tipo_final      = tipo
    dentista_final  = dentista  or resultado.get("dentista")
    clinica_final   = clinica   or resultado.get("clinica")
    data_final      = data_registro or resultado.get("data_registro")
    subtipo_final   = resultado.get("subtipo")
    resumo_final    = resultado.get("resumo", "")

    # upload para Storage
    storage_path = upload_arquivo(usuario_id, arquivo.filename, conteudo)

    # salva no banco
    registro_id = salvar_registro_odonto(usuario_id, {
        "tipo":           tipo_final,
        "subtipo":        subtipo_final,
        "nome_arquivo":   arquivo.filename,
        "texto_extraido": texto,
        "resumo":         resumo_final,
        "dentista":       dentista_final,
        "clinica":        clinica_final,
        "data_registro":  data_final,
    }, storage_path=storage_path)

    # atualiza odontograma com dentes identificados pela IA
    dentes = resultado.get("dentes_afetados", [])
    if dentes:
        atualizar_odontograma_em_lote(usuario_id, dentes)

    return {
        "registro_id":        registro_id,
        "resumo":             resumo_final,
        "dentes_atualizados": len(dentes),
    }


@router.delete("/registros/{registro_id}")
def excluir_registro(
    registro_id: int,
    usuario_id:  int = Depends(get_usuario_atual)
):
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute(
        "SELECT id FROM registros_odonto WHERE id = %s AND usuario_id = %s",
        (registro_id, usuario_id)
    )
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Registro não encontrado.")

    cursor.execute("DELETE FROM registros_odonto WHERE id = %s", (registro_id,))
    conn.commit()
    conn.close()

    return {"message": "Registro excluído com sucesso."}
