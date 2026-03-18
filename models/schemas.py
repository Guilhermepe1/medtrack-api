"""
Schemas Pydantic para validação de request/response da API.
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator
import re


# ── Auth ──

class RegistroRequest(BaseModel):
    nome: str
    username: str
    senha: str
    nome_completo: str
    data_nascimento: date
    cpf: str
    email: EmailStr
    celular: str
    cep: str
    logradouro: str
    numero: str
    complemento: Optional[str] = None
    bairro: str
    cidade: str
    estado: str

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v):
        c = re.sub(r"\D", "", v)
        if len(c) != 11 or len(set(c)) == 1:
            raise ValueError("CPF inválido")
        for i in range(9, 11):
            soma = sum(int(c[j]) * (i + 1 - j) for j in range(i))
            if (soma * 10 % 11) % 10 != int(c[i]):
                raise ValueError("CPF inválido")
        return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}"

    @field_validator("celular")
    @classmethod
    def validar_celular(cls, v):
        c = re.sub(r"\D", "", v)
        if len(c) not in (10, 11) or len(set(c)) == 1:
            raise ValueError("Celular inválido")
        return v

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, v):
        if len(v) < 8:
            raise ValueError("Senha deve ter pelo menos 8 caracteres")
        return v


class LoginRequest(BaseModel):
    username: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario_id: int
    usuario_nome: str


class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str
    confirma_senha: str

    @field_validator("nova_senha")
    @classmethod
    def validar_nova_senha(cls, v):
        if len(v) < 8:
            raise ValueError("Nova senha deve ter pelo menos 8 caracteres")
        return v


# ── Usuário ──

class UsuarioResponse(BaseModel):
    id: int
    nome: str
    username: str
    email: Optional[str] = None
    nome_completo: Optional[str] = None
    data_nascimento: Optional[date] = None
    cpf: Optional[str] = None
    celular: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None


class AtualizarDadosRequest(BaseModel):
    nome_completo: str
    email: EmailStr
    celular: str
    data_nascimento: date
    cep: str
    logradouro: str
    numero: str
    complemento: Optional[str] = None
    bairro: str
    cidade: str
    estado: str

    @field_validator("celular")
    @classmethod
    def validar_celular(cls, v):
        c = re.sub(r"\D", "", v)
        if len(c) not in (10, 11) or len(set(c)) == 1:
            raise ValueError("Celular inválido")
        return v


# ── Exames ──

class ExameResponse(BaseModel):
    id: int
    arquivo: str
    resumo: Optional[str] = None
    categoria: Optional[str] = None
    nome_exame: Optional[str] = None
    data_exame: Optional[date] = None
    data_upload: datetime
    medico: Optional[str] = None
    hospital: Optional[str] = None
    storage_path: Optional[str] = None


class ExameMetadadosRequest(BaseModel):
    nome_exame: Optional[str] = None
    data_exame: Optional[date] = None
    medico: Optional[str] = None
    hospital: Optional[str] = None


# ── Valores laboratoriais ──

class ValorLaboratorialResponse(BaseModel):
    parametro: str
    valor: Optional[float] = None
    unidade: Optional[str] = None
    referencia_min: Optional[float] = None
    referencia_max: Optional[float] = None
    status: Optional[str] = None
    data_coleta: Optional[date] = None


# ── Alertas ──

class AlertaResponse(BaseModel):
    id: int
    parametro: str
    valor: float
    unidade: Optional[str] = None
    referencia_min: Optional[float] = None
    referencia_max: Optional[float] = None
    status: str
    lido: bool
    created_at: datetime
    arquivo: Optional[str] = None


class MarcarLidoRequest(BaseModel):
    alerta_id: int


# ── Perfil de saúde ──

class PerfilSaudeRequest(BaseModel):
    data_nascimento: Optional[date] = None
    sexo: Optional[str] = None
    peso: Optional[float] = None
    altura: Optional[int] = None
    condicoes: Optional[List[str]] = None
    outras_condicoes: Optional[str] = None
    medicamentos: Optional[str] = None
    fumante: Optional[str] = None
    consumo_alcool: Optional[str] = None
    atividade_fisica: Optional[str] = None


class PerfilSaudeResponse(PerfilSaudeRequest):
    imc: Optional[float] = None
    idade: Optional[int] = None


# ── Dashboard ──

class DashboardResponse(BaseModel):
    score: int
    categoria: str
    cor: str
    total_exames: int
    alertas_nao_lidos: int
    imc: Optional[float] = None
    categoria_imc: Optional[str] = None
    idade: Optional[int] = None
    ultimo_exame: Optional[ExameResponse] = None
    recomendacoes: List[dict] = []


# ── Chat ──

class ChatRequest(BaseModel):
    pergunta: str
    historico: Optional[List[dict]] = []


class ChatResponse(BaseModel):
    resposta: str


# ── Compartilhar ──

class LinkMedicoResponse(BaseModel):
    token: str
    url: str
    expira_em: datetime
    acessado_em: Optional[datetime] = None
    created_at: datetime


# ── Odontologia ──

class DenteStatusRequest(BaseModel):
    numero_dente: int
    status: str
    observacao: Optional[str] = None


class RegistroOdontoResponse(BaseModel):
    id: int
    tipo: str
    subtipo: Optional[str] = None
    nome_arquivo: Optional[str] = None
    resumo: Optional[str] = None
    dentista: Optional[str] = None
    clinica: Optional[str] = None
    data_registro: Optional[date] = None
    created_at: datetime
