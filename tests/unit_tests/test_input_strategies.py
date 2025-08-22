"""Tests for input strategy validation error handling."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, Mock

from GenEC.core.input_strategies import RegexInputStrategy, PositionalInputStrategy
from GenEC.core.types.preset_config import Initialized
from GenEC.core.specs import PositionalFilterType


@pytest.fixture
def mock_config() -> Initialized:
    """Create a mock configuration for testing."""
    return Initialized(
        cluster_filter='\n',
        text_filter_type='REGEX',
        text_filter='.*',
        should_slice_clusters=False,
        src_start_cluster_text='',
        src_end_cluster_text='',
        ref_start_cluster_text='',
        ref_end_cluster_text=''
    )


@pytest.mark.unit
def test_regex_input_strategy_invalid_pattern(mock_config: Initialized) -> None:
    """Test that RegexInputStrategy handles invalid regex patterns with re-prompting."""
    mock_ask_question: MagicMock = MagicMock()
    # First call returns invalid regex, second call returns valid regex
    mock_ask_question.side_effect = ['[unclosed', r'\d+']
    
    strategy: RegexInputStrategy = RegexInputStrategy(mock_ask_question)
    
    with patch('GenEC.core.input_strategies.console') as mock_console:
        result: str = strategy.collect_input(mock_config)
    
    # Should have been called twice (invalid then valid)
    assert mock_ask_question.call_count == 2
    assert result == r'\d+'
    
    # Should have printed error message
    mock_console.print.assert_called_once()
    call_args: str = mock_console.print.call_args[0][0]
    assert 'Invalid regex pattern' in call_args


@pytest.mark.unit
def test_positional_input_strategy_invalid_line_number(mock_config: Initialized) -> None:
    """Test that PositionalInputStrategy handles invalid line numbers with re-prompting."""
    mock_ask_question: MagicMock = MagicMock()
    # Sequence: separator, invalid line, valid line, invalid occurrence, valid occurrence
    mock_ask_question.side_effect = [' ', 'invalid', '1', 'also_invalid', '2']
    
    strategy: PositionalInputStrategy = PositionalInputStrategy(mock_ask_question)
    
    with patch('GenEC.core.input_strategies.console') as mock_console:
        result: PositionalFilterType = strategy.collect_input(mock_config)
    
    # Should have been called 5 times total
    assert mock_ask_question.call_count == 5
    assert result.separator == ' '
    assert result.line == 1
    assert result.occurrence == 2
    
    # Should have printed error messages twice (line and occurrence)
    assert mock_console.print.call_count == 2
    call_args_list: list[str] = [call[0][0] for call in mock_console.print.call_args_list]
    assert any('Invalid line number' in args for args in call_args_list)
    assert any('Invalid occurrence number' in args for args in call_args_list)


@pytest.mark.unit
def test_positional_input_strategy_zero_values(mock_config: Initialized) -> None:
    """Test that PositionalInputStrategy rejects zero values for line and occurrence."""
    mock_ask_question: MagicMock = MagicMock()
    # Sequence: separator, zero line, valid line, zero occurrence, valid occurrence
    mock_ask_question.side_effect = [' ', '0', '1', '0', '1']
    
    strategy: PositionalInputStrategy = PositionalInputStrategy(mock_ask_question)
    
    with patch('GenEC.core.input_strategies.console') as mock_console:
        result: PositionalFilterType = strategy.collect_input(mock_config)
    
    # Should have been called 5 times total
    assert mock_ask_question.call_count == 5
    assert result.line == 1
    assert result.occurrence == 1
    
    # Should have printed error messages twice (for zero values)
    assert mock_console.print.call_count == 2
