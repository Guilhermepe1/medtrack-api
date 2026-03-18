from services.pdf_service import extrair_texto_pdf
from services.ocr_service import extrair_texto_imagem


def extrair_texto_documento(arquivo):

    nome = arquivo.name.lower()

    if nome.endswith(".pdf"):
        return extrair_texto_pdf(arquivo)

    elif nome.endswith((".png", ".jpg", ".jpeg")):
        return extrair_texto_imagem(arquivo)

    else:
        raise ValueError("Formato de arquivo não suportado.")
