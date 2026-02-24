from __future__ import annotations

from datetime import datetime

from app.pdf.report_engine import generate_report_pdf


KPI_LABELS = {
    "families_attended": "Famílias atendidas",
    "people_followed": "Pessoas acompanhadas",
    "children_count": "Total crianças",
    "deliveries_count": "Total cestas/entregas",
    "referrals_count": "Encaminhamentos",
    "visits_count": "Visitas",
    "loans_count": "Empréstimos",
    "pending_docs_count": "Pendências documentais",
    "pending_visits_count": "Pendências de visita",
    "avg_vulnerability": "Vulnerabilidade média",
}


def _mom_rows(snapshot_official: dict) -> list[list[object]]:
    mom = snapshot_official.get("mom", {})
    rows: list[list[object]] = []
    for key in (
        "families_attended",
        "people_followed",
        "children_count",
        "deliveries_count",
        "referrals_count",
        "visits_count",
        "loans_count",
        "pending_docs_count",
        "pending_visits_count",
        "avg_vulnerability",
    ):
        item = mom.get(key, {})
        rows.append(
            [
                KPI_LABELS.get(key, key),
                item.get("current", "-"),
                item.get("previous", "-"),
                item.get("absolute", "N/A"),
                item.get("percent", "N/A"),
            ]
        )
    return rows


def render_official_monthly_pdf(snapshot_official: dict, signature: dict, metadata: dict) -> bytes:
    totals = snapshot_official.get("totals", {})
    indicators = snapshot_official.get("indicators", {})

    avg_vulnerability = indicators.get("avg_vulnerability")
    if avg_vulnerability is None:
        vulnerability_value = "Não disponível (sem base de vulnerabilidade no snapshot de fechamento)."
    else:
        vulnerability_value = avg_vulnerability

    summary_rows = [
        ["Total famílias atendidas", totals.get("families_attended", 0)],
        ["Total pessoas acompanhadas", totals.get("people_followed", 0)],
        ["Total crianças", totals.get("children_count", 0)],
        ["Total cestas", totals.get("deliveries_count", 0)],
        ["Total encaminhamentos", totals.get("referrals_count", 0)],
        ["Total visitas", totals.get("visits_count", 0)],
        ["Total empréstimos", totals.get("loans_count", 0)],
    ]

    pending_rows = [
        ["Documentação", indicators.get("pending_docs_count", 0)],
        ["Visita", indicators.get("pending_visits_count", 0)],
    ]
    for item in indicators.get("other_pending", []) or []:
        pending_rows.append([str(item.get("label", "Outras")), item.get("value", 0)])

    neighborhood_rows = [
        [
            item.get("neighborhood", "Não informado"),
            item.get("families", 0),
            item.get("deliveries", 0),
            item.get("pending", "-"),
        ]
        for item in snapshot_official.get("by_neighborhood", [])
    ]

    sections = [
        {
            "type": "table",
            "title": "1️⃣ Resumo Executivo",
            "headers": ["Indicador", "Valor"],
            "rows": summary_rows,
        },
        {
            "type": "table",
            "title": "2️⃣ Indicadores Sociais",
            "headers": ["Indicador", "Valor"],
            "rows": [["Vulnerabilidade média", vulnerability_value]],
        },
        {
            "type": "table",
            "title": "Pendências",
            "headers": ["Tipo", "Quantidade"],
            "rows": pending_rows,
        },
        {
            "type": "table",
            "title": "3️⃣ Distribuição por Bairro",
            "headers": ["Bairro", "Famílias atendidas", "Entregas", "Pendências"],
            "rows": neighborhood_rows,
        },
        {
            "type": "table",
            "title": "4️⃣ Evolução comparativa com mês anterior",
            "headers": ["KPI", "Mês atual", "Mês anterior", "Δ absoluto", "Δ %"],
            "rows": _mom_rows(snapshot_official),
        },
        {
            "type": "text",
            "title": "5️⃣ Assinatura digital administrativa",
            "content": (
                f"Assinado por: {signature.get('name')} (user_id={signature.get('user_id')}). "
                f"Data: {signature.get('signed_at')}. "
                "Assinatura digital simples registrada em base administrativa."
            ),
        },
    ]

    return generate_report_pdf(
        title="Relatório Mensal Consolidado Oficial",
        month=int(metadata.get("month")),
        year=int(metadata.get("year")),
        sections=sections,
        metadata={
            "generated_by": metadata.get("generated_by", "Sistema"),
            "generated_at": metadata.get("generated_at", datetime.now()),
            "institution": metadata.get("institution"),
        },
    )
