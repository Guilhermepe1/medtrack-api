"""
Service responsável pela geração do PDF de relatório médico
para compartilhamento via link temporário.
"""

import io
from datetime import date, datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable,
)

from repositories.usuario_repository import buscar_dados_completos
from repositories.exame_repository import listar_exames
from repositories.perfil_repository import buscar_perfil

COR_PRIMARIA = colors.HexColor("#1A2A6C")
COR_TEAL     = colors.HexColor("#00C9A7")
COR_CINZA    = colors.HexColor("#6B8CB0")
COR_FUNDO    = colors.HexColor("#F4F8FC")


def _calcular_idade(data_nasc):
    if not data_nasc:
        return None
    hoje = date.today()
    nasc = data_nasc if isinstance(data_nasc, date) else \
           datetime.strptime(str(data_nasc)[:10], "%Y-%m-%d").date()
    return hoje.year - nasc.year - (
        (hoje.month, hoje.day) < (nasc.month, nasc.day)
    )


def _fmt_data(d):
    if not d:
        return "—"
    try:
        return datetime.strptime(str(d)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(d)[:10]


def gerar_pdf_medico(usuario_id):
    """
    Gera PDF do relatório médico. Retorna bytes.
    """
    dados  = buscar_dados_completos(usuario_id)
    exames = listar_exames(usuario_id)
    perfil = buscar_perfil(usuario_id)

    buf    = io.BytesIO()
    doc    = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="Relatório Médico — MedTrack",
    )

    styles = getSampleStyleSheet()

    s_titulo = ParagraphStyle("s_titulo", parent=styles["Title"],
        fontSize=20, textColor=COR_PRIMARIA, fontName="Helvetica-Bold", spaceAfter=4)
    s_sub    = ParagraphStyle("s_sub",    parent=styles["Normal"],
        fontSize=11, textColor=COR_CINZA, spaceAfter=14)
    s_secao  = ParagraphStyle("s_secao",  parent=styles["Heading2"],
        fontSize=13, textColor=COR_PRIMARIA, fontName="Helvetica-Bold",
        spaceBefore=16, spaceAfter=8)
    s_corpo  = ParagraphStyle("s_corpo",  parent=styles["Normal"],
        fontSize=10, textColor=COR_PRIMARIA, spaceAfter=6, leading=14)
    s_aviso  = ParagraphStyle("s_aviso",  parent=styles["Normal"],
        fontSize=9, textColor=COR_CINZA, spaceAfter=4, leading=13)
    s_resumo = ParagraphStyle("s_resumo", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#4A6B8C"),
        leftIndent=0.3*cm, spaceAfter=10, leading=13)

    story = []

    # ── Cabeçalho ──
    story.append(Paragraph("MedTrack Health AI", s_titulo))
    story.append(Paragraph("Relatório de Saúde do Paciente", s_sub))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=COR_TEAL, spaceAfter=10))
    story.append(Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}  "
        f"| Válido por 24 horas", s_aviso))
    story.append(Paragraph(
        "Este documento foi gerado automaticamente pelo MedTrack Health AI "
        "e não substitui avaliação médica profissional.", s_aviso))
    story.append(Spacer(1, 0.3*cm))

    # ── Dados do paciente ──
    story.append(Paragraph("Dados do Paciente", s_secao))

    nome  = dados.get("nome_completo") or dados.get("nome") or "—"
    idade = _calcular_idade(dados.get("data_nascimento"))
    end   = " ".join(filter(None, [
        dados.get("logradouro"), dados.get("numero"),
        dados.get("complemento")
    ])) or "—"
    cid_est = "/".join(filter(None, [
        dados.get("cidade"), dados.get("estado")
    ])) or "—"

    grid_dados = [
        ["Nome completo",   nome,
         "Data de nascimento", _fmt_data(dados.get("data_nascimento"))],
        ["Idade",           f"{idade} anos" if idade else "—",
         "CPF",             dados.get("cpf") or "—"],
        ["E-mail",          dados.get("email") or "—",
         "Celular",         dados.get("celular") or "—"],
        ["Endereço",        end,
         "Cidade/Estado",   cid_est],
    ]

    t_dados = Table(grid_dados, colWidths=[3.5*cm, 6.5*cm, 3.5*cm, 3.5*cm])
    t_dados.setStyle(TableStyle([
        ("FONTNAME",       (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",       (0,0), (-1,-1), 9),
        ("FONTNAME",       (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",       (2,0), (2,-1), "Helvetica-Bold"),
        ("TEXTCOLOR",      (0,0), (0,-1), COR_CINZA),
        ("TEXTCOLOR",      (2,0), (2,-1), COR_CINZA),
        ("TEXTCOLOR",      (1,0), (1,-1), COR_PRIMARIA),
        ("TEXTCOLOR",      (3,0), (3,-1), COR_PRIMARIA),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, COR_FUNDO]),
        ("GRID",           (0,0), (-1,-1), 0.3,
                           colors.HexColor("#E0EAF5")),
        ("PADDING",        (0,0), (-1,-1), 6),
        ("VALIGN",         (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(t_dados)

    # ── Perfil de saúde ──
    if perfil:
        story.append(Paragraph("Perfil de Saúde", s_secao))
        linhas = []

        conds = list(perfil.get("condicoes") or [])
        if perfil.get("outras_condicoes"):
            conds.append(perfil["outras_condicoes"])
        if conds:
            linhas.append(["Condições", ", ".join(conds)])

        if perfil.get("medicamentos"):
            linhas.append(["Medicamentos", perfil["medicamentos"]])

        hab = []
        if perfil.get("fumante") and perfil["fumante"] != "Não":
            hab.append(f"Tabagismo: {perfil['fumante']}")
        if perfil.get("consumo_alcool") and perfil["consumo_alcool"] != "Não consome":
            hab.append(f"Álcool: {perfil['consumo_alcool']}")
        if perfil.get("atividade_fisica"):
            hab.append(f"Atividade física: {perfil['atividade_fisica']}")
        if hab:
            linhas.append(["Hábitos", " | ".join(hab)])

        if perfil.get("peso") and perfil.get("altura"):
            imc = round(
                float(perfil["peso"]) / ((float(perfil["altura"]) / 100) ** 2), 1
            )
            linhas.append(["IMC",
                f"{imc} kg/m²  (Peso: {perfil['peso']} kg | "
                f"Altura: {perfil['altura']} cm)"])

        if linhas:
            t_perf = Table(linhas, colWidths=[3.5*cm, 13.5*cm])
            t_perf.setStyle(TableStyle([
                ("FONTNAME",       (0,0), (-1,-1), "Helvetica"),
                ("FONTSIZE",       (0,0), (-1,-1), 9),
                ("FONTNAME",       (0,0), (0,-1), "Helvetica-Bold"),
                ("TEXTCOLOR",      (0,0), (0,-1), COR_CINZA),
                ("TEXTCOLOR",      (1,0), (1,-1), COR_PRIMARIA),
                ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, COR_FUNDO]),
                ("GRID",           (0,0), (-1,-1), 0.3,
                                   colors.HexColor("#E0EAF5")),
                ("PADDING",        (0,0), (-1,-1), 7),
                ("VALIGN",         (0,0), (-1,-1), "TOP"),
            ]))
            story.append(t_perf)
        else:
            story.append(Paragraph("Perfil não preenchido.", s_corpo))

    # ── Exames ──
    story.append(Paragraph("Histórico de Exames", s_secao))

    if not exames:
        story.append(Paragraph("Nenhum exame cadastrado.", s_corpo))
    else:
        for exame in exames:
            nome_e = exame.nome_exame or exame.arquivo
            data_e = _fmt_data(exame.data_exame or exame.data_upload[:10])
            med_e  = exame.medico   or "—"
            hosp_e = exame.hospital or "—"

            cab = [[
                Paragraph(f"<b>{nome_e}</b>", s_corpo),
                Paragraph(f"Data: {data_e}", s_corpo),
                Paragraph(f"Médico: {med_e}", s_corpo),
                Paragraph(f"Local: {hosp_e}", s_corpo),
            ]]
            t_cab = Table(cab, colWidths=[5*cm, 3.5*cm, 4*cm, 4.5*cm])
            t_cab.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1),
                               colors.HexColor("#E8EBF8")),
                ("PADDING",    (0,0), (-1,-1), 6),
                ("GRID",       (0,0), (-1,-1), 0, colors.white),
            ]))
            story.append(t_cab)
            story.append(Paragraph(exame.resumo or "Sem resumo.", s_resumo))

    # ── Rodapé ──
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=1,
                             color=COR_TEAL, spaceAfter=8))
    story.append(Paragraph(
        "MedTrack Health AI — As informações deste relatório foram fornecidas "
        "pelo paciente e interpretadas por inteligência artificial. "
        "Não substitui avaliação médica profissional.", s_aviso))

    doc.build(story)
    buf.seek(0)
    return buf.read()
