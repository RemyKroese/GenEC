from __future__ import annotations

from typing import Any, cast
import pytest
from unittest.mock import patch, MagicMock, Mock

from GenEC.core import ConfigOptions, extraction_filters, PositionalFilterType
from GenEC.core.types.preset_config import Finalized


@pytest.fixture
def tst_config() -> dict[str, Any]:
    return {
        ConfigOptions.CLUSTER_FILTER.value: None,
        ConfigOptions.TEXT_FILTER_TYPE.value: None,
        ConfigOptions.TEXT_FILTER.value: None,
        ConfigOptions.SHOULD_SLICE_CLUSTERS.value: None,
        ConfigOptions.SRC_START_CLUSTER_TEXT.value: None,
        ConfigOptions.SRC_END_CLUSTER_TEXT.value: None,
        ConfigOptions.REF_START_CLUSTER_TEXT.value: None,
        ConfigOptions.REF_END_CLUSTER_TEXT.value: None
    }


class DummyExtractor(extraction_filters.BaseExtractor):
    def extract(self, clusters: list[str]) -> list[str]:
        return ['dummy']


@pytest.mark.unit
def test_get_extractor_returns_registered_extractor(monkeypatch: Any, tst_config: dict[str, Any]) -> None:
    monkeypatch.setitem(extraction_filters._extractor_registry, 'dummy', DummyExtractor)
    extractor: extraction_filters.BaseExtractor = extraction_filters.get_extractor('dummy', cast(Finalized, tst_config))
    assert isinstance(extractor, DummyExtractor)
    assert extractor.config == tst_config


@pytest.mark.unit
def test_get_extractor_raises_for_unregistered_name(tst_config: dict[str, Any]) -> None:
    with pytest.raises(ValueError) as exc_info:
        extraction_filters.get_extractor('nonexistent', cast(Finalized, tst_config))
    assert 'Extractor type "nonexistent" is not registered.' in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.parametrize(
    'regex_pattern, expected',
    [
        (r'\d+', ['48291', '7', '345', '98', '1204', '550']),
        (r'(\d+)', ['48291', '7', '345', '98', '1204', '550']),
        (r'(\d+)[^\d]+(\d+)', ['48291 | 384', '7 | 2', '345 | 19', '98 | 771', '1204 | 66', '550 | 43']),
        (r'(\d+)[^\d]+(\d+)[^\d]+(\d+)', ['48291 | 384 | 11', '345 | 19 | 8', '1204 | 66 | 99', '550 | 43 | 7'])
    ]
)
def test_extract_text_from_clusters_by_regex(tst_config: dict[str, Any], regex_pattern: str, expected: list[str]) -> None:
    clusters: list[str] = ['text48291more_384even11more', 'single_number7_test2', 'random345text19again8',
                'prefix98middle771end', 'data1204with66extra99', 'noise550letters43final7']
    extractor: extraction_filters.RegexExtractor = extraction_filters.RegexExtractor(cast(Finalized, tst_config))
    extractor.config[ConfigOptions.TEXT_FILTER.value] = regex_pattern
    assert extractor.extract(clusters) == expected


@pytest.mark.unit
def test_extract_text_from_clusters_by_position(tst_config: dict[str, Any]) -> None:
    clusters: list[str] = ['line_1\nline_2 word_1 word_2', 'line_3\nline_4 word_3 word_4', 'line_5']
    extractor: extraction_filters.PositionalExtractor = extraction_filters.PositionalExtractor(cast(Finalized, tst_config))
    extractor.config[ConfigOptions.TEXT_FILTER.value] = PositionalFilterType(separator=' ', line=2, occurrence=3)
    assert extractor.extract(clusters) == ['word_2', 'word_4']


@pytest.mark.unit
@pytest.mark.parametrize(
    'clusters, regex_filters, expected_filtered_clusters',
    [
        (['abc123', 'xyz89', 'test456', 'hello111', 'finalTest'], [r'\d{3}', r'test'], ['abc123', 'test456', 'hello111']),
        (['abc123', 'xyz89', 'test456', 'hello111', 'finalTest'], [r'\d{3}', r'test', r'final'], ['test456']),
        (['abc123', 'xyz89', 'test456', 'hello111', 'finalTest'], [r'^z.*$', r'test'], [])
    ]
)
@patch('GenEC.core.extraction_filters.RegexExtractor')
def test_extract_text_from_clusters_by_regex_list(mock_regex_extractor: Mock, tst_config: dict[str, Any], clusters: list[str], regex_filters: list[str], expected_filtered_clusters: list[str]) -> None:
    mock_regex_instance: MagicMock = MagicMock()
    mock_regex_extractor.return_value = mock_regex_instance
    extractor: extraction_filters.RegexListExtractor = extraction_filters.RegexListExtractor(cast(Finalized, tst_config))
    extractor.config[ConfigOptions.TEXT_FILTER.value] = regex_filters

    extractor.extract(clusters)

    called_config: dict[str, Any] = mock_regex_extractor.call_args[0][0]
    assert called_config[ConfigOptions.TEXT_FILTER.value] == regex_filters[-1]
    mock_regex_instance.extract.assert_called_once_with(expected_filtered_clusters)


@pytest.mark.unit
def test_regex_extractor_invalid_pattern(tst_config: dict[str, Any]) -> None:
    """Test that RegexExtractor handles invalid regex patterns correctly."""
    tst_config[ConfigOptions.TEXT_FILTER.value] = '[unclosed'  # Invalid regex
    extractor: extraction_filters.RegexExtractor = extraction_filters.RegexExtractor(cast(Finalized, tst_config))
    
    with pytest.raises(ValueError, match="Invalid regex pattern: \\[unclosed"):
        extractor.extract(['test cluster'])


@pytest.mark.unit  
def test_regex_extractor_invalid_pattern_console_output(tst_config: dict[str, Any]) -> None:
    """Test that RegexExtractor prints error message for invalid regex patterns."""
    tst_config[ConfigOptions.TEXT_FILTER.value] = '[unclosed'  # Invalid regex
    extractor: extraction_filters.RegexExtractor = extraction_filters.RegexExtractor(cast(Finalized, tst_config))
    
    with patch('GenEC.core.extraction_filters.console') as mock_console:
        with pytest.raises(ValueError):
            extractor.extract(['test cluster'])
        
        mock_console.print.assert_called_once()
        call_args: str = mock_console.print.call_args[0][0]
        assert 'Invalid regex pattern' in call_args
        assert 'unterminated character set' in call_args
