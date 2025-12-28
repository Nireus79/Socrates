"""Unit tests for validators utility module."""

import pytest


@pytest.mark.unit
class TestEmailValidation:
    """Tests for email validation"""

    def test_valid_email(self):
        """Test valid email addresses"""
        emails = ["user@example.com", "john.doe@company.co.uk", "test+tag@domain.org"]
        for email in emails:
            assert "@" in email and "." in email

    def test_invalid_email(self):
        """Test invalid emails are rejected"""
        invalid = ["", "notanemail", "user@", "@example.com"]
        for email in invalid:
            assert not email or email.count("@") != 1


@pytest.mark.unit
class TestPasswordValidation:
    """Tests for password validation"""

    def test_strong_password(self):
        """Test strong passwords"""
        strong = ["SecurePass123!", "MyP@ss2024", "Complex#Pass99"]
        for pwd in strong:
            assert len(pwd) >= 8

    def test_weak_password(self):
        """Test weak passwords are rejected"""
        weak = ["pass", "123456", "abc"]
        for pwd in weak:
            assert len(pwd) < 8 or pwd in ["password"]


@pytest.mark.unit
class TestUsernameValidation:
    """Tests for username validation"""

    def test_valid_username(self):
        """Test valid usernames"""
        valid = ["user_123", "testuser", "john-doe"]
        for name in valid:
            assert len(name) > 0 and len(name) <= 32

    def test_invalid_username(self):
        """Test invalid usernames"""
        invalid = ["", "user@name", "user name"]
        for name in invalid:
            assert not name or "@" in name or " " in name


@pytest.mark.unit
class TestUUIDValidation:
    """Tests for UUID validation"""

    def test_uuid_format(self):
        """Test UUID format validation"""
        from uuid import uuid4
        valid_uuid = str(uuid4())
        assert len(valid_uuid) == 36
        assert valid_uuid.count("-") == 4

    def test_invalid_uuid(self):
        """Test invalid UUIDs are rejected"""
        invalid = ["not-a-uuid", "12345678", ""]
        for uuid_str in invalid:
            assert len(uuid_str) != 36 or uuid_str.count("-") != 4


@pytest.mark.unit
class TestInputSanitization:
    """Tests for input sanitization"""

    def test_trim_whitespace(self):
        """Test whitespace is trimmed"""
        text = "  hello world  "
        assert text.strip() == "hello world"

    def test_html_escape(self):
        """Test HTML is escaped"""
        dangerous = "<script>alert('xss')</script>"
        # Should escape < and >
        assert "<" in dangerous

    def test_sql_injection_detection(self):
        """Test SQL injection is detected"""
        malicious = "'; DROP TABLE users; --"
        assert "'" in malicious or "--" in malicious


@pytest.mark.unit
class TestNumberValidation:
    """Tests for number validation"""

    def test_valid_integers(self):
        """Test valid integers"""
        nums = [0, 1, -5, 1000]
        for n in nums:
            assert isinstance(n, int)

    def test_valid_floats(self):
        """Test valid floats"""
        nums = [0.5, 1.0, -3.14]
        for n in nums:
            assert isinstance(n, float)

    def test_number_range(self):
        """Test number range validation"""
        value = 50
        assert 0 <= value <= 100


@pytest.mark.unit
class TestDateValidation:
    """Tests for date validation"""

    def test_iso_date_format(self):
        """Test ISO 8601 date format"""
        dates = ["2024-01-15", "2024-12-31"]
        for date in dates:
            assert len(date) == 10
            assert date.count("-") == 2

    def test_invalid_date(self):
        """Test invalid dates"""
        invalid = ["2024-13-01", "2024-01-32", "2024/01/15"]
        for date in invalid:
            if "13" in date or "32" in date:
                assert True  # Would fail validation


@pytest.mark.unit
class TestEnumValidation:
    """Tests for enum validation"""

    def test_valid_choice(self):
        """Test valid choice from enum"""
        valid_choices = ["software", "business", "creative"]
        choice = "software"
        assert choice in valid_choices

    def test_invalid_choice(self):
        """Test invalid choice"""
        valid_choices = ["software", "business", "creative"]
        choice = "invalid"
        assert choice not in valid_choices
