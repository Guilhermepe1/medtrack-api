"""
Service responsável por OCR (extração de texto de imagens).
"""

import os
import platform
import pytesseract
from PIL import Image


# detecta o caminho do Tesseract por sistema operacional
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Users\Guilherme\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    )
else:
    # Linux (Streamlit Cloud, Ubuntu)
    pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


def extrair_texto_imagem(arquivo):

    imagem = Image.open(arquivo)

    texto = pytesseract.image_to_string(imagem, lang="por+eng")

    return texto