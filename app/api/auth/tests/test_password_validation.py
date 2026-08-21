from typing import cast

import pytest
from fastapi import HTTPException

from app.api.auth.models.user import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    RegisterRequest,
)


def _make_request(password: str) -> RegisterRequest:
    return RegisterRequest(
        email="some@example.com",
        password=password,
        name="Li",
        surname="Ly",
    )


@pytest.mark.parametrize(
    "password",
    [
        "Test12!a",
        "Test12!" + "a" * (PASSWORD_MAX_LENGTH - 7),
        "P@ssw0rd",
        "Aa1!aaaa",
    ],
)
def test_register_request_valid_passwords(password: str) -> None:
    request = _make_request(password)
    assert request.password == password


@pytest.mark.parametrize(
    "password, expected_id",
    [
        ("", "password_too_short"),
        ("A1!a", "password_too_short"),
        ("Test1!a", "password_too_short"),
        ("Test12!" + "a" * (PASSWORD_MAX_LENGTH - 6), "password_too_long"),
        ("Test12345", "password_missing_special_character"),
        ("test123!@#", "password_missing_uppercase"),
        ("TestTest!@#", "password_missing_digit"),
    ],
)
def test_register_request_invalid_passwords(password: str, expected_id: str) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _make_request(password)

    assert exc_info.value.status_code == 422
    assert cast(dict[str, str], exc_info.value.detail)["id"] == expected_id


@pytest.mark.parametrize(
    "length",
    [PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH],
)
def test_register_request_password_length_boundaries(length: int) -> None:
    password = "Aa1!" + "a" * (length - 4)
    assert len(password) == length
    request = _make_request(password)
    assert request.password == password


def test_register_request_strips_surrounding_whitespace() -> None:
    request = _make_request("  Test123!  ")
    assert request.password == "Test123!"
