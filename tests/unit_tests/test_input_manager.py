from io import StringIO
import pytest
from unittest.mock import patch, mock_open

from GenEC.core.analyze import InputManager, ConfigOptions, TextFilterTypes

# Mock preset data for testing
SINGLE_PRESET_DATA = {
    'main_preset': {
        'cluster_filter': '',
        'text_filter_type': 0,
        'text_filter': '',
        'should_slice_clusters': False,
        'src_start_cluster_text': '',
        'source_end_cluster_text': '',
        'ref_start_cluster_text': '',
        'ref_end_cluster_text': ''
    }
}
MULTIPLE_PRESETS_DATA = {
    'main_preset': {
        'cluster_filter': '',
        'text_filter_type': 0,
        'text_filter': '',
        'should_slice_clusters': False,
        'src_start_cluster_text': '',
        'source_end_cluster_text': '',
        'ref_start_cluster_text': '',
        'ref_end_cluster_text': ''
    },
    'sub_preset_A': {
        'cluster_filter': '',
        'text_filter_type': 0,
        'text_filter': '',
        'should_slice_clusters': True,
        'src_start_cluster_text': '',
        'source_end_cluster_text': '',
        'ref_start_cluster_text': '',
        'ref_end_cluster_text': ''
    },
    'sub_preset_B': {
        'cluster_filter': '\\n',
        'text_filter_type': 1,
        'text_filter': '[a-zA-z]{4}',
        'should_slice_clusters': False,
        'src_start_cluster_text': '',
        'source_end_cluster_text': '',
        'ref_start_cluster_text': '',
        'ref_end_cluster_text': ''
    }
}


@pytest.fixture
def im_instance():
    return InputManager()


@pytest.mark.parametrize('preset_param, expected_result', [
    ('main_preset', ('main_preset', None)),
    ('folder/main_preset', ('folder', 'main_preset'))])
def test_parse_preset_param(preset_param, expected_result):
    assert InputManager.parse_preset_param(preset_param) == expected_result


@patch.object(InputManager, 'load_presets_file')
@patch.object(InputManager, 'ask_mpc_question')
def test_load_preset_no_preset_name(mock_ask_mpc_question, mock_load_presets_file, im_instance):
    mock_load_presets_file.return_value = MULTIPLE_PRESETS_DATA
    mock_ask_mpc_question.return_value = preset_name = 'main_preset'
    im_instance.preset_name = None
    result = im_instance.load_preset()
    assert result == MULTIPLE_PRESETS_DATA[preset_name]


@patch.object(InputManager, 'load_presets_file')
def test_load_preset_invalid_preset_name(mock_load_presets_file, im_instance):
    mock_load_presets_file.return_value = MULTIPLE_PRESETS_DATA
    im_instance.preset_name = 'non_existing_preset'
    with pytest.raises(ValueError):
        im_instance.load_preset()


@patch.object(InputManager, 'load_presets_file')
def test_load_from_single_preset(mock_load_presets_file, im_instance):
    mock_load_presets_file.return_value = SINGLE_PRESET_DATA
    result = im_instance.load_preset()
    assert result == SINGLE_PRESET_DATA['main_preset']


@pytest.mark.parametrize('preset_name', [
    ('main_preset'),
    ('sub_preset_A')
])
@patch.object(InputManager, 'load_presets_file')
def test_load_from_multiple_presets_existing_preset_name(mock_load_presets_file, im_instance, preset_name):
    mock_load_presets_file.return_value = MULTIPLE_PRESETS_DATA
    im_instance.preset_name = preset_name
    result = im_instance.load_preset()
    assert result == MULTIPLE_PRESETS_DATA[preset_name]


@patch('os.path.exists', return_value=False)
def test_load_presets_file_file_not_found(mock_exists, im_instance):
    im_instance.preset_file = 'mock_file'
    with pytest.raises(FileNotFoundError):
        im_instance.load_presets_file()


@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open, read_data='')
def test_load_presets_file_empty_file(mock_open_file, mock_exists, im_instance):
    im_instance.preset_file = 'mock_file'
    with pytest.raises(ValueError):
        im_instance.load_presets_file()


@pytest.mark.parametrize('preset_data', [
    (SINGLE_PRESET_DATA),
    (MULTIPLE_PRESETS_DATA)
])
@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open)
@patch('yaml.safe_load')
def test_load_presets_file_valid_file(mock_safe_load, mock_open_file, mock_exists, im_instance, preset_data):
    mock_safe_load.return_value = preset_data
    im_instance.preset_file = 'mock_file'
    result = im_instance.load_presets_file()
    assert result == preset_data


@patch.object(InputManager, 'ask_open_question')
def test_set_cluster_filter(mock_ask_open_question, im_instance):
    mock_ask_open_question.return_value = ';'
    im_instance.set_cluster_filter()
    assert im_instance.config[ConfigOptions.CLUSTER_FILTER.value] == ';'


def test_set_cluster_filter_from_config(im_instance):
    im_instance.config[ConfigOptions.CLUSTER_FILTER.value] = '\n'
    im_instance.set_cluster_filter()
    assert im_instance.config[ConfigOptions.CLUSTER_FILTER.value] == '\n'


@patch.object(InputManager, 'ask_mpc_question')
def test_set_text_filter_type(mock_ask_mpc_question, im_instance):
    mock_ask_mpc_question.return_value = 'type1'
    im_instance.set_text_filter_type()
    assert im_instance.config[ConfigOptions.TEXT_FILTER_TYPE.value] == 'type1'


@patch.object(InputManager, 'request_text_filter')
def test_set_text_filter(mock_request_text_filter, im_instance):
    mock_request_text_filter.return_value = 'filter1'
    im_instance.set_text_filter()
    assert im_instance.config[ConfigOptions.TEXT_FILTER.value] == 'filter1'


@pytest.mark.parametrize('response, expected', [
    ('yes', True),
    ('no', False)
])
@patch.object(InputManager, 'ask_open_question')
def test_set_should_slice_clusters(mock_ask_open_question, response, expected, im_instance):
    mock_ask_open_question.return_value = response
    im_instance.set_should_slice_clusters()

    assert im_instance.config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] == expected


@pytest.mark.parametrize('config_option, start_end, src_ref', [
    (ConfigOptions.SRC_START_CLUSTER_TEXT.value, 'start', 'SRC'),
    (ConfigOptions.SRC_END_CLUSTER_TEXT.value, 'end', 'SRC'),
    (ConfigOptions.REF_START_CLUSTER_TEXT.value, 'start', 'REF'),
    (ConfigOptions.REF_END_CLUSTER_TEXT.value, 'end', 'REF'),
])
@patch.object(InputManager, 'ask_open_question')
def test_set_cluster_text(mock_ask_open_question, config_option, start_end, src_ref, im_instance):
    mock_ask_open_question.return_value = 'some text'
    im_instance.set_cluster_text(config_option, start_end, src_ref)
    assert im_instance.config[config_option] == 'some text'


@patch('builtins.input', return_value='user_input')
def test_ask_open_question(mock_input):
    result = InputManager.ask_open_question('Prompt: ')
    assert result == 'user_input'


@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_ask_mpc_question_valid_choice(mock_input, mock_stdout):
    mock_input.return_value = '2\n'

    user_choice = InputManager.ask_mpc_question('Choose a number:', ['Option 1', 'Option 2', 'Option 3'])

    output = mock_stdout.getvalue().strip()
    assert output == 'Choose a number:\n0. Exit\n1. Option 1\n2. Option 2\n3. Option 3'
    assert user_choice == 'Option 2'


@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_ask_mpc_question_invalid_choice(mock_input, mock_stdout):
    mock_input.side_effect = ['5\n', 'invalid input\n', '1\n']

    user_choice = InputManager.ask_mpc_question('Choose a number:', ['Option 1', 'Option 2'])

    output = mock_stdout.getvalue().strip()
    assert 'Please enter a valid number.' in output
    assert user_choice == 'Option 1'


@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_ask_mpc_question_exit(mock_input, mock_stdout):
    mock_input.return_value = '0\n'

    with pytest.raises(SystemExit):
        InputManager.ask_mpc_question('Choose a number:', ['Option 1', 'Option 2'])

    output = mock_stdout.getvalue().strip()
    assert output == 'Choose a number:\n0. Exit\n1. Option 1\n2. Option 2'


@patch.object(InputManager, 'ask_open_question')
def test_request_REGEX_filter_type(mock_input, im_instance):
    mock_input.return_value = USER_INPUT = 'my_filter'
    im_instance.config[ConfigOptions.TEXT_FILTER_TYPE.value] = TextFilterTypes.REGEX.value
    assert im_instance.request_text_filter() == USER_INPUT


@pytest.mark.parametrize('mock_side_effect, mock_output', [
    ([' ', '2', '4'], [' ', 2, 4]),
    (['', '3', '8'], [' ', 3, 8]),
    (['ABC', '4', '2'], ['ABC', 4, 2])
])
@patch.object(InputManager, 'ask_open_question')
def test_request_POSITIONAL_filter_type(mock_input, mock_side_effect, mock_output, im_instance):
    mock_input.side_effect = mock_side_effect
    im_instance.config[ConfigOptions.TEXT_FILTER_TYPE.value] = TextFilterTypes.POSITIONAL.value
    assert im_instance.request_text_filter() == {'separator': mock_output[0], 'line': mock_output[1], 'occurrence': mock_output[2]}


@pytest.mark.parametrize('filter_type', [
    (TextFilterTypes.KEYWORD.value),
    (TextFilterTypes.SPLIT_KEYWORDS.value)])
def test_request_unsupported_filter_type(im_instance, filter_type):
    im_instance.config[ConfigOptions.TEXT_FILTER_TYPE.value] = filter_type
    with pytest.raises(ValueError, match='Unsupported filter type: %s' % filter_type):
        im_instance.request_text_filter()
