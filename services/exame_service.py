"""
Service responsável pelo fluxo de processamento de exames.
"""


from services.ai_service import resumir_exame
from services.extracao_service import extrair_metadados_e_valores
from services.storage_service import upload_arquivo
from repositories.exame_repository import salvar_exame, buscar_exame_por_nome
from repositories.valores_repository import salvar_valores
from repositories.alertas_repository import salvar_alertas
from rag.vector_store import adicionar_exame
from services.document_reader import extrair_texto_documento
from services.exame_classifier import classificar_exame


def processar_exame(arquivo, usuario_id,
                    nome_exame=None, data_exame=None,
                    medico=None, hospital=None,
                    conteudo=None, texto=None):
    """
    Fluxo completo de processamento de um exame.

    Aceita metadados já confirmados pelo usuário (nome_exame, data_exame,
    medico, hospital) e conteúdo/texto pré-extraídos para evitar
    releitura desnecessária do arquivo.
    """

    # lê conteúdo se não foi passado
    if conteudo is None:
        conteudo = arquivo.read()
        arquivo.seek(0)

    # extrai texto se não foi passado
    if texto is None:
        texto = extrair_texto_documento(arquivo)

    resumo    = resumir_exame(texto)
    categoria = classificar_exame(texto)

    # upload para Supabase Storage
    storage_path = upload_arquivo(usuario_id, arquivo.name, conteudo)

    if not storage_path:
        print("Erro ao salvar arquivo no storage. Tente novamente.")
        return None, texto, resumo, categoria

    # salva metadados no banco
    salvar_exame(
        usuario_id=usuario_id,
        arquivo=arquivo.name,
        texto=texto,
        resumo=resumo,
        categoria=categoria,
        storage_path=storage_path,
        nome_exame=nome_exame,
        data_exame=data_exame,
        medico=medico,
        hospital=hospital
    )

    exame = buscar_exame_por_nome(usuario_id, arquivo.name)

    if exame:
        # usa data_exame confirmada pelo usuário como data de coleta
        resultado  = extrair_metadados_e_valores(texto)
        valores    = resultado.get("valores", [])
        data_coleta = data_exame or resultado.get("data_exame")

        salvar_valores(
            exame_id=exame.id,
            usuario_id=usuario_id,
            data_coleta=data_coleta,
            valores=valores
        )

        salvar_alertas(
            usuario_id=usuario_id,
            exame_id=exame.id,
            valores=valores
        )

        adicionar_exame(usuario_id, exame.id, texto)

    return storage_path, texto, resumo, categoria