from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from achlint.formatter import ensure_ascii
from achlint.models import BuildSummary, ValidationIssue, ValidationResult


def validate_ach(content: str) -> ValidationResult:
    raw_lines = content.splitlines()
    lines = [line.rstrip("\r") for line in raw_lines if line != ""]
    issues: list[ValidationIssue] = []

    for index, line in enumerate(lines, start=1):
        if len(line) != 94:
            issues.append(
                ValidationIssue(
                    code="line_length_invalid",
                    message="Each ACH record must be exactly 94 characters.",
                    line_number=index,
                    original_value=str(len(line)),
                )
            )
        if not ensure_ascii(line):
            issues.append(
                ValidationIssue(
                    code="line_non_ascii",
                    message="ACH records must contain ASCII characters only.",
                    line_number=index,
                )
            )

    if not lines:
        issues.append(ValidationIssue(code="file_empty", message="ACH file is empty."))
        summary = BuildSummary(errors=1, generated_at=datetime.utcnow())
        return ValidationResult(status="fail", summary=summary, issues=issues)

    record_types = [line[:1] for line in lines]
    if record_types[0] != "1":
        issues.append(ValidationIssue(code="record_order_invalid", message="File must start with record type 1.", line_number=1))

    try:
        batch_header_index = record_types.index("5")
    except ValueError:
        batch_header_index = -1
        issues.append(ValidationIssue(code="batch_header_missing", message="Batch header record type 5 is required."))

    entry_lines = [line for line in lines if line.startswith("6")]
    batch_control_lines = [line for line in lines if line.startswith("8")]
    file_control_lines = [line for line in lines if line.startswith("9") and line != "9" * 94]

    if batch_header_index != 1:
        issues.append(
            ValidationIssue(code="record_order_invalid", message="Batch header must appear immediately after the file header."))
    if not entry_lines:
        issues.append(ValidationIssue(code="entries_missing", message="At least one entry detail record is required."))
    if len(batch_control_lines) != 1:
        issues.append(ValidationIssue(code="batch_control_invalid", message="Exactly one batch control record is required."))
    if len(file_control_lines) != 1:
        issues.append(ValidationIssue(code="file_control_invalid", message="Exactly one file control record is required."))

    if batch_header_index > -1:
        batch_header = lines[batch_header_index]
        if batch_header[1:4] != "220":
            issues.append(ValidationIssue(code="service_class_invalid", message="Service class must be 220.", line_number=batch_header_index + 1))
        if batch_header[50:53] != "PPD":
            issues.append(ValidationIssue(code="sec_invalid", message="SEC code must be PPD.", line_number=batch_header_index + 1))

    computed_entry_hash = sum(int(line[3:11]) for line in entry_lines) % (10**10) if entry_lines else 0
    total_credits = sum(int(line[29:39]) for line in entry_lines) if entry_lines else 0
    total_debits = 0
    for line_number, line in enumerate(lines, start=1):
        if line.startswith("6") and line[1:3] not in {"22", "32"}:
            issues.append(
                ValidationIssue(
                    code="transaction_code_invalid",
                    message="Only credit transaction codes 22 and 32 are supported.",
                    line_number=line_number,
                    original_value=line[1:3],
                )
            )

    if batch_control_lines:
        batch_control = batch_control_lines[0]
        if int(batch_control[4:10]) != len(entry_lines):
            issues.append(ValidationIssue(code="entry_count_mismatch", message="Batch control entry count does not match entries."))
        if int(batch_control[10:20]) != computed_entry_hash:
            issues.append(ValidationIssue(code="entry_hash_mismatch", message="Batch control entry hash does not match entries."))
        if int(batch_control[20:32]) != total_debits:
            issues.append(ValidationIssue(code="debit_total_mismatch", message="Batch control debit total must be zero."))
        if int(batch_control[32:44]) != total_credits:
            issues.append(ValidationIssue(code="credit_total_mismatch", message="Batch control credit total does not match entries."))

    if file_control_lines:
        file_control = file_control_lines[0]
        actual_blocks = len(lines) // 10 if len(lines) % 10 == 0 else (len(lines) // 10) + 1
        if int(file_control[1:7]) != 1:
            issues.append(ValidationIssue(code="batch_count_invalid", message="File control batch count must be 1 for MVP."))
        if int(file_control[7:13]) != actual_blocks:
            issues.append(ValidationIssue(code="block_count_mismatch", message="File control block count does not match line count."))
        if int(file_control[13:21]) != len(entry_lines):
            issues.append(ValidationIssue(code="file_entry_count_mismatch", message="File control entry count does not match entries."))
        if int(file_control[21:31]) != computed_entry_hash:
            issues.append(ValidationIssue(code="file_entry_hash_mismatch", message="File control entry hash does not match entries."))
        if int(file_control[31:43]) != total_debits:
            issues.append(ValidationIssue(code="file_debit_total_mismatch", message="File control debit total must be zero."))
        if int(file_control[43:55]) != total_credits:
            issues.append(ValidationIssue(code="file_credit_total_mismatch", message="File control credit total does not match entries."))

    if len(lines) % 10 != 0:
        issues.append(ValidationIssue(code="padding_invalid", message="ACH file must be padded to a multiple of 10 lines."))
    if file_control_lines:
        file_control_index = next(index for index, line in enumerate(lines) if line == file_control_lines[0])
        if batch_control_lines:
            batch_control_index = next(index for index, line in enumerate(lines) if line == batch_control_lines[0])
            expected_entry_section = lines[2:batch_control_index]
            if any(not line.startswith("6") for line in expected_entry_section):
                issues.append(ValidationIssue(code="record_order_invalid", message="Entry detail records must appear between the batch header and batch control."))
            if batch_control_index != 2 + len(entry_lines):
                issues.append(ValidationIssue(code="record_order_invalid", message="Batch control must appear immediately after the last entry detail record."))
        if file_control_index + 1 < len(lines):
            padding_lines = lines[file_control_index + 1 :]
            if any(line != "9" * 94 for line in padding_lines):
                issues.append(ValidationIssue(code="padding_invalid", message="Only all-9 padding records may appear after the file control record."))
        if any(line.startswith("9") and line == "9" * 94 for line in lines[:file_control_index]):
            issues.append(ValidationIssue(code="record_order_invalid", message="Padding records may only appear after the file control record."))

    trace_numbers = [line[79:94] for line in entry_lines]
    if trace_numbers != sorted(trace_numbers):
        issues.append(ValidationIssue(code="trace_order_invalid", message="Trace numbers must be ascending within the batch."))

    warnings = sum(1 for issue in issues if issue.severity == "warning")
    errors = sum(1 for issue in issues if issue.severity == "error")
    status = "fail" if errors else ("pass_with_warnings" if warnings else "pass")
    summary = BuildSummary(
        entries=len(entry_lines),
        total_credit_cents=total_credits,
        total_debit_cents=total_debits,
        warnings=warnings,
        errors=errors,
        batch_count=1,
        block_count=len(lines) // 10 if len(lines) % 10 == 0 else 0,
        service_class="220",
        sec_code="PPD",
        generated_at=datetime.utcnow(),
    )
    return ValidationResult(status=status, summary=replace(summary), issues=issues)
