import pytest
from unittest.mock import patch

from GenEC.core.analyze import Extractor, ConfigOptions, TextFilterTypes, Files

BASIC_TEXT = '''a b c
d e
f g h i
j'''

WHITELINES_TEXT = '''a b c
d e

f g h i

j
k l m n o p
q'''


@pytest.fixture
def extractor_instance():
    config = {
        ConfigOptions.CLUSTER_FILTER: None,
        ConfigOptions.TEXT_FILTER_TYPE: None,
        ConfigOptions.TEXT_FILTER: None,
        ConfigOptions.SHOULD_SLICE_CLUSTERS: None,
        ConfigOptions.SRC_START_CLUSTER_TEXT: None,
        ConfigOptions.SRC_END_CLUSTER_TEXT: None,
        ConfigOptions.REF_START_CLUSTER_TEXT: None,
        ConfigOptions.REF_END_CLUSTER_TEXT: None
    }
    return Extractor(config)


@pytest.mark.parametrize('data, cluster_filter, expected_result', [
    (BASIC_TEXT, '\n', ['a b c', 'd e', 'f g h i', 'j']),
    (WHITELINES_TEXT, '\n\n', ['a b c\nd e', 'f g h i', 'j\nk l m n o p\nq'])])
def test_get_clusters(extractor_instance, data, cluster_filter, expected_result):
    extractor_instance.config[ConfigOptions.CLUSTER_FILTER.value] = cluster_filter
    assert extractor_instance.get_clusters(data, Files.SOURCE.value) == expected_result


@pytest.mark.parametrize(
    "regex_pattern, expected",
    [
        (r'\d+', ['48291', '7', '345', '98', '1204', '550']),
        (r'(\d+)', ['48291', '7', '345', '98', '1204', '550']),
        (r'(\d+)[^\d]+(\d+)', ['48291 | 384', '7 | 2', '345 | 19', '98 | 771', '1204 | 66', '550 | 43']),
        (r'(\d+)[^\d]+(\d+)[^\d]+(\d+)', ['48291 | 384 | 11', '345 | 19 | 8', '1204 | 66 | 99', '550 | 43 | 7'])
    ]
)
def test_extract_text_from_clusters_by_regex(extractor_instance, regex_pattern, expected):
    clusters = [
        'text48291more_384even11more',  # 3 number groups
        'single_number7_test2',  # 2 number groups
        'random345text19again8',  # 3 number groups
        'prefix98middle771end',  # 2 number groups
        'data1204with66extra99',  # 3 number groups
        'noise550letters43final7',  # 3 number groups
    ]
    extractor_instance.config[ConfigOptions.TEXT_FILTER.value] = regex_pattern
    assert extractor_instance.extract_text_from_clusters_by_regex(clusters) == expected


def test_extract_text_from_clusters_by_position(extractor_instance):
    clusters = ['line_1\nline_2 word_1 word_2', 'line_3\nline_4 word_3 word_4', 'line_5']
    extractor_instance.config[ConfigOptions.TEXT_FILTER.value] = {'separator': ' ', 'line': 2, 'occurrence': 3}
    assert extractor_instance.extract_text_from_clusters_by_position(clusters) == ['word_2', 'word_4']


@patch.object(Extractor, 'extract_text_from_clusters_by_regex')
def test_extract_from_data_by_regex(mock_extract_text_from_clusters_by_regex, extractor_instance):
    mock_extract_text_from_clusters_by_regex.return_value = ['my_result']
    extractor_instance.config[ConfigOptions.TEXT_FILTER_TYPE.value] = TextFilterTypes.REGEX.value
    assert extractor_instance.extract_from_data('', Files.SOURCE.value) == ['my_result']


@patch.object(Extractor, 'extract_text_from_clusters_by_position')
def test_extract_from_data_by_position(mock_extract_text_from_clusters_by_position, extractor_instance):
    mock_extract_text_from_clusters_by_position.return_value = ['my_result']
    extractor_instance.config[ConfigOptions.TEXT_FILTER_TYPE.value] = TextFilterTypes.POSITIONAL.value
    assert extractor_instance.extract_from_data('', Files.SOURCE.value) == ['my_result']


@patch.object(Extractor, 'extract_text_from_clusters_by_combi_search')
def test_extract_from_data_by_combi_search(mock_extract_text_from_clusters_by_combi_search, extractor_instance):
    mock_extract_text_from_clusters_by_combi_search.return_value = ['my_result']
    extractor_instance.config[ConfigOptions.TEXT_FILTER_TYPE.value] = TextFilterTypes.COMBI_SEARCH.value
    assert extractor_instance.extract_from_data('', Files.SOURCE.value) == ['my_result']


@pytest.mark.parametrize(
    'clusters, regex_filters, expected_filtered_clusters',
    [
        # Case 1: Some clusters remain after filtering
        (['abc123', 'xyz89', 'test456', 'hello111', 'finalTest'],
         [r'\d{3}', r'test'],
         ['abc123', 'test456', 'hello111']),
        # Case 2: More restrictive filtering, leaving only 'test456'
        (['abc123', 'xyz89', 'test456', 'hello111', 'finalTest'],
         [r'\d{3}', r'test', r'final'],
         ['test456']),
        # Case 3: All clusters are removed by the regex filters, leaving an empty list
        (['abc123', 'xyz89', 'test456', 'hello111', 'finalTest'],
         [r'^z.*$', r'test'],  # First filter keeps only words starting with 'z'
         [])
    ]
)
@patch.object(Extractor, 'extract_text_from_clusters_by_regex')
def test_extract_text_from_clusters_by_combi_search(mock_extract_text, extractor_instance, clusters, regex_filters, expected_filtered_clusters):
    extractor_instance.config[ConfigOptions.TEXT_FILTER.value] = regex_filters
    extractor_instance.extract_text_from_clusters_by_combi_search(clusters)
    mock_extract_text.assert_called_once_with(expected_filtered_clusters, regex_filters[-1])


def test_extract_from_data_unsupported_filter_type(extractor_instance):
    data = 'saiucdjh1\ndusi2hiuw\n3134ferw\n4waijc\ndjhe56fk7\niuaijaudc'
    extractor_instance.config[ConfigOptions.CLUSTER_FILTER.value] = '\n'
    extractor_instance.config[ConfigOptions.TEXT_FILTER_TYPE.value] = TextFilterTypes.KEYWORD.value
    extractor_instance.config[ConfigOptions.TEXT_FILTER.value] = r'^[^\d]*(\d)'
    with pytest.raises(ValueError, match='Unsupported filter type: %s' % TextFilterTypes.KEYWORD.value):
        extractor_instance.extract_from_data(data, Files.SOURCE.value)


@pytest.mark.parametrize('input_side_effects, clusters,expected_result', [
    (['start', 'end'],
     ['This is the first cluster', 'This is the start cluster',
      'This is another cluster', 'This is the end cluster', 'This is the last cluster'],
     ['This is the start cluster', 'This is another cluster', 'This is the end cluster']),
    (['', ''], ['Cluster one', 'Cluster two', 'Cluster three'], ['Cluster one', 'Cluster two', 'Cluster three']),
    (['nonexistent', ''], ['Cluster one', 'Cluster two', 'Cluster three'],
     ['Cluster one', 'Cluster two', 'Cluster three']),
    (['', 'nonexistent'], ['Cluster one', 'Cluster two', 'Cluster three'],
     ['Cluster one', 'Cluster two', 'Cluster three']),
    (['start', 'nonexistent'], ['Cluster one', 'Cluster start', 'Cluster two', 'Cluster three'],
     ['Cluster start', 'Cluster two', 'Cluster three']),
    (['', 'end'], ['Cluster one', 'Cluster two', 'Cluster end', 'Cluster three'],
     ['Cluster one', 'Cluster two', 'Cluster end']),
])
def test_get_sliced_clusters(extractor_instance, input_side_effects, clusters, expected_result):
    result = extractor_instance.get_sliced_clusters(clusters, input_side_effects[0], input_side_effects[1])
    assert result == expected_result


def test_get_src_clusters_with_slicing(extractor_instance):
    data = 'This is the first cluster\nThis is the start cluster\nThis is another cluster\nThis is the end cluster\nThis is the last cluster'
    expected_result = ['This is the start cluster', 'This is another cluster', 'This is the end cluster']
    extractor_instance.config[ConfigOptions.CLUSTER_FILTER.value] = '\n'
    extractor_instance.config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] = True
    extractor_instance.config[ConfigOptions.SRC_START_CLUSTER_TEXT.value] = 'start'
    extractor_instance.config[ConfigOptions.SRC_END_CLUSTER_TEXT.value] = 'end'
    assert extractor_instance.get_clusters(data, Files.SOURCE.value) == expected_result


def test_get_ref_clusters_with_slicing(extractor_instance):
    data = 'This is the first cluster\nThis is the start cluster\nThis is another cluster\nThis is the end cluster\nThis is the last cluster'
    expected_result = ['This is the start cluster', 'This is another cluster', 'This is the end cluster']
    extractor_instance.config[ConfigOptions.CLUSTER_FILTER.value] = '\n'
    extractor_instance.config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] = True
    extractor_instance.config[ConfigOptions.REF_START_CLUSTER_TEXT.value] = 'start'
    extractor_instance.config[ConfigOptions.REF_END_CLUSTER_TEXT.value] = 'end'
    assert extractor_instance.get_clusters(data, Files.REFERENCE.value) == expected_result
