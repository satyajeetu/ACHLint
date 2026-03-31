from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from achlint.formatter import amount_to_cents, ensure_ascii, pad_left_spaces, pad_left_zeros, pad_right_spaces, to_upper_ascii
from achlint.holidays import is_us_federal_holiday
from achlint.models import BuildResult, BuildSummary, OriginatorConfig, PaymentRowInput, ValidationIssue
from achlint.routing import is_valid_routing_number


def build_file(config: OriginatorConfig, rows: list[PaymentRowInput]) -> BuildResult:
    issues = validate_originator_config(config)
    issues.extend(validate_rows(rows, config))
    summary = BuildSummary(
        entries=len(rows),
        total_credit_cents=sum(amount_to_cents(row.amount) for row in rows),
        total_debit_cents=0,
        warnings=sum(1 for issue in issues if issue.severity == "warning"),
        errors=sum(1 for issue in issues if issue.severity == "error"),
        effective_date=config.effective_entry_date,
        originating_dfi=config.originating_dfi_identification,
        immediate_destination=config.immediate_destination_routing,
    )
    if summary.errors:
        return BuildResult(
            status="failed",
            summary=summary,
            issues=issues,
        )

    created_at = datetime.utcnow()
    file_header = build_file_header(config, created_at)
    batch_header = build_batch_header(config, batch_number=1)
    entry_details = [build_entry_detail(row, config, index) for index, row in enumerate(rows, start=config.trace_number_start)]

    entry_hash = compute_entry_hash([row.routing_number for row in rows])
    batch_control = build_batch_control(
        entry_count=len(rows),
        entry_hash=entry_hash,
        total_credit_cents=summary.total_credit_cents,
        config=config,
        batch_number=1,
    )

    current_records = [file_header, batch_header, *entry_details, batch_control]
    block_count = (len(current_records) + 1 + 9) // 10
    file_control = build_file_control(
        batch_count=1,
        block_count=block_count,
        entry_count=len(rows),
        entry_hash=entry_hash,
        total_credit_cents=summary.total_credit_cents,
    )
    all_records = [file_header, batch_header, *entry_details, batch_control, file_control]
    all_records.extend(build_padding_lines(len(all_records)))
    summary.block_count = len(all_records) // 10

    ach_text = "\n".join(all_records)
    return BuildResult(
        status="success",
        summary=replace(summary, generated_at=created_at),
        issues=issues,
        ach_text=ach_text,
    )


def validate_originator_config(config: OriginatorConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required_fields = {
        "company_name": config.company_name,
        "company_identification": config.company_identification,
        "immediate_destination_routing": config.immediate_destination_routing,
        "immediate_destination_name": config.immediate_destination_name,
        "immediate_origin_routing": config.immediate_origin_routing,
        "immediate_origin_name": config.immediate_origin_name,
        "company_entry_description": config.company_entry_description,
        "originating_dfi_identification": config.originating_dfi_identification,
        "file_id_modifier": config.file_id_modifier,
    }
    for field_name, value in required_fields.items():
        if not str(value).strip():
            issues.append(ValidationIssue(code="config_required", message=f"{field_name} is required.", field=field_name))

    if config.effective_entry_date.weekday() >= 5 or is_us_federal_holiday(config.effective_entry_date):
        issues.append(
            ValidationIssue(
                code="effective_date_invalid",
                message="Effective entry date must be a U.S. business day and not a federal holiday.",
                field="effective_entry_date",
            )
        )

    if not is_valid_routing_number(config.immediate_destination_routing):
        issues.append(
            ValidationIssue(
                code="destination_routing_invalid",
                message="Immediate destination routing must be a valid 9-digit ABA routing number.",
                field="immediate_destination_routing",
            )
        )
    if not is_valid_routing_number(config.immediate_origin_routing):
        issues.append(
            ValidationIssue(
                code="origin_routing_invalid",
                message="Immediate origin routing must be a valid 9-digit ABA routing number.",
                field="immediate_origin_routing",
            )
        )
    if len(config.originating_dfi_identification) != 8 or not config.originating_dfi_identification.isdigit():
        issues.append(
            ValidationIssue(
                code="originating_dfi_invalid",
                message="Originating DFI identification must be 8 digits.",
                field="originating_dfi_identification",
            )
        )
    if len(config.file_id_modifier) != 1 or not config.file_id_modifier.isalnum():
        issues.append(
            ValidationIssue(
                code="file_id_modifier_invalid",
                message="File ID modifier must be one alphanumeric character.",
                field="file_id_modifier",
            )
        )
    return issues


def validate_rows(rows: list[PaymentRowInput], config: OriginatorConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for row in rows:
        normalized_name = to_upper_ascii(row.name)
        if normalized_name != row.name.upper():
            issues.append(
                ValidationIssue(
                    code="name_normalized",
                    message="Name was normalized to uppercase ASCII for ACH output.",
                    severity="warning",
                    field="name",
                    row_number=row.row_number,
                    original_value=row.name,
                    suggested_fix="Review the generated recipient name preview.",
                )
            )
        if len(normalized_name) > 22:
            issues.append(
                ValidationIssue(
                    code="name_too_long",
                    message="Recipient name exceeds 22 characters after normalization.",
                    field="name",
                    row_number=row.row_number,
                    original_value=row.name,
                )
            )
        if row.effective_date and row.effective_date != config.effective_entry_date:
            issues.append(
                ValidationIssue(
                    code="row_effective_date_ignored",
                    message="Row-level effective dates are not supported in the output file and were ignored.",
                    severity="warning",
                    field="effective_date",
                    row_number=row.row_number,
                    original_value=row.effective_date.isoformat(),
                    suggested_fix="Use the batch-level effective entry date.",
                )
            )
    return issues


def build_file_header(config: OriginatorConfig, created_at: datetime) -> str:
    record = (
        "1"
        + "01"
        + pad_left_spaces(config.immediate_destination_routing, 10)
        + pad_left_spaces(config.immediate_origin_routing, 10)
        + created_at.strftime("%y%m%d")
        + created_at.strftime("%H%M")
        + to_upper_ascii(config.file_id_modifier[:1])
        + "094"
        + "10"
        + "1"
        + pad_right_spaces(to_upper_ascii(config.immediate_destination_name), 23)
        + pad_right_spaces(to_upper_ascii(config.immediate_origin_name), 23)
        + pad_right_spaces(to_upper_ascii(config.reference_code), 8)
    )
    return _assert_record(record, "File Header")


def build_batch_header(config: OriginatorConfig, batch_number: int) -> str:
    record = (
        "5"
        + "220"
        + pad_right_spaces(to_upper_ascii(config.company_name), 16)
        + pad_right_spaces(to_upper_ascii(config.company_discretionary_data), 20)
        + pad_right_spaces(to_upper_ascii(config.company_identification), 10)
        + "PPD"
        + pad_right_spaces(to_upper_ascii(config.company_entry_description), 10)
        + pad_right_spaces(to_upper_ascii(config.company_descriptive_date), 6)
        + config.effective_entry_date.strftime("%y%m%d")
        + "   "
        + "1"
        + pad_left_zeros(config.originating_dfi_identification, 8)
        + pad_left_zeros(batch_number, 7)
    )
    return _assert_record(record, "Batch Header")


def build_entry_detail(row: PaymentRowInput, config: OriginatorConfig, sequence: int) -> str:
    transaction_code = "22" if row.account_type == "checking" else "32"
    cents = amount_to_cents(row.amount)
    record = (
        "6"
        + transaction_code
        + row.routing_number[:8]
        + row.routing_number[8]
        + pad_right_spaces(to_upper_ascii(row.account_number), 17)
        + pad_left_zeros(cents, 10)
        + pad_right_spaces(to_upper_ascii(row.id_number), 15)
        + pad_right_spaces(to_upper_ascii(row.name), 22)
        + pad_right_spaces(to_upper_ascii(row.discretionary_data), 2)
        + "0"
        + pad_left_zeros(config.originating_dfi_identification, 8)
        + pad_left_zeros(sequence, 7)
    )
    return _assert_record(record, "Entry Detail")


def build_batch_control(
    *,
    entry_count: int,
    entry_hash: int,
    total_credit_cents: int,
    config: OriginatorConfig,
    batch_number: int,
) -> str:
    record = (
        "8"
        + "220"
        + pad_left_zeros(entry_count, 6)
        + pad_left_zeros(entry_hash, 10)
        + pad_left_zeros(0, 12)
        + pad_left_zeros(total_credit_cents, 12)
        + pad_right_spaces(to_upper_ascii(config.company_identification), 10)
        + (" " * 19)
        + (" " * 6)
        + pad_left_zeros(config.originating_dfi_identification, 8)
        + pad_left_zeros(batch_number, 7)
    )
    return _assert_record(record, "Batch Control")


def build_file_control(
    *,
    batch_count: int,
    block_count: int,
    entry_count: int,
    entry_hash: int,
    total_credit_cents: int,
) -> str:
    record = (
        "9"
        + pad_left_zeros(batch_count, 6)
        + pad_left_zeros(block_count, 6)
        + pad_left_zeros(entry_count, 8)
        + pad_left_zeros(entry_hash, 10)
        + pad_left_zeros(0, 12)
        + pad_left_zeros(total_credit_cents, 12)
        + (" " * 39)
    )
    return _assert_record(record, "File Control")


def build_padding_lines(current_line_count: int) -> list[str]:
    remainder = current_line_count % 10
    if remainder == 0:
        return []
    return ["9" * 94 for _ in range(10 - remainder)]


def compute_entry_hash(routing_numbers: list[str]) -> int:
    return sum(int(routing[:8]) for routing in routing_numbers) % (10**10)


def _assert_record(record: str, record_name: str) -> str:
    if len(record) != 94:
        raise ValueError(f"{record_name} must be exactly 94 characters, received {len(record)}.")
    if not ensure_ascii(record):
        raise ValueError(f"{record_name} contains non-ASCII characters.")
    return record
