"""
Responsável por identificar o tipo de exame.
"""

def classificar_exame(texto):

    texto = texto.lower()

    if any(p in texto for p in [
        "hemoglobina",
        "hematócrito",
        "leucócitos",
        "plaquetas"
    ]):
        return "Hemograma"

    if any(p in texto for p in [
        "colesterol",
        "hdl",
        "ldl",
        "triglicerídeos"
    ]):
        return "Colesterol"

    if any(p in texto for p in [
        "glicose",
        "hemoglobina glicada",
        "hba1c"
    ]):
        return "Diabetes"

    if any(p in texto for p in [
        "ressonância",
        "tomografia",
        "ultrassom"
    ]):
        return "Imagem"

    return "Outros"
