"""Unit tests for security functions (password hashing, JWT tokens)."""

import pytest
from datetime import timedelta
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)


@pytest.mark.unit
def test_password_hashing():
    """Test password hashing creates different hashes for same password."""
    password = "testpassword123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)

    # Hashes should be different due to salt
    assert hash1 != hash2
    # Both should verify correctly
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)


@pytest.mark.unit
def test_password_verification_success():
    """Test password verification succeeds with correct password."""
    password = "correctpassword"
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True


@pytest.mark.unit
def test_password_verification_failure():
    """Test password verification fails with wrong password."""
    password = "correctpassword"
    wrong_password = "wrongpassword"
    hashed = get_password_hash(password)

    assert verify_password(wrong_password, hashed) is False


@pytest.mark.unit
def test_create_access_token():
    """Test JWT token creation includes expected data."""
    data = {"user_id": "123", "username": "testuser"}
    token = create_access_token(data)

    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify contents
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["user_id"] == "123"
    assert decoded["username"] == "testuser"
    assert "exp" in decoded


@pytest.mark.unit
def test_create_access_token_with_custom_expiry():
    """Test JWT token creation with custom expiration."""
    data = {"user_id": "123", "username": "testuser"}
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta=expires_delta)

    decoded = decode_access_token(token)
    assert decoded is not None
    assert "exp" in decoded


@pytest.mark.unit
def test_decode_invalid_token():
    """Test decoding invalid JWT token returns None."""
    invalid_token = "invalid.jwt.token"
    decoded = decode_access_token(invalid_token)

    assert decoded is None


@pytest.mark.unit
def test_decode_tampered_token():
    """Test decoding tampered JWT token returns None."""
    data = {"user_id": "123", "username": "testuser"}
    token = create_access_token(data)

    # Tamper with token
    tampered = token[:-5] + "xxxxx"
    decoded = decode_access_token(tampered)

    assert decoded is None


@pytest.mark.unit
def test_token_with_uuid_user_id():
    """Test JWT token handles UUID user_id correctly."""
    from uuid import uuid4

    user_id = uuid4()
    data = {"user_id": user_id, "username": "testuser"}
    token = create_access_token(data)

    decoded = decode_access_token(token)
    assert decoded is not None
    # UUID should be converted to string
    assert decoded["user_id"] == str(user_id)
