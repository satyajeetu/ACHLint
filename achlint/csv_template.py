from __future__ import annotations


TEMPLATE_HEADERS = [
    "name",
    "routing_number",
    "account_number",
    "account_type",
    "amount",
    "id_number",
    "discretionary_data",
    "effective_date",
]


def get_template_csv() -> str:
    return (
        "name,routing_number,account_number,account_type,amount,id_number,discretionary_data,effective_date\n"
        "Jane Doe,021000021,123456789,checking,1250.00,EMP001,,\n"
        "John Smith,011000138,987654321,savings,980.55,EMP002,,\n"
    )
