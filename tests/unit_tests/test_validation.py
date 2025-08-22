"""Tests for validation utilities."""

from __future__ import annotations

import pytest

from GenEC.core.validation import validate_regex, validate_integer, ValidationError


class TestValidateRegex:
    """Test cases for validate_regex function."""

    @pytest.mark.unit
    def test_valid_regex_patterns(self) -> None:
        """Test that valid regex patterns return True."""
        valid_patterns: list[str] = [
            r'\d+',
            r'[a-zA-Z]+',
            r'.*',
            r'test',
            r'ab?c*',
            r'^start.*end$',
            r'(\w+)\s+(\w+)',
            r'(?P<name>\w+)',
            r'a{2,5}',
            r'[0-9]{3}-[0-9]{3}-[0-9]{4}'
        ]

        for pattern in valid_patterns:
            assert validate_regex(pattern) is True, f"Expected {pattern} to be valid"

    @pytest.mark.unit
    def test_invalid_regex_patterns(self) -> None:
        """Test that invalid regex patterns return False."""
        invalid_patterns: list[str] = [
            '[unclosed',
            '(unclosed group',
            '*invalid quantifier',
            '+invalid quantifier',
            '?invalid quantifier',
            '(?P<>empty name)',
            '(?P<123>invalid name)',
        ]

        for pattern in invalid_patterns:
            assert validate_regex(pattern) is False, f"Expected {pattern} to be invalid"

    @pytest.mark.unit
    def test_empty_patterns(self) -> None:
        """Test that empty or whitespace-only patterns return False."""
        empty_patterns: list[str] = ['', '   ', '\t', '\n', '  \t  \n  ']

        for pattern in empty_patterns:
            assert validate_regex(pattern) is False, f"Expected empty pattern '{pattern}' to be invalid"


class TestValidateInteger:
    """Test cases for validate_integer function."""

    @pytest.mark.unit
    def test_valid_integers(self) -> None:
        """Test that valid integer strings return True."""
        valid_integers: list[str] = ['0', '1', '42', '-1', '-42', '999', '1000']

        for value in valid_integers:
            assert validate_integer(value) is True, f"Expected {value} to be valid integer"

    @pytest.mark.unit
    def test_invalid_integers(self) -> None:
        """Test that invalid integer strings return False."""
        invalid_integers: list[str] = [
            'abc', '1.5', '1a', 'a1', '', '   ',
            '1 2', '1.0', 'one', 'NaN', 'inf', '-inf'
        ]

        for value in invalid_integers:
            assert validate_integer(value) is False, f"Expected {value} to be invalid integer"

    @pytest.mark.unit
    def test_integer_with_min_value(self) -> None:
        """Test integer validation with minimum value constraint."""
        # Valid cases with min_val=1
        assert validate_integer('1', min_val=1) is True
        assert validate_integer('5', min_val=1) is True
        assert validate_integer('100', min_val=1) is True

        # Invalid cases with min_val=1
        assert validate_integer('0', min_val=1) is False
        assert validate_integer('-1', min_val=1) is False
        assert validate_integer('-10', min_val=1) is False

    @pytest.mark.unit
    def test_integer_with_max_value(self) -> None:
        """Test integer validation with maximum value constraint."""
        # Valid cases with max_val=10
        assert validate_integer('10', max_val=10) is True
        assert validate_integer('5', max_val=10) is True
        assert validate_integer('0', max_val=10) is True
        assert validate_integer('-5', max_val=10) is True

        # Invalid cases with max_val=10
        assert validate_integer('11', max_val=10) is False
        assert validate_integer('100', max_val=10) is False

    @pytest.mark.unit
    def test_integer_with_min_and_max_values(self) -> None:
        """Test integer validation with both minimum and maximum value constraints."""
        # Valid cases with min_val=1, max_val=10
        assert validate_integer('1', min_val=1, max_val=10) is True
        assert validate_integer('5', min_val=1, max_val=10) is True
        assert validate_integer('10', min_val=1, max_val=10) is True

        # Invalid cases with min_val=1, max_val=10
        assert validate_integer('0', min_val=1, max_val=10) is False
        assert validate_integer('11', min_val=1, max_val=10) is False
        assert validate_integer('-1', min_val=1, max_val=10) is False

    @pytest.mark.unit
    def test_integer_whitespace_handling(self) -> None:
        """Test that whitespace-only strings are handled correctly."""
        whitespace_values: list[str] = ['', '   ', '\t', '\n', '  \t  \n  ']

        for value in whitespace_values:
            assert validate_integer(value) is False, f"Expected whitespace value '{value}' to be invalid"


class TestValidationError:
    """Test cases for ValidationError exception."""

    @pytest.mark.unit
    def test_validation_error_creation(self) -> None:
        """Test that ValidationError can be created and raised."""
        error_message: str = "Test validation error"

        with pytest.raises(ValidationError, match=error_message):
            raise ValidationError(error_message)

    @pytest.mark.unit
    def test_validation_error_inheritance(self) -> None:
        """Test that ValidationError inherits from Exception."""
        error: ValidationError = ValidationError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, ValidationError)
