import pytest
from unittest.mock import patch, MagicMock

from GenEC.core import ConfigOptions, extraction_filters, PositionalFilterType


@pytest.fixture
def tst_config():
    return {
        ConfigOptions.CLUSTER_FILTER: None,
        ConfigOptions.TEXT_FILTER_TYPE: None,
        ConfigOptions.TEXT_FILTER: None,
        ConfigOptions.SHOULD_SLICE_CLUSTERS: None,
        ConfigOptions.SRC_START_CLUSTER_TEXT: None,
        ConfigOptions.SRC_END_CLUSTER_TEXT: None,
        ConfigOptions.REF_START_CLUSTER_TEXT: None,
        ConfigOptions.REF_END_CLUSTER_TEXT: None
    }


class DummyExtractor(extraction_filters.BaseExtractor):
    def extract(self, clusters):
        return ['dummy']


def test_get_extractor_returns_registered_extractor(monkeypatch, tst_config):
    monkeypatch.setitem(extraction_filters._extractor_registry, 'dummy', DummyExtractor)
    extractor = extraction_filters.get_extractor('dummy', tst_config)
    assert isinstance(extractor, DummyExtractor)
    assert extractor.config == tst_config


def test_get_extractor_raises_for_unregistered_name(tst_config):
    with pytest.raises(ValueError) as exc_info:
        extraction_filters.get_extractor('nonexistent', tst_config)
    assert 'Extractor type "nonexistent" is not registered.' in str(exc_info.value)


@pytest.mark.parametrize(
    'regex_pattern, expected',
    [
        (r'\d+', ['48291', '7', '345', '98', '1204', '550']),
        (r'(\d+)', ['48291', '7', '345', '98', '1204', '550']),
        (r'(\d+)[^\d]+(\d+)', ['48291 | 384', '7 | 2', '345 | 19', '98 | 771', '1204 | 66', '550 | 43']),
        (r'(\d+)[^\d]+(\d+)[^\d]+(\d+)', ['48291 | 384 | 11', '345 | 19 | 8', '1204 | 66 | 99', '550 | 43 | 7'])
    ]
)
def test_extract_text_from_clusters_by_regex(tst_config, regex_pattern, expected):
    clusters = ['text48291more_384even11more', 'single_number7_test2', 'random345text19again8',
                'prefix98middle771end', 'data1204with66extra99', 'noise550letters43final7']
    extractor = extraction_filters.RegexExtractor(tst_config)
    extractor.config[ConfigOptions.TEXT_FILTER.value] = regex_pattern
    assert extractor.extract(clusters) == expected


def test_extract_text_from_clusters_by_position(tst_config):
    clusters = ['line_1\nline_2 word_1 word_2', 'line_3\nline_4 word_3 word_4', 'line_5']
    extractor = extraction_filters.PositionalExtractor(tst_config)
    extractor.config[ConfigOptions.TEXT_FILTER.value] = PositionalFilterType(separator=' ', line=2, occurrence=3)
    assert extractor.extract(clusters) == ['word_2', 'word_4']


@pytest.mark.parametrize(
    'clusters, regex_filters, expected_filtered_clusters',
    [
        (['abc123', 'xyz89', 'test456', 'hello111', 'finalTest'], [r'\d{3}', r'test'], ['abc123', 'test456', 'hello111']),
        (['abc123', 'xyz89', 'test456', 'hello111', 'finalTest'], [r'\d{3}', r'test', r'final'], ['test456']),
        (['abc123', 'xyz89', 'test456', 'hello111', 'finalTest'], [r'^z.*$', r'test'], [])
    ]
)
@patch('GenEC.core.extraction_filters.RegexExtractor')
def test_extract_text_from_clusters_by_regex_list(mock_regex_extractor, tst_config, clusters, regex_filters, expected_filtered_clusters):
    mock_regex_instance = MagicMock()
    mock_regex_extractor.return_value = mock_regex_instance
    extractor = extraction_filters.RegexListExtractor(tst_config)
    extractor.config[ConfigOptions.TEXT_FILTER.value] = regex_filters

    extractor.extract(clusters)

    called_config = mock_regex_extractor.call_args[0][0]
    assert called_config[ConfigOptions.TEXT_FILTER.value] == regex_filters[-1]
    mock_regex_instance.extract.assert_called_once_with(expected_filtered_clusters)
