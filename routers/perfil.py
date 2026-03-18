"""
Router do perfil de saúde do usuário.
"""

from fastapi import APIRouter, Depends
from core.security import get_usuario_atual
from models.schemas import PerfilSaudeRequest, PerfilSaudeResponse

router = APIRouter(prefix="/perfil", tags=["Perfil de Saúde"])


@router.get("/", response_model=PerfilSaudeResponse)
def get_perfil(usuario_id: int = Depends(get_usuario_atual)):
    from repositories.perfil_repository import buscar_perfil
    from services.dashboard_service import calcular_imc, calcular_idade

    perfil = buscar_perfil(usuario_id) or {}
    imc_result = calcular_imc(perfil)
    idade      = calcular_idade(perfil)

    return PerfilSaudeResponse(
        **{k: perfil.get(k) for k in PerfilSaudeRequest.model_fields},
        imc=imc_result[0] if imc_result else None,
        idade=idade,
    )


@router.put("/")
def salvar_perfil(
    dados: PerfilSaudeRequest,
    usuario_id: int = Depends(get_usuario_atual)
):
    from repositories.perfil_repository import salvar_perfil
    salvar_perfil(usuario_id, dados.model_dump())
    return {"message": "Perfil atualizado com sucesso."}
