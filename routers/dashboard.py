"""
Router do dashboard de saúde personalizado.
"""

from fastapi import APIRouter, Depends
from core.security import get_usuario_atual
from models.schemas import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/", response_model=DashboardResponse)
def get_dashboard(usuario_id: int = Depends(get_usuario_atual)):
    from services.dashboard_service import (
        calcular_score_saude,
        calcular_imc,
        calcular_idade,
        gerar_recomendacoes,
    )
    from repositories.exame_repository import listar_exames
    from repositories.alertas_repository import buscar_todos_alertas
    from repositories.perfil_repository import buscar_perfil

    score, categoria, cor = calcular_score_saude(usuario_id)
    perfil  = buscar_perfil(usuario_id)
    exames  = listar_exames(usuario_id)
    alertas = buscar_todos_alertas(usuario_id)
    nao_lidos     = [a for a in alertas if not a["lido"]]
    recomendacoes = gerar_recomendacoes(usuario_id)

    imc_result = calcular_imc(perfil)
    idade      = calcular_idade(perfil)

    ultimo_exame = None
    if exames:
        e = exames[0]
        ultimo_exame = {
            "id":           e.id,
            "arquivo":      e.arquivo,
            "resumo":       e.resumo,
            "categoria":    e.categoria,
            "nome_exame":   getattr(e, "nome_exame", None),
            "data_exame":   getattr(e, "data_exame", None),
            "data_upload":  e.data_upload,
            "medico":       getattr(e, "medico", None),
            "hospital":     getattr(e, "hospital", None),
            "storage_path": getattr(e, "storage_path", None),
        }

    return DashboardResponse(
        score=score,
        categoria=categoria,
        cor=cor,
        total_exames=len(exames),
        alertas_nao_lidos=len(nao_lidos),
        imc=imc_result[0] if imc_result else None,
        categoria_imc=imc_result[1] if imc_result else None,
        idade=idade,
        ultimo_exame=ultimo_exame,
        recomendacoes=recomendacoes,
    )
