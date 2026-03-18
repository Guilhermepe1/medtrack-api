"""
Router de compartilhamento com médico.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from core.security import get_usuario_atual
from models.schemas import LinkMedicoResponse

router = APIRouter(prefix="/compartilhar", tags=["Compartilhar com Médico"])


@router.post("/link", response_model=LinkMedicoResponse)
def gerar_link(
    usuario_id: int = Depends(get_usuario_atual)
):
    from repositories.link_medico_repository import criar_link, listar_links_usuario
    from core.config import settings

    token = criar_link(usuario_id, horas=24)
    links = listar_links_usuario(usuario_id)
    link  = next((l for l in links if l["token"] == token), None)

    return LinkMedicoResponse(
        token=token,
        url=f"{settings.FRONTEND_URL}/medico/{token}",
        expira_em=link["expira_em"],
        acessado_em=link.get("acessado_em"),
        created_at=link["created_at"],
    )


@router.delete("/link")
def revogar_link(usuario_id: int = Depends(get_usuario_atual)):
    from repositories.link_medico_repository import revogar_links
    revogar_links(usuario_id)
    return {"message": "Link revogado com sucesso."}


@router.get("/link/ativo", response_model=LinkMedicoResponse)
def get_link_ativo(usuario_id: int = Depends(get_usuario_atual)):
    from repositories.link_medico_repository import listar_links_usuario
    from datetime import datetime
    from fastapi import HTTPException
    from core.config import settings

    links = listar_links_usuario(usuario_id)
    ativo = next((l for l in links if l["expira_em"] > datetime.now()), None)

    if not ativo:
        raise HTTPException(status_code=404, detail="Nenhum link ativo.")

    return LinkMedicoResponse(
        token=ativo["token"],
        url=f"{settings.FRONTEND_URL}/medico/{ativo['token']}",
        expira_em=ativo["expira_em"],
        acessado_em=ativo.get("acessado_em"),
        created_at=ativo["created_at"],
    )


@router.get("/pdf")
def download_pdf(usuario_id: int = Depends(get_usuario_atual)):
    from services.relatorio_service import gerar_pdf_medico
    from datetime import datetime

    pdf = gerar_pdf_medico(usuario_id)
    nome = f"relatorio_medtrack_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nome}"}
    )


@router.get("/medico/{token}")
def acesso_medico(token: str):
    """Endpoint público — acessado pelo médico via link."""
    from repositories.link_medico_repository import buscar_link_valido, registrar_acesso
    from services.relatorio_service import gerar_pdf_medico
    from fastapi import HTTPException
    from datetime import datetime

    link = buscar_link_valido(token)
    if not link:
        raise HTTPException(status_code=404, detail="Link inválido ou expirado.")

    registrar_acesso(token)
    pdf = gerar_pdf_medico(link["usuario_id"])
    nome = f"relatorio_medtrack_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nome}"}
    )
