"""Unit tests for GenEC Extractor class."""
from __future__ import annotations

from typing import Any, cast
from unittest.mock import patch, MagicMock, Mock
import pytest

from GenEC.core import ConfigOptions, FileID, TextFilterTypes
from GenEC.core.analyze import Extractor
from GenEC.core.types.preset_config import Finalized

BASIC_TEXT: str = '''a b c
d e
f g h i
j'''

WHITELINES_TEXT: str = '''a b c
d e

f g h i

j
k l m n o p
q'''


@pytest.fixture
def config_fixture() -> dict[str, Any]:
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


@pytest.fixture
def extractor_instance() -> Extractor:
    return Extractor()


@pytest.mark.unit
@pytest.mark.parametrize('data, cluster_filter, expected_result', [
    (BASIC_TEXT, '\n', ['a b c', 'd e', 'f g h i', 'j']),
    (WHITELINES_TEXT, '\n\n', ['a b c\nd e', 'f g h i', 'j\nk l m n o p\nq'])])
def test_get_clusters(extractor_instance: Extractor, config_fixture: dict[str, Any],
                      data: str, cluster_filter: str, expected_result: list[str]) -> None:
    config: dict[str, Any] = config_fixture.copy()
    config[ConfigOptions.CLUSTER_FILTER.value] = cluster_filter
    assert extractor_instance.get_clusters(
        cast(Finalized, config), data, FileID.SOURCE) == expected_result


@pytest.mark.unit
@pytest.mark.parametrize("filter_type", [
    TextFilterTypes.REGEX,
    TextFilterTypes.POSITIONAL,
    TextFilterTypes.REGEX_LIST,
])
@patch("GenEC.core.extraction_filters.get_extractor")
def test_extract_from_data(mock_get_extractor: Mock, filter_type: TextFilterTypes,
                           extractor_instance: Extractor, config_fixture: dict[str, Any]) -> None:
    fake_extractor: MagicMock = MagicMock()
    fake_extractor.extract.return_value = ['my_result']
    mock_get_extractor.return_value = fake_extractor

    config: dict[str, Any] = config_fixture.copy()
    config[ConfigOptions.TEXT_FILTER_TYPE.value] = filter_type.value
    result: list[str] = extractor_instance.extract_from_data(
        cast(Finalized, config), "some data", FileID.SOURCE)

    assert result == ['my_result']
    mock_get_extractor.assert_called_once_with(filter_type.value, config)
    fake_extractor.extract.assert_called_once()


@pytest.mark.unit
def test_extract_from_data_unsupported_filter_type(
        extractor_instance: Extractor, config_fixture: dict[str, Any]) -> None:
    data: str = 'saiucdjh1\ndusi2hiuw\n3134ferw\n4waijc\ndjhe56fk7\niuaijaudc'
    config: dict[str, Any] = config_fixture.copy()
    config[ConfigOptions.CLUSTER_FILTER.value] = '\n'
    config[ConfigOptions.TEXT_FILTER_TYPE.value] = TextFilterTypes.KEYWORD.value
    config[ConfigOptions.TEXT_FILTER.value] = r'^[^\d]*(\d)'
    with pytest.raises(ValueError, match='Unsupported filter type: %s' % TextFilterTypes.KEYWORD.value):
        extractor_instance.extract_from_data(
            cast(Finalized, config), data, FileID.SOURCE)


@pytest.mark.unit
@pytest.mark.parametrize('input_side_effects, clusters,expected_result', [
    (['start', 'end'],
     ['This is the first cluster', 'This is the start cluster',
      'This is another cluster', 'This is the end cluster', 'This is the last cluster'],
     ['This is the start cluster', 'This is another cluster', 'This is the end cluster']),
    (['', ''], ['Cluster one', 'Cluster two', 'Cluster three'],
     ['Cluster one', 'Cluster two', 'Cluster three']),
    (['nonexistent', ''], ['Cluster one', 'Cluster two', 'Cluster three'],
     ['Cluster one', 'Cluster two', 'Cluster three']),
    (['', 'nonexistent'], ['Cluster one', 'Cluster two', 'Cluster three'],
     ['Cluster one', 'Cluster two', 'Cluster three']),
    (['start', 'nonexistent'], ['Cluster one', 'Cluster start', 'Cluster two', 'Cluster three'],
     ['Cluster start', 'Cluster two', 'Cluster three']),
    (['', 'end'], ['Cluster one', 'Cluster two', 'Cluster end', 'Cluster three'],
     ['Cluster one', 'Cluster two', 'Cluster end']),
])
def test_get_sliced_clusters(extractor_instance: Extractor,
                             input_side_effects: list[str], clusters: list[str], expected_result: list[str]) -> None:
    result: list[str] = extractor_instance.get_sliced_clusters(
        clusters, input_side_effects[0], input_side_effects[1])
    assert result == expected_result


@pytest.mark.unit
def test_get_src_clusters_with_slicing(
        extractor_instance: Extractor, config_fixture: dict[str, Any]) -> None:
    data: str = 'This is the first cluster\nThis is the start cluster\nThis is another cluster\nThis is the end cluster\nThis is the last cluster'
    expected_result: list[str] = [
        'This is the start cluster',
        'This is another cluster',
        'This is the end cluster']
    config: dict[str, Any] = config_fixture.copy()
    config[ConfigOptions.CLUSTER_FILTER.value] = '\n'
    config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] = True
    config[ConfigOptions.SRC_START_CLUSTER_TEXT.value] = 'start'
    config[ConfigOptions.SRC_END_CLUSTER_TEXT.value] = 'end'
    assert extractor_instance.get_clusters(
        cast(Finalized, config), data, FileID.SOURCE) == expected_result


@pytest.mark.unit
def test_get_ref_clusters_with_slicing(
        extractor_instance: Extractor, config_fixture: dict[str, Any]) -> None:
    data: str = 'This is the first cluster\nThis is the start cluster\nThis is another cluster\nThis is the end cluster\nThis is the last cluster'
    expected_result: list[str] = [
        'This is the start cluster',
        'This is another cluster',
        'This is the end cluster']
    config: dict[str, Any] = config_fixture.copy()
    config[ConfigOptions.CLUSTER_FILTER.value] = '\n'
    config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] = True
    config[ConfigOptions.REF_START_CLUSTER_TEXT.value] = 'start'
    config[ConfigOptions.REF_END_CLUSTER_TEXT.value] = 'end'
    assert extractor_instance.get_clusters(
        cast(Finalized, config), data, FileID.REFERENCE) == expected_result
