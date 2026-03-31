from __future__ import annotations

from datetime import date

from achlint.csv_parser import parse_payment_csv
from achlint.formatter import amount_to_cents, pad_left_zeros, to_upper_ascii
from achlint.holidays import is_us_federal_holiday, next_business_day
from achlint.models import OriginatorConfig
from achlint.nacha_builder import build_batch_header, build_entry_detail, build_file, compute_entry_hash
from achlint.nacha_validator import validate_ach
from achlint.routing import compute_routing_check_digit, is_valid_routing_number


def sample_config() -> OriginatorConfig:
    return OriginatorConfig(
        company_name="ACME PAYROLL",
        company_identification="1234567890",
        immediate_destination_routing="021000021",
        immediate_destination_name="JPMORGAN CHASE",
        immediate_origin_routing="011000015",
        immediate_origin_name="BANK OF AMERICA",
        company_entry_description="PAYROLL",
        effective_entry_date=date(2026, 4, 1),
        originating_dfi_identification="01100001",
        file_id_modifier="A",
    )


def sample_csv() -> bytes:
    return (
        b"name,routing_number,account_number,account_type,amount,id_number\n"
        b"Jane Doe,021000021,123456789,checking,1250.00,EMP001\n"
        b"John Smith,011000138,987654321,savings,980.55,EMP002\n"
    )


def test_routing_check_digit() -> None:
    assert compute_routing_check_digit("02100002") == 1
    assert is_valid_routing_number("021000021")


def test_amount_to_cents_and_padding() -> None:
    assert amount_to_cents("12.34") == 1234
    assert pad_left_zeros(1234, 10) == "0000001234"
    assert to_upper_ascii("Jos\xe9") == "JOSE"


def test_holiday_logic() -> None:
    assert is_us_federal_holiday(date(2026, 7, 3))
    assert next_business_day(date(2026, 7, 4)) == date(2026, 7, 6)


def test_csv_to_valid_ach() -> None:
    rows, issues = parse_payment_csv(sample_csv())
    assert not issues
    result = build_file(sample_config(), rows)
    assert result.status == "success"
    assert result.ach_text

    validation = validate_ach(result.ach_text)
    assert validation.status == "pass"


def test_record_lengths() -> None:
    rows, _ = parse_payment_csv(sample_csv())
    config = sample_config()
    batch_header = build_batch_header(config, 1)
    entry = build_entry_detail(rows[0], config, 1)
    assert len(batch_header) == 94
    assert len(entry) == 94


def test_entry_hash() -> None:
    rows, _ = parse_payment_csv(sample_csv())
    assert compute_entry_hash([row.routing_number for row in rows]) == 3200015


def test_invalid_csv_headers() -> None:
    rows, issues = parse_payment_csv(b"name,amount\nJane,1.00\n")
    assert not rows
    assert any(issue.code == "csv_missing_columns" for issue in issues)


def test_invalid_ach_line_length() -> None:
    validation = validate_ach("123")
    assert validation.status == "fail"
    assert any(issue.code == "line_length_invalid" for issue in validation.issues)
