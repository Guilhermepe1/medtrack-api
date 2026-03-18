"""
Service responsável pelo cálculo do score de saúde e recomendações do dashboard.
"""

from datetime import date, datetime
from repositories.alertas_repository import buscar_todos_alertas
from repositories.exame_repository import listar_exames
from repositories.valores_repository import buscar_parametros_disponiveis, buscar_evolucao_parametro
from repositories.perfil_repository import buscar_perfil


def calcular_score_saude(usuario_id):
    """
    Calcula um score de saúde de 0 a 100 baseado em:
    - Alertas ativos (-15 por alto, -10 por baixo)
    - Tempo desde o último exame (-5 por mês sem exame, até -30)
    - Perfil preenchido (+10)
    - Exames cadastrados (+10 se tiver 3+)
    Retorna: (score, categoria, cor)
    """
    score = 100
    alertas = buscar_todos_alertas(usuario_id)
    nao_lidos = [a for a in alertas if not a["lido"]]

    for alerta in nao_lidos:
        if alerta["status"] == "alto":
            score -= 15
        elif alerta["status"] == "baixo":
            score -= 10

    exames = listar_exames(usuario_id)
    if exames:
        ultimo = exames[0]
        data_ref = ultimo.data_exame or ultimo.data_upload[:10]
        try:
            data_ultimo = datetime.strptime(data_ref, "%Y-%m-%d").date()
            meses_sem_exame = (date.today() - data_ultimo).days // 30
            score -= min(meses_sem_exame * 5, 30)
        except Exception:
            pass

        if len(exames) >= 3:
            score += 10
    else:
        score -= 20

    perfil = buscar_perfil(usuario_id)
    if perfil and perfil.get("data_nascimento") and perfil.get("peso"):
        score += 10

    score = max(0, min(100, score))

    if score >= 80:
        return score, "Ótimo", "#00C9A7"
    elif score >= 60:
        return score, "Bom", "#2B7FD4"
    elif score >= 40:
        return score, "Atenção", "#F5A623"
    else:
        return score, "Crítico", "#E84545"


def calcular_imc(perfil):
    """Retorna (imc, categoria) ou None se dados insuficientes."""
    if not perfil or not perfil.get("peso") or not perfil.get("altura"):
        return None
    try:
        peso   = float(perfil["peso"])
        altura = float(perfil["altura"]) / 100
        imc    = round(peso / (altura ** 2), 1)
        if imc < 18.5:
            cat = "Abaixo do peso"
        elif imc < 25:
            cat = "Peso normal"
        elif imc < 30:
            cat = "Sobrepeso"
        else:
            cat = "Obesidade"
        return imc, cat
    except Exception:
        return None


def calcular_idade(perfil):
    """Retorna idade em anos ou None."""
    if not perfil or not perfil.get("data_nascimento"):
        return None
    try:
        nasc  = perfil["data_nascimento"]
        hoje  = date.today()
        return hoje.year - nasc.year - (
            (hoje.month, hoje.day) < (nasc.month, nasc.day)
        )
    except Exception:
        return None


def gerar_recomendacoes(usuario_id):
    """
    Gera recomendações personalizadas baseadas no histórico do usuário.
    Retorna lista de dicts com {icone, texto, prioridade}.
    """
    recomendacoes = []
    exames  = listar_exames(usuario_id)
    alertas = buscar_todos_alertas(usuario_id)
    perfil  = buscar_perfil(usuario_id)
    nao_lidos = [a for a in alertas if not a["lido"]]

    # alertas não resolvidos
    if nao_lidos:
        params = list({a["parametro"] for a in nao_lidos})[:3]
        recomendacoes.append({
            "icone": "⚠️",
            "texto": f"Você tem {len(nao_lidos)} alerta(s) clínico(s) não lido(s): "
                     f"{', '.join(params)}. Consulte um médico.",
            "prioridade": 1
        })

    # tempo sem exame
    if exames:
        ultimo    = exames[0]
        data_ref  = ultimo.data_exame or ultimo.data_upload[:10]
        try:
            data_ultimo = datetime.strptime(data_ref, "%Y-%m-%d").date()
            dias        = (date.today() - data_ultimo).days
            if dias > 365:
                recomendacoes.append({
                    "icone": "📅",
                    "texto": f"Seu último exame foi há {dias // 30} meses. "
                             "Considere fazer um check-up completo.",
                    "prioridade": 2
                })
            elif dias > 180:
                recomendacoes.append({
                    "icone": "📅",
                    "texto": f"Seu último exame foi há {dias // 30} meses. "
                             "Que tal agendar um novo hemograma?",
                    "prioridade": 3
                })
        except Exception:
            pass
    else:
        recomendacoes.append({
            "icone": "📤",
            "texto": "Você ainda não tem exames cadastrados. "
                     "Faça upload do seu primeiro exame!",
            "prioridade": 1
        })

    # perfil incompleto
    if not perfil or not perfil.get("data_nascimento"):
        recomendacoes.append({
            "icone": "👤",
            "texto": "Complete seu perfil de saúde para respostas mais personalizadas da IA.",
            "prioridade": 4
        })

    # IMC fora do normal
    imc_result = calcular_imc(perfil)
    if imc_result:
        imc, cat = imc_result
        if cat in ("Sobrepeso", "Obesidade"):
            recomendacoes.append({
                "icone": "⚖️",
                "texto": f"Seu IMC é {imc} ({cat}). "
                         "Considere orientação nutricional e atividade física regular.",
                "prioridade": 3
            })
        elif cat == "Abaixo do peso":
            recomendacoes.append({
                "icone": "⚖️",
                "texto": f"Seu IMC é {imc} ({cat}). "
                         "Considere avaliação com nutricionista.",
                "prioridade": 3
            })

    return sorted(recomendacoes, key=lambda x: x["prioridade"])


def buscar_melhor_parametro_grafico(usuario_id):
    """
    Retorna o parâmetro com mais pontos de dados para exibir no gráfico.
    """
    parametros = buscar_parametros_disponiveis(usuario_id)
    if not parametros:
        return None, []

    melhor_param = None
    melhor_dados = []

    for p in parametros:
        dados = buscar_evolucao_parametro(usuario_id, p)
        dados_validos = [d for d in dados if d["valor"] is not None
                         and d["data_coleta"] is not None]
        if len(dados_validos) > len(melhor_dados):
            melhor_param = p
            melhor_dados = dados_validos

    return melhor_param, melhor_dados
