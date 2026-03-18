"""
Router de alertas clínicos.
"""

from fastapi import APIRouter, Depends
from typing import List
from core.security import get_usuario_atual
from models.schemas import AlertaResponse

router = APIRouter(prefix="/alertas", tags=["Alertas"])


@router.get("/", response_model=List[AlertaResponse])
def listar_alertas(usuario_id: int = Depends(get_usuario_atual)):
    from repositories.alertas_repository import buscar_todos_alertas
    alertas = buscar_todos_alertas(usuario_id)
    return [dict(a) for a in alertas]


@router.patch("/{alerta_id}/lido")
def marcar_lido(
    alerta_id: int,
    usuario_id: int = Depends(get_usuario_atual)
):
    from repositories.alertas_repository import marcar_alerta_lido
    marcar_alerta_lido(alerta_id)
    return {"message": "Alerta marcado como lido."}


@router.patch("/lidos/todos")
def marcar_todos_lidos(usuario_id: int = Depends(get_usuario_atual)):
    from repositories.alertas_repository import marcar_todos_lidos
    marcar_todos_lidos(usuario_id)
    return {"message": "Todos os alertas marcados como lidos."}
