"""
Router de autenticação — registro, login, OAuth Google.
"""

from fastapi import APIRouter, HTTPException, status
from core.security import hash_senha, verificar_senha, criar_token, get_usuario_atual
from core.database import get_connection, get_cursor
from models.schemas import RegistroRequest, LoginRequest, TokenResponse, AlterarSenhaRequest
from fastapi import Depends
import re

router = APIRouter(prefix="/auth", tags=["Autenticação"])


def _buscar_usuario_por_username(username: str):
    conn   = get_connection()
    cursor = get_cursor(conn)
    cursor.execute(
        "SELECT id, nome, username, senha FROM usuarios WHERE username = %s",
        (username,)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def _buscar_usuario_por_email(email: str):
    conn   = get_connection()
    cursor = get_cursor(conn)
    cursor.execute(
        "SELECT id FROM usuarios WHERE email = %s", (email,)
    )
    row = cursor.fetchone()
    conn.close()
    return row


def _buscar_usuario_por_cpf(cpf: str):
    conn   = get_connection()
    cursor = get_cursor(conn)
    cursor.execute(
        "SELECT id FROM usuarios WHERE cpf = %s", (cpf,)
    )
    row = cursor.fetchone()
    conn.close()
    return row


@router.post("/register", status_code=status.HTTP_201_CREATED)
def registrar(dados: RegistroRequest):

    if _buscar_usuario_por_username(dados.username):
        raise HTTPException(
            status_code=400, detail="Username já está em uso."
        )

    if _buscar_usuario_por_email(dados.email):
        raise HTTPException(
            status_code=400, detail="E-mail já cadastrado."
        )

    if _buscar_usuario_por_cpf(dados.cpf):
        raise HTTPException(
            status_code=400, detail="CPF já cadastrado."
        )

    senha_hash = hash_senha(dados.senha)

    conn   = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO usuarios (
            nome, username, senha,
            nome_completo, data_nascimento, cpf, email, celular,
            cep, logradouro, numero, complemento, bairro, cidade, estado
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (
        dados.username, dados.username, senha_hash,
        dados.nome_completo, str(dados.data_nascimento), dados.cpf,
        dados.email, dados.celular, dados.cep, dados.logradouro,
        dados.numero, dados.complemento, dados.bairro,
        dados.cidade, dados.estado
    ))

    row = cursor.fetchone()
    conn.commit()
    conn.close()

    return {"message": "Usuário criado com sucesso.", "usuario_id": row["id"]}


@router.post("/login", response_model=TokenResponse)
def login(dados: LoginRequest):

    usuario = _buscar_usuario_por_username(dados.username)

    if not usuario or not usuario.get("senha"):
        raise HTTPException(
            status_code=401, detail="Usuário ou senha inválidos."
        )

    if not verificar_senha(dados.senha, usuario["senha"]):
        raise HTTPException(
            status_code=401, detail="Usuário ou senha inválidos."
        )

    token = criar_token({"sub": str(usuario["id"])})

    return TokenResponse(
        access_token=token,
        usuario_id=usuario["id"],
        usuario_nome=usuario["nome"]
    )


@router.post("/alterar-senha")
def alterar_senha(
    dados: AlterarSenhaRequest,
    usuario_id: int = Depends(get_usuario_atual)
):
    if dados.nova_senha != dados.confirma_senha:
        raise HTTPException(status_code=400, detail="As senhas não coincidem.")

    conn   = get_connection()
    cursor = get_cursor(conn)
    cursor.execute("SELECT senha FROM usuarios WHERE id = %s", (usuario_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not verificar_senha(dados.senha_atual, row["senha"]):
        raise HTTPException(status_code=401, detail="Senha atual incorreta.")

    nova_hash = hash_senha(dados.nova_senha)
    conn   = get_connection()
    cursor = get_cursor(conn)
    cursor.execute(
        "UPDATE usuarios SET senha = %s WHERE id = %s",
        (nova_hash, usuario_id)
    )
    conn.commit()
    conn.close()

    return {"message": "Senha alterada com sucesso."}
