"""
Test password and email validation
"""
import pytest
from app.api.user_routes import validate_password, validate_email_format


class TestPasswordValidation:
    """Test password validation requirements"""
    
    def test_valid_passwords(self):
        """Test valid password examples"""
        valid_passwords = [
            "Pass123!word",
            "Secure#99Pass",
            "MyP@ssw0rd",
            "Test123$abc",
            "Hello_World1",
        ]
        
        for pwd in valid_passwords:
            is_valid, error = validate_password(pwd)
            assert is_valid, f"Password '{pwd}' should be valid but got error: {error}"
            assert error == ""
    
    def test_password_too_short(self):
        """Test password less than 8 characters"""
        is_valid, error = validate_password("Short1!")
        assert not is_valid
        assert "at least 8 characters" in error
    
    def test_password_no_numbers(self):
        """Test password without numbers"""
        is_valid, error = validate_password("NoNumbers!")
        assert not is_valid
        assert "at least one number" in error
    
    def test_password_no_letters(self):
        """Test password without letters"""
        is_valid, error = validate_password("12345678!")
        assert not is_valid
        assert "at least one letter" in error
    
    def test_password_no_special_char(self):
        """Test password without special characters"""
        is_valid, error = validate_password("Password123")
        assert not is_valid
        assert "special character" in error
    
    def test_password_with_whitespace(self):
        """Test password with whitespace"""
        is_valid, error = validate_password("Pass word1!")
        assert not is_valid
        assert "whitespace" in error
        
        # Test with tabs and newlines
        is_valid, error = validate_password("Pass\tword1!")
        assert not is_valid
        
        is_valid, error = validate_password("Pass\nword1!")
        assert not is_valid


class TestEmailValidation:
    """Test email format validation"""
    
    def test_valid_emails(self):
        """Test valid email formats"""
        valid_emails = [
            "user@example.com",
            "john.doe@company.org",
            "test_user@domain.co.uk",
            "admin@sub.domain.com",
            "user123@test.io",
        ]
        
        for email in valid_emails:
            is_valid, error = validate_email_format(email)
            assert is_valid, f"Email '{email}' should be valid but got error: {error}"
            assert error == ""
    
    def test_invalid_emails(self):
        """Test invalid email formats"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user@domain",
            "user domain@example.com",
            "user@domain com",
            "",
        ]
        
        for email in invalid_emails:
            is_valid, error = validate_email_format(email)
            assert not is_valid, f"Email '{email}' should be invalid"
            assert "Invalid email format" in error
    
    def test_email_missing_at_symbol(self):
        """Test email without @ symbol"""
        is_valid, error = validate_email_format("userexample.com")
        assert not is_valid
        assert "Invalid email format" in error
    
    def test_email_missing_domain(self):
        """Test email without domain"""
        is_valid, error = validate_email_format("user@")
        assert not is_valid
        assert "Invalid email format" in error
    
    def test_email_missing_tld(self):
        """Test email without top-level domain"""
        is_valid, error = validate_email_format("user@domain")
        assert not is_valid
        assert "Invalid email format" in error


class TestCombinedValidation:
    """Test realistic scenarios"""
    
    def test_common_weak_passwords(self):
        """Test commonly weak passwords are rejected"""
        weak_passwords = [
            "password",
            "12345678",
            "qwerty123",
            "letmein",
        ]
        
        for pwd in weak_passwords:
            is_valid, error = validate_password(pwd)
            assert not is_valid, f"Weak password '{pwd}' should be rejected"
    
    def test_strong_password_examples(self):
        """Test strong password examples"""
        strong_passwords = [
            "MySecure#Pass123",
            "Tr0ub4dor&3",
            "C0rrect-H0rse-Battery!Staple",
        ]
        
        for pwd in strong_passwords:
            is_valid, error = validate_password(pwd)
            assert is_valid, f"Strong password '{pwd}' should be accepted"
