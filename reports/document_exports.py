from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from io import BytesIO
import re
from typing import Mapping, Sequence

from django.utils import timezone
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

# XML 1.0 does not permit most C0 control characters. They can arrive from
# imported organizational data and otherwise make openpyxl/python-docx fail.
_ILLEGAL_XML_CHARACTERS = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


def _clean_xml_text(value: str) -> str:
    return _ILLEGAL_XML_CHARACTERS.sub("", value)


def _safe_docx_text(value: object) -> str:
    if value is None:
        return ""
    return _clean_xml_text(str(value))


@dataclass(frozen=True)
class CertificateData:
    certificate_number: str
    organization_name: str
    employee_name: str
    username: str
    department: str
    position: str
    course_title: str
    program_title: str
    completed_at: date
    result_percent: float | None
    valid_until: date | None
    signer_title: str
    signer_name: str


def _safe_excel_text(value: object) -> object:
    """Return XML-safe text and prevent spreadsheet formula injection."""
    if not isinstance(value, str):
        return value

    cleaned = _clean_xml_text(value)
    candidate = cleaned.lstrip(" \t\r\n")
    if cleaned.startswith(("\t", "\r", "\n")) or candidate.startswith(
        ("=", "+", "-", "@")
    ):
        return f"'{cleaned}"
    return cleaned


def _excel_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return value.replace(tzinfo=None)


def _apply_cell_border(cell, color: str = "D9E2F3") -> None:
    thin = Side(style="thin", color=color)
    cell.border = Border(left=thin, right=thin, top=thin, bottom=thin)


def build_training_registry_xlsx(
    rows: Sequence[Mapping[str, object]],
    *,
    generated_at: datetime,
    filters_description: str = "Все данные",
) -> bytes:
    """Build a polished XLSX registry from normalized report rows."""
    workbook = Workbook()
    registry = workbook.active
    registry.title = "Реестр обучения"

    title_fill = PatternFill("solid", fgColor="1F4E78")
    header_fill = PatternFill("solid", fgColor="D9EAF7")
    accent_fill = PatternFill("solid", fgColor="E2F0D9")
    overdue_fill = PatternFill("solid", fgColor="FCE4D6")
    white_font = Font(color="FFFFFF", bold=True, size=14)
    header_font = Font(bold=True, color="1F1F1F")
    centered = Alignment(horizontal="center", vertical="center", wrap_text=True)
    wrapped = Alignment(vertical="top", wrap_text=True)

    headers = [
        "ID назначения",
        "Сотрудник",
        "Логин",
        "Подразделение",
        "Должность",
        "Курс",
        "Программа ИБ",
        "Статус",
        "Дата назначения",
        "Срок прохождения",
        "Дата завершения",
        "Последний результат, %",
        "Тест пройден",
        "Количество попыток",
        "Действительно до",
    ]

    registry.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    title_cell = registry.cell(1, 1, "Реестр обучения по информационной безопасности")
    title_cell.fill = title_fill
    title_cell.font = white_font
    title_cell.alignment = centered
    registry.row_dimensions[1].height = 28

    generated_local = _excel_datetime(generated_at)
    registry.cell(2, 1, "Сформирован")
    registry.cell(2, 2, generated_local)
    registry.cell(2, 2).number_format = "dd.mm.yyyy hh:mm"
    registry.cell(3, 1, "Фильтры")
    registry.merge_cells(start_row=3, start_column=2, end_row=3, end_column=len(headers))
    registry.cell(3, 2, _safe_excel_text(filters_description))

    header_row = 5
    for col_index, header in enumerate(headers, start=1):
        cell = registry.cell(header_row, col_index, header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = centered
        _apply_cell_border(cell)
    registry.row_dimensions[header_row].height = 42

    status_counts: dict[str, int] = {}
    percent_values: list[float] = []

    for row_index, item in enumerate(rows, start=header_row + 1):
        values = [
            item.get("assignment_id"),
            _safe_excel_text(item.get("employee", "")),
            _safe_excel_text(item.get("username", "")),
            _safe_excel_text(item.get("department", "")),
            _safe_excel_text(item.get("position", "")),
            _safe_excel_text(item.get("course", "")),
            _safe_excel_text(item.get("program", "")),
            _safe_excel_text(item.get("status", "")),
            _excel_datetime(item.get("assigned_at")),
            item.get("due_date"),
            _excel_datetime(item.get("completed_at")),
            item.get("latest_percent"),
            _safe_excel_text(item.get("passed", "")),
            item.get("attempts", 0),
            item.get("valid_until"),
        ]
        for col_index, value in enumerate(values, start=1):
            cell = registry.cell(row_index, col_index, value)
            cell.alignment = centered if col_index in {1, 8, 9, 10, 11, 12, 13, 14, 15} else wrapped
            _apply_cell_border(cell, "E7E6E6")

        for column in (9, 11):
            registry.cell(row_index, column).number_format = "dd.mm.yyyy hh:mm"
        for column in (10, 15):
            registry.cell(row_index, column).number_format = "dd.mm.yyyy"
        registry.cell(row_index, 12).number_format = "0.00"

        status = str(item.get("status", ""))
        status_counts[status] = status_counts.get(status, 0) + 1
        if status == "Завершено":
            registry.cell(row_index, 8).fill = accent_fill
        elif status == "Просрочено":
            registry.cell(row_index, 8).fill = overdue_fill

        percent = item.get("latest_percent")
        if isinstance(percent, (int, float)):
            percent_values.append(float(percent))

    last_row = max(header_row + len(rows), header_row)
    registry.freeze_panes = "A6"
    registry.auto_filter.ref = f"A{header_row}:O{last_row}"
    registry.sheet_view.showGridLines = False
    registry.page_setup.orientation = "landscape"
    registry.page_setup.fitToWidth = 1
    registry.sheet_properties.pageSetUpPr.fitToPage = True
    registry.print_title_rows = f"1:{header_row}"

    if rows:
        table = Table(displayName="TrainingRegistry", ref=f"A{header_row}:O{last_row}")
        table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        registry.add_table(table)
    else:
        registry.merge_cells(start_row=header_row + 1, start_column=1, end_row=header_row + 1, end_column=len(headers))
        empty_cell = registry.cell(header_row + 1, 1, "По выбранным фильтрам данные отсутствуют")
        empty_cell.alignment = centered

    widths = {
        1: 14,
        2: 26,
        3: 18,
        4: 24,
        5: 24,
        6: 34,
        7: 30,
        8: 16,
        9: 19,
        10: 18,
        11: 19,
        12: 21,
        13: 15,
        14: 19,
        15: 18,
    }
    for column_index, width in widths.items():
        registry.column_dimensions[get_column_letter(column_index)].width = width

    summary = workbook.create_sheet("Сводка")
    summary.sheet_view.showGridLines = False
    summary.merge_cells("A1:K1")
    summary["A1"] = "Сводка по реестру обучения"
    summary["A1"].fill = title_fill
    summary["A1"].font = white_font
    summary["A1"].alignment = centered
    summary.row_dimensions[1].height = 28

    completed = status_counts.get("Завершено", 0)
    overdue = status_counts.get("Просрочено", 0)
    in_progress = status_counts.get("В процессе", 0)
    assigned = status_counts.get("Назначено", 0)
    average_percent = round(sum(percent_values) / len(percent_values), 2) if percent_values else 0

    metrics = [
        ("Всего назначений", len(rows)),
        ("Завершено", completed),
        ("Просрочено", overdue),
        ("Средний результат, %", average_percent),
    ]
    for row_index, (label, value) in enumerate(metrics, start=3):
        summary.cell(row_index, 1, label)
        summary.cell(row_index, 2, value)
        summary.cell(row_index, 1).font = header_font
        summary.cell(row_index, 1).fill = header_fill
        summary.cell(row_index, 2).fill = accent_fill
        summary.cell(row_index, 1).alignment = wrapped
        summary.cell(row_index, 2).alignment = centered
        _apply_cell_border(summary.cell(row_index, 1))
        _apply_cell_border(summary.cell(row_index, 2))
    summary["B6"].number_format = "0.00"

    summary["A9"] = "Статус"
    summary["B9"] = "Количество"
    for cell in summary[9]:
        if cell.column <= 2:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = centered
            _apply_cell_border(cell)

    status_rows = [
        ("Назначено", assigned),
        ("В процессе", in_progress),
        ("Завершено", completed),
        ("Просрочено", overdue),
    ]
    for row_index, (label, value) in enumerate(status_rows, start=10):
        summary.cell(row_index, 1, label)
        summary.cell(row_index, 2, value)
        _apply_cell_border(summary.cell(row_index, 1))
        _apply_cell_border(summary.cell(row_index, 2))

    chart = BarChart()
    chart.type = "bar"
    chart.style = 10
    chart.title = "Назначения по статусам"
    chart.y_axis.title = "Количество"
    chart.x_axis.title = "Статус"
    data = Reference(summary, min_col=2, min_row=9, max_row=13)
    categories = Reference(summary, min_col=1, min_row=10, max_row=13)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(categories)
    chart.height = 8
    chart.width = 16
    chart.legend = None
    summary.add_chart(chart, "D3")

    summary.column_dimensions["A"].width = 28
    summary.column_dimensions["B"].width = 18
    summary.column_dimensions["C"].width = 3
    summary.column_dimensions["D"].width = 16
    summary.page_setup.orientation = "landscape"
    summary.page_setup.fitToWidth = 1
    summary.page_setup.fitToHeight = 1
    summary.sheet_properties.pageSetUpPr.fitToPage = True
    summary.print_area = "A1:K16"

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def _set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    tc_pr.append(shading)


def _set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    table_header = OxmlElement("w:tblHeader")
    table_header.set(qn("w:val"), "true")
    tr_pr.append(table_header)


def build_certificate_docx(data: CertificateData) -> bytes:
    # Sanitize every string before passing it to the XML-based DOCX writer.
    data = replace(
        data,
        certificate_number=_safe_docx_text(data.certificate_number),
        organization_name=_safe_docx_text(data.organization_name),
        employee_name=_safe_docx_text(data.employee_name),
        username=_safe_docx_text(data.username),
        department=_safe_docx_text(data.department),
        position=_safe_docx_text(data.position),
        course_title=_safe_docx_text(data.course_title),
        program_title=_safe_docx_text(data.program_title),
        signer_title=_safe_docx_text(data.signer_title),
        signer_name=_safe_docx_text(data.signer_name),
    )

    document = Document()
    section = document.sections[0]
    section.top_margin = Cm(1.8)
    section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(2.2)
    section.right_margin = Cm(2.2)

    normal_style = document.styles["Normal"]
    normal_style.font.name = "Arial"
    normal_style._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    normal_style.font.size = Pt(11)

    organization = document.add_paragraph()
    organization.alignment = WD_ALIGN_PARAGRAPH.CENTER
    organization_run = organization.add_run(data.organization_name)
    organization_run.bold = True
    organization_run.font.size = Pt(13)
    organization_run.font.name = "Arial"

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_before = Pt(10)
    title.paragraph_format.space_after = Pt(4)
    title_run = title.add_run("СЕРТИФИКАТ")
    title_run.bold = True
    title_run.font.size = Pt(26)
    title_run.font.name = "Arial"

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle_run = subtitle.add_run("о прохождении обучения по информационной безопасности")
    subtitle_run.italic = True
    subtitle_run.font.size = Pt(12)

    number = document.add_paragraph()
    number.alignment = WD_ALIGN_PARAGRAPH.CENTER
    number.add_run(f"№ {data.certificate_number}").bold = True

    intro = document.add_paragraph()
    intro.alignment = WD_ALIGN_PARAGRAPH.CENTER
    intro.paragraph_format.space_before = Pt(14)
    intro.paragraph_format.space_after = Pt(6)
    intro.add_run("Настоящим подтверждается, что").font.size = Pt(12)

    employee = document.add_paragraph()
    employee.alignment = WD_ALIGN_PARAGRAPH.CENTER
    employee.paragraph_format.space_after = Pt(10)
    employee_run = employee.add_run(data.employee_name)
    employee_run.bold = True
    employee_run.font.size = Pt(18)

    course_text = document.add_paragraph()
    course_text.alignment = WD_ALIGN_PARAGRAPH.CENTER
    course_text.add_run("успешно завершил(а) курс\n")
    course_run = course_text.add_run(f"«{data.course_title}»")
    course_run.bold = True
    course_run.font.size = Pt(15)

    details = document.add_table(rows=1, cols=2)
    details.style = "Table Grid"
    details.autofit = False
    details.columns[0].width = Cm(6)
    details.columns[1].width = Cm(10)
    _set_repeat_table_header(details.rows[0])
    details.rows[0].cells[0].text = "Показатель"
    details.rows[0].cells[1].text = "Значение"
    for cell in details.rows[0].cells:
        _set_cell_shading(cell, "D9EAF7")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in paragraph.runs:
                run.bold = True
                run.font.name = "Arial"

    detail_rows = [
        ("Учетная запись", data.username),
        ("Подразделение", data.department or "—"),
        ("Должность", data.position or "—"),
        ("Программа обучения", data.program_title or "—"),
        ("Дата завершения", data.completed_at.strftime("%d.%m.%Y")),
        (
            "Результат тестирования",
            f"{data.result_percent:.2f}%" if data.result_percent is not None else "Не указан",
        ),
        (
            "Срок действия",
            f"до {data.valid_until.strftime('%d.%m.%Y')}" if data.valid_until else "Не ограничен",
        ),
    ]
    for label, value in detail_rows:
        cells = details.add_row().cells
        cells[0].text = label
        cells[1].text = value
        for cell in cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.name = "Arial"
        cells[0].paragraphs[0].runs[0].bold = True

    document.add_paragraph()
    signatures = document.add_table(rows=2, cols=2)
    signatures.autofit = False
    signatures.columns[0].width = Cm(9)
    signatures.columns[1].width = Cm(7)
    signatures.cell(0, 0).text = data.signer_title or "Ответственный за информационную безопасность"
    signatures.cell(0, 1).text = data.signer_name or "________________________"
    signatures.cell(1, 0).text = "Подпись"
    signatures.cell(1, 1).text = "Ф.И.О."
    for row in signatures.rows:
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(10)

    note = document.add_paragraph()
    note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    note.paragraph_format.space_before = Pt(12)
    note_run = note.add_run(
        "Документ сформирован информационной системой IBSec LMS. "
        "Достоверность сведений подтверждается данными журнала обучения."
    )
    note_run.font.size = Pt(8)
    note_run.italic = True

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run(f"IBSec LMS • Сертификат {data.certificate_number}")
    footer_run.font.name = "Arial"
    footer_run.font.size = Pt(8)

    properties = document.core_properties
    properties.title = f"Сертификат {data.certificate_number}"
    properties.subject = "Подтверждение прохождения обучения по информационной безопасности"
    properties.author = "IBSec LMS"
    properties.keywords = "IBSec LMS, обучение, информационная безопасность, сертификат"

    output = BytesIO()
    document.save(output)
    return output.getvalue()
