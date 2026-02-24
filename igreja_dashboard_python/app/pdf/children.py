from __future__ import annotations

from datetime import datetime

from app.pdf.report_engine import generate_report_pdf


def build_event_children_pdf(
    title: str, subtitle: str, headers: list[str], rows: list[list[object]]
) -> bytes:
    return generate_report_pdf(
        title=title,
        month=None,
        year=None,
        sections=[
            {"type": "text", "title": "Resumo", "content": subtitle},
            {"type": "table", "title": "Crianças", "headers": headers, "rows": rows},
        ],
        metadata={
            "generated_by": "Sistema",
            "generated_at": datetime.now(),
            "institution": "Primeira Igreja Batista de Taubaté",
        },
    )
