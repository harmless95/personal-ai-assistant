from app.api.auth.utils.password import PasswordUtils


def test_password_hashing_and_validation() -> None:
    password = "test_password"
    hashed = PasswordUtils.hash_password(password=password)
    assert hashed != password
    assert PasswordUtils.validate_password(password=password, hashed_password=hashed) is True
    assert PasswordUtils.validate_password(password="fail_password", hashed_password=hashed) is False


def test_salting_uniqueness() -> None:
    password = "test_password"
    hashed1 = PasswordUtils.hash_password(password=password)
    hashed2 = PasswordUtils.hash_password(password=password)
    assert hashed1 != hashed2
