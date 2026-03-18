"""
Router de valores laboratoriais estruturados.
"""

from fastapi import APIRouter, Depends
from typing import List
from core.security import get_usuario_atual
from core.database import get_connection, get_cursor
from models.schemas import ValorLaboratorialResponse

router = APIRouter(prefix="/valores", tags=["Valores Laboratoriais"])


@router.get("/parametros", response_model=List[str])
def listar_parametros(usuario_id: int = Depends(get_usuario_atual)):
    """Retorna lista de parâmetros disponíveis para o usuário."""
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT DISTINCT parametro
        FROM exame_valores
        WHERE usuario_id = %s
        ORDER BY parametro
    """, (usuario_id,))

    rows = cursor.fetchall()
    conn.close()

    return [r["parametro"] for r in rows]


@router.get("/evolucao/{parametro}", response_model=List[ValorLaboratorialResponse])
def evolucao_parametro(
    parametro: str,
    usuario_id: int = Depends(get_usuario_atual)
):
    """Retorna a evolução temporal de um parâmetro."""
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT parametro, valor, unidade, referencia_min, referencia_max,
               status, data_coleta
        FROM exame_valores
        WHERE usuario_id = %s AND parametro ILIKE %s
        ORDER BY data_coleta ASC
    """, (usuario_id, f"%{parametro}%"))

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]


@router.get("/exame/{exame_id}", response_model=List[ValorLaboratorialResponse])
def valores_por_exame(
    exame_id: int,
    usuario_id: int = Depends(get_usuario_atual)
):
    """Retorna todos os valores de um exame específico."""
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT parametro, valor, unidade, referencia_min, referencia_max,
               status, data_coleta
        FROM exame_valores
        WHERE exame_id = %s AND usuario_id = %s
        ORDER BY parametro
    """, (exame_id, usuario_id))

    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]
