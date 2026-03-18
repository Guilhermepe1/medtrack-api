"""
Repository responsável pelo perfil de saúde do usuário.
"""

from database.db import get_connection, get_cursor


def buscar_perfil(usuario_id):
    """
    Retorna o perfil de saúde do usuário ou None se não preenchido.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        SELECT
            data_nascimento, sexo, peso, altura,
            condicoes, outras_condicoes,
            medicamentos,
            fumante, consumo_alcool, atividade_fisica
        FROM perfil_saude
        WHERE usuario_id = %s
    """, (usuario_id,))

    row = cursor.fetchone()
    conn.close()

    return row


def salvar_perfil(usuario_id, dados):
    """
    Cria ou atualiza o perfil de saúde do usuário (upsert).
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
        INSERT INTO perfil_saude (
            usuario_id, data_nascimento, sexo, peso, altura,
            condicoes, outras_condicoes, medicamentos,
            fumante, consumo_alcool, atividade_fisica,
            updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (usuario_id) DO UPDATE SET
            data_nascimento  = EXCLUDED.data_nascimento,
            sexo             = EXCLUDED.sexo,
            peso             = EXCLUDED.peso,
            altura           = EXCLUDED.altura,
            condicoes        = EXCLUDED.condicoes,
            outras_condicoes = EXCLUDED.outras_condicoes,
            medicamentos     = EXCLUDED.medicamentos,
            fumante          = EXCLUDED.fumante,
            consumo_alcool   = EXCLUDED.consumo_alcool,
            atividade_fisica = EXCLUDED.atividade_fisica,
            updated_at       = NOW()
    """, (
        usuario_id,
        dados.get("data_nascimento"),
        dados.get("sexo"),
        dados.get("peso"),
        dados.get("altura"),
        dados.get("condicoes", []),
        dados.get("outras_condicoes"),
        dados.get("medicamentos"),
        dados.get("fumante"),
        dados.get("consumo_alcool"),
        dados.get("atividade_fisica"),
    ))

    conn.commit()
    conn.close()


def perfil_para_contexto(usuario_id):
    """
    Retorna o perfil formatado em texto para ser usado como
    contexto do sistema no chat de IA.
    """
    perfil = buscar_perfil(usuario_id)

    if not perfil:
        return ""

    from datetime import date
    linhas = ["=== Perfil do paciente ==="]

    if perfil["data_nascimento"]:
        hoje  = date.today()
        nasc  = perfil["data_nascimento"]
        idade = hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
        linhas.append(f"Idade: {idade} anos")

    if perfil["sexo"]:
        linhas.append(f"Sexo: {perfil['sexo']}")

    if perfil["peso"] and perfil["altura"]:
        imc = round(float(perfil["peso"]) / ((perfil["altura"] / 100) ** 2), 1)
        linhas.append(f"Peso: {perfil['peso']} kg | Altura: {perfil['altura']} cm | IMC: {imc}")
    elif perfil["peso"]:
        linhas.append(f"Peso: {perfil['peso']} kg")
    elif perfil["altura"]:
        linhas.append(f"Altura: {perfil['altura']} cm")

    condicoes = perfil["condicoes"] or []
    if perfil["outras_condicoes"]:
        condicoes = list(condicoes) + [perfil["outras_condicoes"]]
    if condicoes:
        linhas.append(f"Condições de saúde: {', '.join(condicoes)}")

    if perfil["medicamentos"]:
        linhas.append(f"Medicamentos em uso: {perfil['medicamentos']}")

    habitos = []
    if perfil["fumante"] and perfil["fumante"] != "Não":
        habitos.append(f"fumante ({perfil['fumante'].lower()})")
    if perfil["consumo_alcool"] and perfil["consumo_alcool"] != "Não consome":
        habitos.append(f"consome álcool ({perfil['consumo_alcool'].lower()})")
    if perfil["atividade_fisica"]:
        habitos.append(f"atividade física: {perfil['atividade_fisica'].lower()}")
    if habitos:
        linhas.append(f"Hábitos: {', '.join(habitos)}")

    linhas.append("=========================")

    return "\n".join(linhas)