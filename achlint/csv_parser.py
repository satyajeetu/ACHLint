from __future__ import annotations

import csv
import io
from datetime import datetime

from achlint.formatter import parse_amount, to_upper_ascii
from achlint.models import PaymentRowInput, ValidationIssue
from achlint.routing import is_valid_routing_number


REQUIRED_HEADERS = {
    "name",
    "routing_number",
    "account_number",
    "account_type",
    "amount",
}
OPTIONAL_HEADERS = {"id_number", "discretionary_data", "effective_date"}
ALLOWED_HEADERS = REQUIRED_HEADERS | OPTIONAL_HEADERS
ALLOWED_ACCOUNT_TYPES = {"checking", "savings"}


def parse_payment_csv(content: bytes) -> tuple[list[PaymentRowInput], list[ValidationIssue]]:
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    issues: list[ValidationIssue] = []

    headers = set(reader.fieldnames or [])
    missing = REQUIRED_HEADERS - headers
    extra = headers - ALLOWED_HEADERS
    if missing:
        issues.append(
            ValidationIssue(
                code="csv_missing_columns",
                message=f"Missing required columns: {', '.join(sorted(missing))}.",
                field="headers",
            )
        )
    if extra:
        issues.append(
            ValidationIssue(
                code="csv_unknown_columns",
                message=f"Unknown columns in strict mode: {', '.join(sorted(extra))}.",
                field="headers",
            )
        )
    if issues:
        return [], issues

    rows: list[PaymentRowInput] = []
    seen_signatures: set[tuple[str, str, str, str]] = set()
    for row_number, record in enumerate(reader, start=2):
        name = (record.get("name") or "").strip()
        routing_number = (record.get("routing_number") or "").strip()
        account_number = (record.get("account_number") or "").strip()
        account_type = (record.get("account_type") or "").strip().lower()
        amount_text = (record.get("amount") or "").strip()
        id_number = (record.get("id_number") or "").strip()
        discretionary_data = (record.get("discretionary_data") or "").strip()
        effective_date_text = (record.get("effective_date") or "").strip()

        if not name:
            issues.append(_row_issue(row_number, "name", "name_required", "Name is required.", name))
        if len(to_upper_ascii(name)) > 22:
            issues.append(
                _row_issue(
                    row_number,
                    "name",
                    "name_too_long",
                    "Name exceeds 22 characters after normalization.",
                    name,
                    "Shorten the recipient name.",
                )
            )
        if not account_number:
            issues.append(
                _row_issue(row_number, "account_number", "account_required", "Account number is required.", account_number)
            )
        if len(account_number) > 17:
            issues.append(
                _row_issue(
                    row_number,
                    "account_number",
                    "account_too_long",
                    "Account number must be 17 characters or fewer.",
                    account_number,
                )
            )
        if not is_valid_routing_number(routing_number):
            issues.append(
                _row_issue(
                    row_number,
                    "routing_number",
                    "routing_invalid",
                    "Routing number must be 9 digits and pass the ABA check digit test.",
                    routing_number,
                )
            )
        if account_type not in ALLOWED_ACCOUNT_TYPES:
            issues.append(
                _row_issue(
                    row_number,
                    "account_type",
                    "account_type_invalid",
                    "Account type must be checking or savings.",
                    account_type,
                )
            )

        try:
            amount = parse_amount(amount_text)
        except ValueError as exc:
            issues.append(_row_issue(row_number, "amount", "amount_invalid", str(exc), amount_text))
            amount = None

        effective_date = None
        if effective_date_text:
            try:
                effective_date = datetime.strptime(effective_date_text, "%Y-%m-%d").date()
            except ValueError:
                issues.append(
                    _row_issue(
                        row_number,
                        "effective_date",
                        "effective_date_invalid",
                        "Effective date must use YYYY-MM-DD format.",
                        effective_date_text,
                    )
                )

        signature = (routing_number, account_number, amount_text, name.upper())
        if signature in seen_signatures:
            issues.append(
                _row_issue(
                    row_number,
                    "row",
                    "duplicate_row",
                    "Duplicate payment row detected.",
                    ",".join(signature),
                )
            )
        else:
            seen_signatures.add(signature)

        if amount is None:
            continue

        rows.append(
            PaymentRowInput(
                row_number=row_number,
                name=name,
                routing_number=routing_number,
                account_number=account_number,
                account_type=account_type,
                amount=amount,
                id_number=id_number,
                discretionary_data=discretionary_data,
                effective_date=effective_date,
            )
        )

    return rows, issues


def _row_issue(
    row_number: int,
    field: str,
    code: str,
    message: str,
    original_value: str,
    suggested_fix: str | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        message=message,
        field=field,
        row_number=row_number,
        original_value=original_value,
        suggested_fix=suggested_fix,
    )
