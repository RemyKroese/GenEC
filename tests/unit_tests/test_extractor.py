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


def test_extract_text_from_clusters_by_regex(extractor_instance):
    clusters = ['saiucdjh1', 'dusi2hiuw', '3134ferw', '4waijc', 'djhe56fk7', 'iuaijaudc']
    extractor_instance.config[ConfigOptions.TEXT_FILTER.value] = r'^[^\d]*(\d)'
    assert extractor_instance.extract_text_from_clusters_by_regex(clusters) == ['1', '2', '3', '4', '5']


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
