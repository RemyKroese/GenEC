from mock import patch
import pytest

from src.genec import Extractor

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


@pytest.mark.parametrize('data, cluster_filter, expected_result', [
    (BASIC_TEXT, '\n', ['a b c', 'd e', 'f g h i', 'j']),
    (WHITELINES_TEXT, '\n\n', ['a b c\nd e', 'f g h i', 'j\nk l m n o p\nq'])])
@patch('builtins.input')
def test_get_clusters(mock_input, data, cluster_filter, expected_result):
    mock_input.return_value = cluster_filter
    e = Extractor()
    e.request_cluster_filter()
    assert e.get_clusters(data) == expected_result


@pytest.mark.parametrize('user_input, expected_result', [
    (1, Extractor.TextFilterTypes.REGEX),
    (2, Extractor.TextFilterTypes.KEYWORD),
    (3, Extractor.TextFilterTypes.POSITIONAL),
    (4, Extractor.TextFilterTypes.SPLIT_KEYWORDS)])
@patch('builtins.input')
def test_request_text_filter_type(mock_input, user_input, expected_result):
    mock_input.return_value = user_input
    e = Extractor()
    filter_type = e.request_text_filter_type()
    assert filter_type == expected_result


@pytest.mark.parametrize('user_input, expected_result', [
    (2, Extractor.TextFilterTypes.KEYWORD.name),
    (3, Extractor.TextFilterTypes.POSITIONAL.name),
    (4, Extractor.TextFilterTypes.SPLIT_KEYWORDS.name)])
@patch('builtins.input')
def test_request_unsupported_filter_type(mock_input, user_input, expected_result):
    mock_input.return_value = user_input
    e = Extractor()
    with pytest.raises(ValueError, match='Unsupported filter type: %s' % expected_result):
        e.request_text_filter()


@patch('builtins.input')
def test_request_invalid_filter_type(mock_input):
    mock_input.return_value = 999
    e = Extractor()
    with pytest.raises(ValueError, match='999 is not a valid Extractor.TextFilterTypes'):
        e.request_text_filter()


@pytest.mark.parametrize('user_input, expected_filter', [
    ('ab*', 'ab*'),
    ('[a-z]+', '[a-z]+'),
    ('""', '""'),
    (r'/^[^\d]*(\d+)/', r'/^[^\d]*(\d+)/')])
@patch('builtins.input')
@patch('src.genec.Extractor.request_text_filter_type', return_value=Extractor.TextFilterTypes(1))
def test_request_text_filter_regex(mock_request, mock_input, user_input, expected_filter):
    mock_input.return_value = user_input
    e = Extractor()
    e.request_text_filter()
    assert e.text_filter == {'filter_type': Extractor.TextFilterTypes.REGEX, 'filter': expected_filter}


def test_extract_text_from_clusters_by_regex():
    clusters = ['saiucdjh1', 'dusi2hiuw', '3134ferw', '4waijc', 'djhe56fk7', 'iuaijaudc']
    e = Extractor()
    e.text_filter = {'filter_type': Extractor.TextFilterTypes.REGEX, 'filter': r'^[^\d]*(\d)'}  # 1st number in group
    assert e.extract_text_from_clusters_by_regex(clusters) == ['1', '2', '3', '4', '5']


@patch('builtins.input')
def test_extract_from_data(mock_input):
    mock_input.return_value = '\n'
    data = 'saiucdjh1\ndusi2hiuw\n3134ferw\n4waijc\ndjhe56fk7\niuaijaudc'
    e = Extractor()
    e.request_cluster_filter()
    e.text_filter = {'filter_type': Extractor.TextFilterTypes.REGEX, 'filter': r'^[^\d]*(\d)'}  # 1st number in group
    assert e.extract_from_data(data) == ['1', '2', '3', '4', '5']


@patch('builtins.input')
def test_extract_from_data_unsupported_filter_type(mock_input):
    mock_input.return_value = '\n'
    data = 'saiucdjh1\ndusi2hiuw\n3134ferw\n4waijc\ndjhe56fk7\niuaijaudc'
    e = Extractor()
    e.request_cluster_filter()
    e.text_filter = {'filter_type': Extractor.TextFilterTypes.KEYWORD, 'filter': r'^[^\d]*(\d)'}  # 1st number in group
    with pytest.raises(ValueError, match='Unsupported filter type: KEYWORD'):
        e.extract_from_data(data)
