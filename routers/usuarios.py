"""
Router de dados cadastrais do usuário.
"""

from fastapi import APIRouter, Depends, HTTPException
from core.security import get_usuario_atual
from core.database import get_connection, get_cursor
from models.schemas import UsuarioResponse, AtualizarDadosRequest
import re

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.get("/me", response_model=UsuarioResponse)
def get_meus_dados(usuario_id: int = Depends(get_usuario_atual)):
    """Retorna os dados cadastrais completos do usuário logado."""
    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT id, nome, username, email, nome_completo, data_nascimento,
               cpf, celular, cep, logradouro, numero, complemento,
               bairro, cidade, estado
        FROM usuarios
        WHERE id = %s
    """, (usuario_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    return dict(row)


@router.put("/me", response_model=UsuarioResponse)
def atualizar_meus_dados(
    dados: AtualizarDadosRequest,
    usuario_id: int = Depends(get_usuario_atual)
):
    """Atualiza os dados cadastrais do usuário logado."""
    conn   = get_connection()
    cursor = get_cursor(conn)

    # verifica se e-mail já pertence a outro usuário
    cursor.execute(
        "SELECT id FROM usuarios WHERE email = %s AND id != %s",
        (dados.email, usuario_id)
    )
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")

    # formata celular
    cel_limpo = re.sub(r"\D", "", dados.celular)
    if len(cel_limpo) == 11:
        celular_fmt = f"({cel_limpo[:2]}) {cel_limpo[2:7]}-{cel_limpo[7:]}"
    elif len(cel_limpo) == 10:
        celular_fmt = f"({cel_limpo[:2]}) {cel_limpo[2:6]}-{cel_limpo[6:]}"
    else:
        raise HTTPException(status_code=400, detail="Celular inválido.")

    cursor.execute("""
        UPDATE usuarios SET
            nome_completo   = %s,
            email           = %s,
            celular         = %s,
            data_nascimento = %s,
            cep             = %s,
            logradouro      = %s,
            numero          = %s,
            complemento     = %s,
            bairro          = %s,
            cidade          = %s,
            estado          = %s
        WHERE id = %s
    """, (
        dados.nome_completo,
        dados.email,
        celular_fmt,
        str(dados.data_nascimento),
        re.sub(r"\D", "", dados.cep),
        dados.logradouro,
        dados.numero,
        dados.complemento,
        dados.bairro,
        dados.cidade,
        dados.estado,
        usuario_id,
    ))

    conn.commit()

    # retorna dados atualizados
    cursor.execute("""
        SELECT id, nome, username, email, nome_completo, data_nascimento,
               cpf, celular, cep, logradouro, numero, complemento,
               bairro, cidade, estado
        FROM usuarios WHERE id = %s
    """, (usuario_id,))

    row = cursor.fetchone()
    conn.close()

    return dict(row)
