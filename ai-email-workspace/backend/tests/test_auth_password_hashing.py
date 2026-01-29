from app.services.auth import hash_password, verify_password


def test_hash_password_short_password() -> None:
    password = "short-password"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash)


def test_hash_password_long_password() -> None:
    password = "long-password-" * 20
    password_hash = hash_password(password)

    assert verify_password(password, password_hash)
