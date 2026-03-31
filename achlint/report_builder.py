from __future__ import annotations

import csv
import io
from typing import Iterable

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from achlint.models import BuildSummary, ValidationIssue


def build_exceptions_csv(issues: Iterable[ValidationIssue]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["row_number", "line_number", "field", "error_code", "severity", "message", "original_value", "suggested_fix"]
    )
    for issue in issues:
        writer.writerow(
            [
                issue.row_number or "",
                issue.line_number or "",
                issue.field or "",
                issue.code,
                issue.severity,
                issue.message,
                issue.original_value or "",
                issue.suggested_fix or "",
            ]
        )
    return output.getvalue()


def build_report_pdf(
    *,
    title: str,
    status: str,
    summary: BuildSummary,
    issues: list[ValidationIssue],
) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    def line(text: str, gap: int = 16) -> None:
        nonlocal y
        if y < 50:
            pdf.showPage()
            y = height - 50
        pdf.drawString(50, y, text[:110])
        y -= gap

    pdf.setFont("Helvetica-Bold", 16)
    line(title, 22)
    pdf.setFont("Helvetica", 10)
    line(f"Status: {status}")
    line(f"Generated: {summary.generated_at.isoformat()} UTC")
    line(f"Entries: {summary.entries}")
    line(f"Total Credit: ${summary.total_credit_cents / 100:.2f}")
    line(f"Service Class: {summary.service_class} | SEC: {summary.sec_code}")
    if summary.effective_date:
        line(f"Effective Date: {summary.effective_date.isoformat()}")
    line(f"Originating DFI: {summary.originating_dfi}")
    line(f"Immediate Destination: {summary.immediate_destination}")
    line(f"Batch Count: {summary.batch_count} | Block Count: {summary.block_count}")
    line("")
    pdf.setFont("Helvetica-Bold", 12)
    line("Issues", 18)
    pdf.setFont("Helvetica", 10)
    if not issues:
        line("No issues found.")
    for issue in issues:
        location_parts = []
        if issue.row_number:
            location_parts.append(f"row {issue.row_number}")
        if issue.line_number:
            location_parts.append(f"line {issue.line_number}")
        if issue.field:
            location_parts.append(issue.field)
        location = f"[{', '.join(location_parts)}] " if location_parts else ""
        line(f"{issue.severity.upper()} {issue.code}: {location}{issue.message}")
        if issue.suggested_fix:
            line(f"Fix: {issue.suggested_fix}")

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
