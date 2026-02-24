from __future__ import annotations

from datetime import datetime

from app.pdf.report_engine import generate_report_pdf


def render_pdf(title: str, subtitle: str, table_data: list[list[object]], footer: str) -> bytes:
    headers: list[str] = []
    rows: list[list[object]] = []
    if table_data:
        first_row = table_data[0]
        if first_row and all(isinstance(item, str) for item in first_row):
            headers = [str(item) for item in first_row]
            rows = table_data[1:]
        else:
            rows = table_data

    sections = [
        {"type": "text", "title": "Resumo", "content": subtitle},
        {"type": "table", "title": "Dados", "headers": headers, "rows": rows},
        {"type": "text", "title": "Observações", "content": footer},
    ]

    return generate_report_pdf(
        title=title,
        month=None,
        year=None,
        sections=sections,
        metadata={
            "generated_by": "Sistema",
            "generated_at": datetime.now(),
            "institution": "Primeira Igreja Batista de Taubaté",
        },
    )
