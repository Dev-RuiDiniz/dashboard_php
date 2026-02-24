from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

A4_WIDTH = 595
A4_HEIGHT = 842
LEFT_MARGIN = 42
RIGHT_MARGIN = 42
TOP_MARGIN = 42
BOTTOM_MARGIN = 42
LINE_HEIGHT = 14
MAX_TEXT_WIDTH = 105

INSTITUTION_NAME = "Primeira Igreja Batista de Taubaté"
SYSTEM_NAME = "Sistema de Gestão da Ação Social"
FOOTER_TEXT = "Documento gerado automaticamente pelo Sistema de Gestão da Ação Social"


MONTH_LABELS = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _normalize_generated_at(value: object) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if value is None:
        return datetime.now().strftime("%d/%m/%Y %H:%M")
    return str(value)


def _logo_label() -> str:
    candidates = [
        Path("static/logos/inicial.jpg"),
        Path("static/logos/logo.cliente.jpeg"),
        Path("static/logos/fundo.jpg"),
    ]
    existing = next((item for item in candidates if item.exists()), None)
    if existing:
        return f"Logo institucional: {existing.name}"
    return "Logo institucional: [placeholder]"


def _period_label(month: int | None, year: int | None) -> str:
    if month and year:
        month_name = MONTH_LABELS.get(month, str(month))
        return f"Período: {month_name}/{year}"
    if year:
        return f"Período: {year}"
    return "Período: Geral"


def _stringify(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return str(value)


def _wrap_text(text: str, max_chars: int = MAX_TEXT_WIDTH) -> list[str]:
    normalized = " ".join(text.split()) if text else ""
    if not normalized:
        return [""]

    words = normalized.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = word
        else:
            lines.append(word[:max_chars])
            current = word[max_chars:]
    if current:
        lines.append(current)
    return lines


def _append_lines(pages: list[list[str]], text: str) -> None:
    for wrapped in _wrap_text(text):
        page = pages[-1]
        if len(page) >= 48:
            pages.append([])
            page = pages[-1]
        page.append(wrapped)


def _draw_lines_for_section(pages: list[list[str]], section: dict[str, object]) -> None:
    title = _stringify(section.get("title") or "Seção")
    _append_lines(pages, f"\n{title}")

    section_type = section.get("type")
    if section_type == "text":
        content = _stringify(section.get("content") or "-")
        for line in _wrap_text(content):
            _append_lines(pages, line)
        return

    if section_type == "table":
        headers = [str(value) for value in section.get("headers", [])]
        rows = section.get("rows") or []
        if headers:
            _append_lines(pages, " | ".join(headers))
            _append_lines(pages, "-" * min(110, max(20, len(" | ".join(headers)))))
        if rows:
            for row in rows:
                values = [_stringify(item) for item in row]
                _append_lines(pages, " | ".join(values))
        else:
            _append_lines(pages, "Sem registros para os filtros informados.")
        return

    _append_lines(pages, "Tipo de seção não suportado.")


def _build_document_lines(
    title: str,
    month: int | None,
    year: int | None,
    sections: list[dict[str, object]],
    metadata: dict[str, object],
) -> list[list[str]]:
    generated_by = _stringify(metadata.get("generated_by") or "Usuário autenticado")
    generated_at = _normalize_generated_at(metadata.get("generated_at"))
    institution = _stringify(metadata.get("institution") or INSTITUTION_NAME)

    pages: list[list[str]] = [[]]

    _append_lines(pages, _logo_label())
    _append_lines(pages, SYSTEM_NAME)
    _append_lines(pages, institution)
    _append_lines(pages, f"Relatório: {title}")
    _append_lines(pages, _period_label(month, year))
    _append_lines(pages, f"Data de geração: {generated_at}")
    _append_lines(pages, f"Gerado por: {generated_by}")
    _append_lines(pages, "=" * 90)

    for section in sections:
        _draw_lines_for_section(pages, section)

    return pages


def _page_stream(lines: list[str], page_number: int, total_pages: int) -> bytes:
    y = A4_HEIGHT - TOP_MARGIN
    stream_lines: list[str] = []

    for line in lines:
        escaped = _escape_pdf_text(line[:180])
        stream_lines.append(f"BT /F1 10 Tf {LEFT_MARGIN} {y} Td ({escaped}) Tj ET")
        y -= LINE_HEIGHT

    footer_y = BOTTOM_MARGIN
    page_footer = f"Página {page_number} de {total_pages}"
    stream_lines.append(f"BT /F1 9 Tf {LEFT_MARGIN} {footer_y} Td ({_escape_pdf_text(page_footer)}) Tj ET")
    stream_lines.append(
        f"BT /F1 9 Tf {LEFT_MARGIN + 120} {footer_y} Td ({_escape_pdf_text(FOOTER_TEXT)}) Tj ET"
    )

    return "\n".join(stream_lines).encode("latin-1", errors="replace")


def generate_report_pdf(
    title: str,
    month: int | None,
    year: int | None,
    sections: list[dict[str, object]],
    metadata: dict[str, object],
) -> bytes:
    pages_lines = _build_document_lines(title, month, year, sections, metadata)
    total_pages = len(pages_lines)

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")

    page_object_ids = [3 + idx for idx in range(total_pages)]
    kids = " ".join(f"{pid} 0 R" for pid in page_object_ids)
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {total_pages} >>".encode("ascii"))

    content_object_ids = [3 + total_pages + idx for idx in range(total_pages)]

    for idx, content_id in enumerate(content_object_ids):
        page_obj = (
            "<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {A4_WIDTH} {A4_HEIGHT}] "
            "/Resources << /Font << /F1 "
            f"{3 + (2 * total_pages)} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        )
        objects.append(page_obj.encode("ascii"))

    for idx, lines in enumerate(pages_lines, start=1):
        stream_data = _page_stream(lines, idx, total_pages)
        objects.append(
            f"<< /Length {len(stream_data)} >>\nstream\n".encode("ascii")
            + stream_data
            + b"\nendstream"
        )

    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{idx} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode(
            "ascii"
        )
    )
    return bytes(pdf)
