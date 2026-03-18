"""
Router de conformidade LGPD.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from core.security import get_usuario_atual
from core.database import get_connection, get_cursor
from pydantic import BaseModel

router = APIRouter(prefix="/lgpd", tags=["LGPD"])

VERSAO_ATUAL = "1.0"


# ── Schemas locais ──

class ConsentimentoResponse(BaseModel):
    versao:     str
    aceito:     bool
    created_at: str


class LogResponse(BaseModel):
    acao:       str
    descricao:  str | None = None
    ip:         str | None = None
    created_at: str


class ConsentirRequest(BaseModel):
    aceito: bool


# ── Consentimento ──

@router.get("/consentimento")
def verificar_consentimento(usuario_id: int = Depends(get_usuario_atual)):
    """Verifica se o usuário aceitou o termo na versão atual."""
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT versao, aceito, created_at
        FROM consentimentos
        WHERE usuario_id = %s AND versao = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (usuario_id, VERSAO_ATUAL))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"consentiu": False, "versao": VERSAO_ATUAL}

    return {
        "consentiu":  row["aceito"],
        "versao":     row["versao"],
        "created_at": str(row["created_at"]),
    }


@router.post("/consentimento")
def registrar_consentimento(
    dados:      ConsentirRequest,
    usuario_id: int = Depends(get_usuario_atual)
):
    """Registra o aceite ou recusa do termo de consentimento."""
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO consentimentos (usuario_id, versao, aceito)
        VALUES (%s, %s, %s)
    """, (usuario_id, VERSAO_ATUAL, dados.aceito))

    conn.commit()
    conn.close()

    return {"message": "Consentimento registrado.", "aceito": dados.aceito}


# ── Logs de acesso ──

@router.get("/logs", response_model=List[LogResponse])
def listar_logs(usuario_id: int = Depends(get_usuario_atual)):
    """Retorna os logs de acesso do usuário."""
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT acao, descricao, ip, created_at
        FROM logs_acesso
        WHERE usuario_id = %s
        ORDER BY created_at DESC
        LIMIT 50
    """, (usuario_id,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


@router.post("/log")
def registrar_log(
    acao:       str,
    descricao:  str | None = None,
    usuario_id: int = Depends(get_usuario_atual)
):
    """Registra uma ação do usuário nos logs."""
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO logs_acesso (usuario_id, acao, descricao)
        VALUES (%s, %s, %s)
    """, (usuario_id, acao, descricao))

    conn.commit()
    conn.close()

    return {"message": "Log registrado."}


# ── Direito ao esquecimento ──

@router.delete("/excluir-conta")
def excluir_conta(usuario_id: int = Depends(get_usuario_atual)):
    """
    Remove todos os dados do usuário permanentemente (Art. 18 LGPD).
    A exclusão em cascata cuida de todas as tabelas relacionadas.
    """
    conn   = get_connection()
    cursor = get_cursor(conn)

    # registra o log antes de deletar
    cursor.execute("""
        INSERT INTO logs_acesso (usuario_id, acao, descricao)
        VALUES (%s, 'solicitou_exclusao_conta',
                'Usuário solicitou exclusão completa de dados (LGPD Art. 18)')
    """, (usuario_id,))

    # deleta o usuário — ON DELETE CASCADE remove tudo
    cursor.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))

    conn.commit()
    conn.close()

    return {"message": "Conta e todos os dados excluídos permanentemente."}
