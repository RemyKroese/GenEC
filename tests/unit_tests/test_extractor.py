"""Unit tests for GenEC Extractor class."""
from __future__ import annotations

from unittest.mock import patch, MagicMock, Mock
import pytest

from GenEC.core import FileID, TextFilterTypes
from GenEC.core.analyze import Extractor
from GenEC.core.configuration import RegexConfiguration, RegexListConfiguration, PositionalConfiguration, BaseConfiguration
from GenEC.core.specs import PositionalFilterType

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
def regex_config() -> RegexConfiguration:
    """Create a RegexConfiguration for testing."""
    return RegexConfiguration(
        cluster_filter='\n',
        should_slice_clusters=False,
        text_filter='test.*'
    )


@pytest.fixture
def extractor_instance() -> Extractor:
    return Extractor()


@pytest.mark.unit
@pytest.mark.parametrize('data, cluster_filter, expected_result', [
    (BASIC_TEXT, '\n', ['a b c', 'd e', 'f g h i', 'j']),
    (WHITELINES_TEXT, '\n\n', ['a b c\nd e', 'f g h i', 'j\nk l m n o p\nq'])])
def test_get_clusters(extractor_instance: Extractor,
                      data: str, cluster_filter: str, expected_result: list[str]) -> None:
    config = RegexConfiguration(
        cluster_filter=cluster_filter,
        should_slice_clusters=False,
        text_filter='test.*'
    )
    assert extractor_instance.get_clusters(config, data, FileID.SOURCE) == expected_result


@pytest.mark.unit
@pytest.mark.parametrize("filter_type", [
    TextFilterTypes.REGEX,
    TextFilterTypes.REGEX_LIST,
    TextFilterTypes.POSITIONAL,
])
@patch("GenEC.core.extraction_filters.get_extractor")
def test_extract_from_data(mock_get_extractor: Mock, filter_type: TextFilterTypes,
                           extractor_instance: Extractor) -> None:
    fake_extractor: MagicMock = MagicMock()
    fake_extractor.extract.return_value = ['my_result']
    mock_get_extractor.return_value = fake_extractor

    # Create appropriate config based on filter type
    config: BaseConfiguration
    if filter_type == TextFilterTypes.REGEX:
        config = RegexConfiguration(
            cluster_filter='\n',
            should_slice_clusters=False,
            text_filter='test.*'
        )
    elif filter_type == TextFilterTypes.REGEX_LIST:
        config = RegexListConfiguration(
            cluster_filter='\n',
            should_slice_clusters=False,
            text_filter=['test.*', 'pattern']
        )
    else:  # POSITIONAL
        config = PositionalConfiguration(
            cluster_filter='\n',
            should_slice_clusters=False,
            text_filter=PositionalFilterType(separator=' ', line=1, occurrence=1)
        )

    result: list[str] = extractor_instance.extract_from_data(config, "some data", FileID.SOURCE)

    assert result == ['my_result']
    mock_get_extractor.assert_called_once_with(filter_type.value, config)
    fake_extractor.extract.assert_called_once()


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
def test_get_src_clusters_with_slicing(extractor_instance: Extractor) -> None:
    data: str = 'This is the first cluster\nThis is the start cluster\nThis is another cluster\nThis is the end cluster\nThis is the last cluster'
    expected_result: list[str] = [
        'This is the start cluster',
        'This is another cluster',
        'This is the end cluster']
    config = RegexConfiguration(
        cluster_filter='\n',
        should_slice_clusters=True,
        text_filter='test.*',
        src_start_cluster_text='start',
        src_end_cluster_text='end'
    )
    assert extractor_instance.get_clusters(config, data, FileID.SOURCE) == expected_result


@pytest.mark.unit
def test_get_ref_clusters_with_slicing(extractor_instance: Extractor) -> None:
    data: str = 'This is the first cluster\nThis is the start cluster\nThis is another cluster\nThis is the end cluster\nThis is the last cluster'
    expected_result: list[str] = [
        'This is the start cluster',
        'This is another cluster',
        'This is the end cluster']
    config = RegexConfiguration(
        cluster_filter='\n',
        should_slice_clusters=True,
        text_filter='test.*',
        ref_start_cluster_text='start',
        ref_end_cluster_text='end'
    )
    assert extractor_instance.get_clusters(config, data, FileID.REFERENCE) == expected_result
