from __future__ import annotations

from datetime import datetime

from app.pdf.report_engine import generate_report_pdf


def _table_from_mapping(data: dict[str, int]) -> list[list[object]]:
    return [[key, value] for key, value in sorted(data.items(), key=lambda item: item[0])]


def render_monthly_closure_pdf(snapshot: dict, metadata: dict) -> bytes:
    totals = snapshot.get("totals", {})
    breakdowns = snapshot.get("breakdowns", {})
    month = int(metadata.get("month"))
    year = int(metadata.get("year"))

    totals_rows = [
        ["Famílias atendidas", totals.get("families_attended", 0)],
        ["Entregas confirmadas", totals.get("deliveries_count", 0)],
        ["Crianças alcançadas", totals.get("children_count", 0)],
        ["Encaminhamentos", totals.get("referrals_count", {}).get("total", 0)],
        ["Visitas", totals.get("visits_count", 0)],
        ["Empréstimos", totals.get("equipment_loans_count", 0)],
        ["Devoluções", totals.get("equipment_returns_count", 0)],
        ["Pendências documentais", totals.get("pending_docs_count", 0)],
        ["Visitas pendentes", totals.get("pending_visits_count", 0)],
    ]

    by_neighborhood = breakdowns.get("by_neighborhood", [])
    neighborhood_rows = [
        [item.get("neighborhood"), item.get("families", 0), item.get("deliveries", 0)]
        for item in by_neighborhood
    ]

    referral_rows = _table_from_mapping(breakdowns.get("referrals_by_type", {}))
    equipment_rows = _table_from_mapping(breakdowns.get("equipment_status_summary", {}))
    pending_rows = [
        ["Pendências documentais", totals.get("pending_docs_count", 0)],
        ["Visitas pendentes", totals.get("pending_visits_count", 0)],
    ]

    sections = [
        {
            "type": "text",
            "title": "Resumo executivo",
            "content": (
                "Fechamento oficial mensal consolidado com snapshot contábil/social. "
                "Após o fechamento, alterações retroativas do mês são bloqueadas."
            ),
        },
        {"type": "table", "title": "Totais", "headers": ["Indicador", "Valor"], "rows": totals_rows},
        {
            "type": "table",
            "title": "Distribuição por bairro",
            "headers": ["Bairro", "Famílias", "Entregas"],
            "rows": neighborhood_rows,
        },
        {
            "type": "table",
            "title": "Encaminhamentos por tipo",
            "headers": ["Tipo", "Quantidade"],
            "rows": referral_rows,
        },
        {
            "type": "table",
            "title": "Equipamentos",
            "headers": ["Status", "Quantidade"],
            "rows": equipment_rows,
        },
        {
            "type": "table",
            "title": "Pendências",
            "headers": ["Tipo", "Quantidade"],
            "rows": pending_rows,
        },
    ]

    return generate_report_pdf(
        title="Fechamento Mensal Oficial",
        month=month,
        year=year,
        sections=sections,
        metadata={
            "generated_by": metadata.get("generated_by", "Sistema"),
            "generated_at": metadata.get("generated_at", datetime.now()),
            "institution": metadata.get("institution", "Primeira Igreja Batista de Taubaté"),
        },
    )
