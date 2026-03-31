from __future__ import annotations


def compute_routing_check_digit(routing_number: str) -> int:
    digits = [int(char) for char in routing_number[:8]]
    weights = [3, 7, 1] * 3
    total = sum(digit * weight for digit, weight in zip(digits, weights))
    return (10 - (total % 10)) % 10


def is_valid_routing_number(routing_number: str) -> bool:
    if len(routing_number) != 9 or not routing_number.isdigit():
        return False
    return compute_routing_check_digit(routing_number) == int(routing_number[-1])
