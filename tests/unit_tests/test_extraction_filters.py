"""Unit tests for GenEC extraction filters module."""
from __future__ import annotations

from typing import Any
from unittest.mock import patch, MagicMock, Mock
import pytest

from GenEC.core import extraction_filters, PositionalFilterType
from GenEC.core.configuration import RegexConfiguration, RegexListConfiguration, PositionalConfiguration


@pytest.fixture
def regex_config() -> RegexConfiguration:
    """Create a RegexConfiguration for testing."""
    return RegexConfiguration(
        cluster_filter='\n',
        should_slice_clusters=False,
        text_filter='test.*'
    )


@pytest.fixture
def regex_list_config() -> RegexListConfiguration:
    """Create a RegexListConfiguration for testing."""
    return RegexListConfiguration(
        cluster_filter='\n',
        should_slice_clusters=False,
        text_filter=['filter1', 'filter2']
    )


@pytest.fixture
def positional_config() -> PositionalConfiguration:
    """Create a PositionalConfiguration for testing."""
    return PositionalConfiguration(
        cluster_filter='\n',
        should_slice_clusters=False,
        text_filter=PositionalFilterType(separator=' ', line=1, occurrence=2)
    )


class DummyExtractor(extraction_filters.BaseExtractor):
    """Test dummy extractor for unit testing."""

    def extract(self, clusters: list[str]) -> list[str]:
        return ['dummy']


@pytest.mark.unit
def test_get_extractor_returns_registered_extractor(
        monkeypatch: Any, regex_config: RegexConfiguration) -> None:
    monkeypatch.setitem(
        extraction_filters._extractor_registry,
        'dummy',
        DummyExtractor)
    extractor: extraction_filters.BaseExtractor = extraction_filters.get_extractor(
        'dummy', regex_config)
    assert isinstance(extractor, DummyExtractor)
    assert extractor.config == regex_config


@pytest.mark.unit
def test_get_extractor_raises_for_unregistered_name(
        regex_config: RegexConfiguration) -> None:
    with pytest.raises(ValueError) as exc_info:
        extraction_filters.get_extractor(
            'nonexistent', regex_config)
    assert 'Extractor type "nonexistent" is not registered.' in str(
        exc_info.value)


@pytest.mark.unit
@pytest.mark.parametrize(
    'regex_pattern, expected',
    [
        (r'\d+', ['48291', '7', '345', '98', '1204', '550']),
        (r'(\d+)', ['48291', '7', '345', '98', '1204', '550']),
        (r'(\d+)[^\d]+(\d+)', ['48291 | 384', '7 | 2',
         '345 | 19', '98 | 771', '1204 | 66', '550 | 43']),
        (r'(\d+)[^\d]+(\d+)[^\d]+(\d+)', ['48291 | 384 | 11',
         '345 | 19 | 8', '1204 | 66 | 99', '550 | 43 | 7'])
    ]
)
def test_extract_text_from_clusters_by_regex(
        regex_pattern: str, expected: list[str]) -> None:
    clusters: list[str] = ['text48291more_384even11more', 'single_number7_test2', 'random345text19again8',
                           'prefix98middle771end', 'data1204with66extra99', 'noise550letters43final7']
    # Create a config for testing
    test_config = RegexConfiguration(
        cluster_filter='\n',
        should_slice_clusters=False,
        text_filter=regex_pattern
    )
    extractor: extraction_filters.RegexExtractor = extraction_filters.RegexExtractor(test_config)
    assert extractor.extract(clusters) == expected


@pytest.mark.unit
def test_extract_text_from_clusters_by_position() -> None:
    clusters: list[str] = [
        'line_1\nline_2 word_1 word_2',
        'line_3\nline_4 word_3 word_4',
        'line_5']
    # Create a config for testing
    test_config = PositionalConfiguration(
        cluster_filter='\n',
        should_slice_clusters=False,
        text_filter=PositionalFilterType(separator=' ', line=2, occurrence=3)
    )
    extractor: extraction_filters.PositionalExtractor = extraction_filters.PositionalExtractor(test_config)
    assert extractor.extract(clusters) == ['word_2', 'word_4']


@pytest.mark.unit
@pytest.mark.parametrize(
    'clusters, regex_filters, expected_filtered_clusters',
    [
        (['abc123', 'xyz89', 'test456', 'hello111', 'finalTest'],
         [r'\d{3}', r'test'], ['abc123', 'test456', 'hello111']),
        (['abc123', 'xyz89', 'test456', 'hello111', 'finalTest'],
         [r'\d{3}', r'test', r'final'], ['test456']),
        (['abc123', 'xyz89', 'test456', 'hello111',
         'finalTest'], [r'^z.*$', r'test'], [])
    ]
)
@patch('GenEC.core.extraction_filters.RegexExtractor')
def test_extract_text_from_clusters_by_regex_list(mock_regex_extractor: Mock,
                                                  clusters: list[str], regex_filters: list[str],
                                                  expected_filtered_clusters: list[str]) -> None:
    mock_regex_instance: MagicMock = MagicMock()
    mock_regex_extractor.return_value = mock_regex_instance
    # Create a config for testing
    test_config = RegexListConfiguration(
        cluster_filter='\n',
        should_slice_clusters=False,
        text_filter=regex_filters
    )
    extractor: extraction_filters.RegexListExtractor = extraction_filters.RegexListExtractor(test_config)

    extractor.extract(clusters)

    called_config = mock_regex_extractor.call_args[0][0]
    assert called_config.text_filter == regex_filters[-1]
    mock_regex_instance.extract.assert_called_once_with(
        expected_filtered_clusters)


@pytest.mark.unit
def test_regex_extractor_invalid_pattern() -> None:
    """Test that RegexExtractor handles invalid regex patterns correctly."""
    test_config = RegexConfiguration(
        cluster_filter='\n',
        should_slice_clusters=False,
        text_filter='[unclosed'  # Invalid regex
    )
    extractor: extraction_filters.RegexExtractor = extraction_filters.RegexExtractor(test_config)

    with pytest.raises(ValueError, match="Invalid regex pattern: \\[unclosed"):
        extractor.extract(['test cluster'])


@pytest.mark.unit
def test_regex_extractor_invalid_pattern_console_output() -> None:
    """Test that RegexExtractor prints error message for invalid regex patterns."""
    test_config = RegexConfiguration(
        cluster_filter='\n',
        should_slice_clusters=False,
        text_filter='[unclosed'  # Invalid regex
    )
    extractor: extraction_filters.RegexExtractor = extraction_filters.RegexExtractor(test_config)

    with patch('GenEC.core.extraction_filters.console') as mock_console:
        with pytest.raises(ValueError):
            extractor.extract(['test cluster'])

        mock_console.print.assert_called_once()
        call_args: str = mock_console.print.call_args[0][0]
        assert 'Invalid regex pattern' in call_args
        assert 'unterminated character set' in call_args
