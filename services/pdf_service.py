import fitz


def extrair_texto_pdf(arquivo_pdf):

    try:

        arquivo_pdf.seek(0)

        pdf = fitz.open(stream=arquivo_pdf.read(), filetype="pdf")

        texto = ""

        for pagina in pdf:
            texto += pagina.get_text()

        return texto

    except Exception as e:

        print("Erro ao ler PDF:", e)

        return ""
