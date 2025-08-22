"""Validation utilities for user input and configuration data."""

import re
from typing import Optional
from rich.console import Console

console = Console()


class ValidationError(Exception):
    """Custom exception for validation errors."""


def validate_regex(pattern: str) -> bool:
    """
    Validate if a string is a valid regex pattern.

    Parameters
    ----------
    pattern : str
        The regex pattern to validate

    Returns
    -------
    bool
        True if valid regex, False otherwise
    """
    if not pattern.strip():
        return False
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False


def validate_integer(value: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> bool:
    """
    Validate if a string represents a valid integer within optional bounds.

    Parameters
    ----------
    value : str
        The string to validate
    min_val : Optional[int]
        Minimum allowed value
    max_val : Optional[int]
        Maximum allowed value

    Returns
    -------
    bool
        True if valid integer within bounds, False otherwise
    """
    if not value.strip():
        return False
    try:
        int_val = int(value)
        if min_val is not None and int_val < min_val:
            return False
        if max_val is not None and int_val > max_val:
            return False
        return True
    except ValueError:
        return False
