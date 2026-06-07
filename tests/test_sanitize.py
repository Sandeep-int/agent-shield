import pytest
from api.main import sanitize_prompt

def test_credit_card_redacted():
    result = sanitize_prompt("my card is 4111 1111 1111 1111")
    assert "[CARD_REDACTED]" in result
    assert "4111" not in result

def test_ssn_redacted():
    result = sanitize_prompt("my ssn is 123-45-6789")
    assert "[SSN_REDACTED]" in result
    assert "123-45-6789" not in result

def test_email_redacted():
    result = sanitize_prompt("email me at sandeep@gmail.com")
    assert "[EMAIL_REDACTED]" in result
    assert "sandeep@gmail.com" not in result

def test_api_key_redacted():
    result = sanitize_prompt("api_key: abc123secret")
    assert "[APIKEY_REDACTED]" in result
    assert "abc123secret" not in result

def test_password_redacted():
    result = sanitize_prompt("password: mySecret@123")
    assert "[PASSWORD_REDACTED]" in result
    assert "mySecret@123" not in result

def test_normal_prompt_unchanged():
    result = sanitize_prompt("What is the capital of France?")
    assert result == "What is the capital of France?"

def test_multiple_pii_redacted():
    result = sanitize_prompt("email: test@test.com card: 4111 1111 1111 1111")
    assert "[EMAIL_REDACTED]" in result
    assert "[CARD_REDACTED]" in result
    assert "test@test.com" not in result
    assert "4111" not in result
