from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional


Severity = Literal["error", "warning", "info"]


@dataclass
class ValidationIssue:
    code: str
    message: str
    severity: Severity = "error"
    field: Optional[str] = None
    row_number: Optional[int] = None
    line_number: Optional[int] = None
    original_value: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class PaymentRowInput:
    row_number: int
    name: str
    routing_number: str
    account_number: str
    account_type: str
    amount: Decimal
    id_number: str = ""
    discretionary_data: str = ""
    effective_date: Optional[date] = None


@dataclass
class OriginatorConfig:
    company_name: str
    company_identification: str
    immediate_destination_routing: str
    immediate_destination_name: str
    immediate_origin_routing: str
    immediate_origin_name: str
    company_entry_description: str
    effective_entry_date: date
    originating_dfi_identification: str
    file_id_modifier: str
    company_discretionary_data: str = ""
    company_descriptive_date: str = ""
    reference_code: str = ""
    trace_number_start: int = 1


@dataclass
class BuildSummary:
    entries: int = 0
    total_credit_cents: int = 0
    total_debit_cents: int = 0
    warnings: int = 0
    errors: int = 0
    batch_count: int = 1
    block_count: int = 0
    effective_date: Optional[date] = None
    service_class: str = "220"
    sec_code: str = "PPD"
    originating_dfi: str = ""
    immediate_destination: str = ""
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BuildResult:
    status: Literal["success", "failed"]
    summary: BuildSummary
    issues: list[ValidationIssue]
    ach_text: str = ""
    exceptions_csv: str = ""
    report_pdf: bytes = b""


@dataclass
class ValidationResult:
    status: Literal["pass", "pass_with_warnings", "fail"]
    summary: BuildSummary
    issues: list[ValidationIssue]
    report_pdf: bytes = b""
    exceptions_csv: str = ""
