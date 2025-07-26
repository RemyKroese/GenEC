import pytest
from unittest.mock import patch, MagicMock

from GenEC.core import ConfigOptions, FileID, TextFilterTypes
from GenEC.core.analyze import Extractor

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
    assert extractor_instance.get_clusters(data, FileID.SOURCE) == expected_result


@pytest.mark.parametrize("filter_type", [
    TextFilterTypes.REGEX,
    TextFilterTypes.POSITIONAL,
    TextFilterTypes.COMBI_SEARCH,
])
@patch("GenEC.core.extraction_filters.get_extractor")
def test_extract_from_data(mock_get_extractor, filter_type, extractor_instance):
    fake_extractor = MagicMock()
    fake_extractor.extract.return_value = ['my_result']
    mock_get_extractor.return_value = fake_extractor

    extractor_instance.config[ConfigOptions.TEXT_FILTER_TYPE.value] = filter_type.value
    result = extractor_instance.extract_from_data("some data", FileID.SOURCE)

    assert result == ['my_result']
    mock_get_extractor.assert_called_once_with(filter_type.value, extractor_instance.config)
    fake_extractor.extract.assert_called_once()


def test_extract_from_data_unsupported_filter_type(extractor_instance):
    data = 'saiucdjh1\ndusi2hiuw\n3134ferw\n4waijc\ndjhe56fk7\niuaijaudc'
    extractor_instance.config[ConfigOptions.CLUSTER_FILTER.value] = '\n'
    extractor_instance.config[ConfigOptions.TEXT_FILTER_TYPE.value] = TextFilterTypes.KEYWORD.value
    extractor_instance.config[ConfigOptions.TEXT_FILTER.value] = r'^[^\d]*(\d)'
    with pytest.raises(ValueError, match='Unsupported filter type: %s' % TextFilterTypes.KEYWORD.value):
        extractor_instance.extract_from_data(data, FileID.SOURCE)


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
    assert extractor_instance.get_clusters(data, FileID.SOURCE) == expected_result


def test_get_ref_clusters_with_slicing(extractor_instance):
    data = 'This is the first cluster\nThis is the start cluster\nThis is another cluster\nThis is the end cluster\nThis is the last cluster'
    expected_result = ['This is the start cluster', 'This is another cluster', 'This is the end cluster']
    extractor_instance.config[ConfigOptions.CLUSTER_FILTER.value] = '\n'
    extractor_instance.config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] = True
    extractor_instance.config[ConfigOptions.REF_START_CLUSTER_TEXT.value] = 'start'
    extractor_instance.config[ConfigOptions.REF_END_CLUSTER_TEXT.value] = 'end'
    assert extractor_instance.get_clusters(data, FileID.REFERENCE) == expected_result
