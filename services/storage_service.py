"""
Service responsável pelo armazenamento de arquivos no Supabase Storage.
"""

import requests
from core.config import settings


SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_SERVICE_KEY
BUCKET = "exames"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

CONTENT_TYPES = {
    "pdf":  "application/pdf",
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "png":  "image/png",
}


def _get_content_type(nome_arquivo: str) -> str:
    extensao = nome_arquivo.rsplit(".", 1)[-1].lower()
    return CONTENT_TYPES.get(extensao, "application/octet-stream")


def upload_arquivo(usuario_id: int, nome_arquivo: str, conteudo: bytes) -> str | None:
    """
    Faz upload do arquivo para o Supabase Storage.
    Retorna o caminho salvo (storage_path) ou None em caso de erro.

    Estrutura no bucket: {usuario_id}/{nome_arquivo}
    """
    storage_path = f"{usuario_id}/{nome_arquivo}"
    content_type = _get_content_type(nome_arquivo)

    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{storage_path}"

    response = requests.post(
        url,
        headers={**HEADERS, "Content-Type": content_type},
        data=conteudo
    )

    if response.status_code in (200, 201):
        return storage_path

    # se arquivo já existe, tenta atualizar
    if response.status_code == 400:
        response = requests.put(
            url,
            headers={**HEADERS, "Content-Type": content_type},
            data=conteudo
        )
        if response.status_code in (200, 201):
            return storage_path

    print(f"Erro no upload: {response.status_code} — {response.text}")
    return None


def gerar_url_temporaria(storage_path: str, expira_em: int = 3600) -> str | None:
    """
    Gera uma URL assinada e temporária para acesso ao arquivo.
    expira_em: tempo em segundos (padrão 1 hora)
    """
    url = f"{SUPABASE_URL}/storage/v1/object/sign/{BUCKET}/{storage_path}"

    response = requests.post(
        url,
        headers=HEADERS,
        json={"expiresIn": expira_em}
    )

    if response.status_code == 200:
        token = response.json().get("signedURL")
        return f"{SUPABASE_URL}/storage/v1{token}"

    print(f"Erro ao gerar URL: {response.status_code} — {response.text}")
    return None


def excluir_arquivo(storage_path: str) -> bool:
    """
    Remove um arquivo do Supabase Storage.
    """
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{storage_path}"

    response = requests.delete(url, headers=HEADERS)

    return response.status_code in (200, 204)
