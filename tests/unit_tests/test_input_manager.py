from io import StringIO
import pytest
from unittest.mock import patch

from GenEC.core import ConfigOptions, TextFilterTypes, PositionalFilterType
from GenEC.core.manage_io import InputManager
from GenEC.core.types.preset_config import Initialized


@patch.object(InputManager, 'ask_open_question')
def test_set_cluster_filter(mock_ask_open_question):
    mock_ask_open_question.return_value = ';'
    config = Initialized(cluster_filter=None)
    assert InputManager.set_cluster_filter(config) == ';'


def test_set_cluster_filter_from_config():
    config = Initialized(cluster_filter='\n')
    assert InputManager.set_cluster_filter(config) == '\n'


@patch.object(InputManager, 'ask_mpc_question')
def test_set_text_filter_type(mock_ask_mpc_question):
    mock_ask_mpc_question.return_value = 'type1'
    config = Initialized(text_filter_type=None)
    assert InputManager.set_text_filter_type(config) == 'type1'


@patch.object(InputManager, 'request_text_filter')
def test_set_text_filter(mock_request_text_filter):
    mock_request_text_filter.return_value = 'filter1'
    config = Initialized(text_filter=None)
    assert InputManager.set_text_filter(config) == 'filter1'


@pytest.mark.parametrize('response, expected', [
    ('yes', True),
    ('no', False)
])
@patch.object(InputManager, 'ask_open_question')
def test_set_should_slice_clusters(mock_ask_open_question, response, expected):
    mock_ask_open_question.return_value = response
    config = Initialized(should_slice_clusters=None)
    assert InputManager.set_should_slice_clusters(config) == expected


@pytest.mark.parametrize('config_option, start_end, src_ref', [
    (ConfigOptions.SRC_START_CLUSTER_TEXT.value, 'start', 'SRC'),
    (ConfigOptions.SRC_END_CLUSTER_TEXT.value, 'end', 'SRC'),
    (ConfigOptions.REF_START_CLUSTER_TEXT.value, 'start', 'REF'),
    (ConfigOptions.REF_END_CLUSTER_TEXT.value, 'end', 'REF'),
])
@patch.object(InputManager, 'ask_open_question')
def test_set_cluster_text(mock_ask_open_question, config_option, start_end, src_ref):
    mock_ask_open_question.return_value = 'some text'
    config = Initialized()
    assert InputManager.set_cluster_text(config, config_option, start_end, src_ref) == 'some text'


@patch('builtins.input', return_value='user_input')
def test_ask_open_question(mock_input):
    assert InputManager.ask_open_question('Prompt: ') == 'user_input'


@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_ask_mpc_question_valid_choice(mock_input, mock_stdout):
    mock_input.return_value = '2\n'
    assert InputManager.ask_mpc_question('Choose a number:', ['Option 1', 'Option 2', 'Option 3']) == 'Option 2'
    assert mock_stdout.getvalue().strip() == 'Choose a number:\n0. Exit\n1. Option 1\n2. Option 2\n3. Option 3'


@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_ask_mpc_question_invalid_choice(mock_input, mock_stdout):
    mock_input.side_effect = ['5\n', 'invalid input\n', '1\n']
    assert InputManager.ask_mpc_question('Choose a number:', ['Option 1', 'Option 2']) == 'Option 1'
    assert 'Please enter a valid number.' in mock_stdout.getvalue().strip()


@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_ask_mpc_question_exit(mock_input, mock_stdout):
    mock_input.return_value = '0\n'
    with pytest.raises(SystemExit):
        InputManager.ask_mpc_question('Choose a number:', ['Option 1', 'Option 2'])
    assert mock_stdout.getvalue().strip() == 'Choose a number:\n0. Exit\n1. Option 1\n2. Option 2'


@patch.object(InputManager, 'ask_open_question')
def test_request_REGEX_filter_type(mock_input):
    mock_input.return_value = USER_INPUT = 'my_filter'
    config = Initialized(text_filter_type=TextFilterTypes.REGEX.value)
    assert InputManager.request_text_filter(config) == USER_INPUT


@pytest.mark.parametrize('mock_side_effect, mock_output', [
    ([' ', '2', '4'], [' ', 2, 4]),
    (['', '3', '8'], [' ', 3, 8]),
    (['ABC', '4', '2'], ['ABC', 4, 2])
])
@patch.object(InputManager, 'ask_open_question')
def test_request_POSITIONAL_filter_type(mock_input, mock_side_effect, mock_output):
    mock_input.side_effect = mock_side_effect
    config = Initialized(text_filter_type=TextFilterTypes.POSITIONAL.value)
    assert InputManager.request_text_filter(config) == PositionalFilterType(separator=mock_output[0], line=mock_output[1], occurrence=mock_output[2])


@pytest.mark.parametrize('mock_side_effect, mock_output', [
    (['regex_1', 'y', 'regex_2', 'done'], ['regex_1', 'regex_2']),
    (['regex_1', 'n'], ['regex_1']),
    (['regex_1', 'Y', 'regex_2', 'YeS', 'regex_3', ''], ['regex_1', 'regex_2', 'regex_3']),
])
@patch.object(InputManager, 'ask_open_question')
def test_request_REGEX_LIST_filter_type(mock_input, mock_side_effect, mock_output):
    mock_input.side_effect = mock_side_effect
    config = Initialized(text_filter_type=TextFilterTypes.REGEX_LIST.value)
    assert InputManager.request_text_filter(config) == mock_output


@pytest.mark.parametrize('filter_type', [
    (TextFilterTypes.KEYWORD.value),
    (TextFilterTypes.SPLIT_KEYWORDS.value)])
def test_request_unsupported_filter_type(filter_type):
    config = Initialized(text_filter_type=filter_type)
    with pytest.raises(ValueError, match='Unsupported filter type: %s' % filter_type):
        InputManager.request_text_filter(config)
