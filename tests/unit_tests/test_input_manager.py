from io import StringIO
import pytest
try:
    from unittest.mock import patch, mock_open
except ImportError:
    from mock import patch, mock_open

from GenEC.core import ConfigOptions, TextFilterTypes
from GenEC.core.manage_io import InputManager

# Python 2 fallback
try:
    FileNotFoundError
    import builtins
except NameError:
    FileNotFoundError = IOError
    import __builtin__ as builtins


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

MOCK_YAML_CONTENT = {
    'presets': [
        'file1/presetA',
        'file1/presetB',
        'file2/presetC'
    ]
}

MOCK_LOADED_PRESETS_FILE_1 = {
    'presetA': {'key': 'value'},
    'presetB': {'key2': 'value2'}
}

MOCK_LOADED_PRESETS_FILE_2 = {
    'presetB': {'key3': 'value3'}
}


@pytest.fixture
def im_instance():
    return InputManager()


@patch.object(InputManager, 'load_preset', return_value={'key': 'value'})
@patch.object(InputManager, 'parse_preset_param', return_value=('file.yaml', 'presetA'))
def test_init_with_preset_type(mock_parse_preset_param, mock_load_preset):
    im_instance = InputManager({'type': 'preset', 'value': 'fake_path'})
    assert im_instance.preset_file == 'file.yaml'
    assert im_instance.preset_name == 'presetA'
    assert im_instance.config == {'key': 'value'}
    assert not hasattr(im_instance, 'presets')


@patch.object(InputManager, 'load_preset_list', return_value=['presetA', 'presetB'])
def test_init_with_preset_list_type(mock_load_preset_list):
    im_instance = InputManager({'type': 'preset-list', 'value': 'fake_list'})
    assert im_instance.presets == ['presetA', 'presetB']
    assert im_instance.preset_file is None
    assert im_instance.preset_name is None
    assert im_instance.config == {}


def test_init_with_invalid_type():
    with pytest.raises(ValueError, match='not a valid preset parameter type'):
        InputManager({'type': 'invalid', 'value': 'something'})


def test_init_with_no_parameters(im_instance):
    assert im_instance.preset_file is None
    assert im_instance.preset_name is None
    assert im_instance.config == {}


@pytest.mark.parametrize('preset_param, expected_result', [
    ('main_preset', ('main_preset', None)),
    ('folder/main_preset', ('folder', 'main_preset'))])
def test_parse_preset_param(preset_param, expected_result):
    assert InputManager.parse_preset_param(preset_param) == expected_result


@patch.object(InputManager, 'load_preset_file')
@patch.object(InputManager, 'ask_mpc_question')
def test_load_preset_no_preset_name(mock_ask_mpc_question, mock_load_preset_file, im_instance):
    mock_load_preset_file.return_value = MULTIPLE_PRESETS_DATA
    mock_ask_mpc_question.return_value = preset_name = 'main_preset'
    im_instance.preset_name = None
    result = im_instance.load_preset()
    assert result == MULTIPLE_PRESETS_DATA[preset_name]


@patch.object(InputManager, 'load_preset_file')
def test_load_preset_invalid_preset_name(mock_load_preset_file, im_instance):
    mock_load_preset_file.return_value = MULTIPLE_PRESETS_DATA
    im_instance.preset_name = 'non_existing_preset'
    with pytest.raises(ValueError):
        im_instance.load_preset()


@patch.object(InputManager, 'load_preset_file')
def test_load_from_single_preset(mock_load_preset_file, im_instance):
    mock_load_preset_file.return_value = SINGLE_PRESET_DATA
    result = im_instance.load_preset()
    assert result == SINGLE_PRESET_DATA['main_preset']


@pytest.mark.parametrize('preset_name', [
    ('main_preset'),
    ('sub_preset_A')
])
@patch.object(InputManager, 'load_preset_file')
def test_load_from_multiple_presets_existing_preset_name(mock_load_preset_file, im_instance, preset_name):
    mock_load_preset_file.return_value = MULTIPLE_PRESETS_DATA
    im_instance.preset_name = preset_name
    result = im_instance.load_preset()
    assert result == MULTIPLE_PRESETS_DATA[preset_name]


@patch('os.path.exists', return_value=False)
def test_load_preset_file_file_not_found(mock_exists, im_instance):
    im_instance.preset_file = 'mock_file'
    with pytest.raises(FileNotFoundError):
        im_instance.load_preset_file()


@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open, read_data='')
def test_load_preset_file_empty_file(mock_open_file, mock_exists, im_instance):
    im_instance.preset_file = 'mock_file'
    with pytest.raises(ValueError):
        im_instance.load_preset_file()


@pytest.mark.parametrize('preset_data', [
    (SINGLE_PRESET_DATA),
    (MULTIPLE_PRESETS_DATA)
])
@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open)
@patch('yaml.safe_load')
def test_load_preset_file_valid_file(mock_safe_load, mock_open_file, mock_exists, im_instance, preset_data):
    mock_safe_load.return_value = preset_data
    im_instance.preset_file = 'mock_file'
    result = im_instance.load_preset_file()
    assert result == preset_data


@patch('GenEC.utils.read_yaml_file', return_value=MOCK_YAML_CONTENT)
@patch.object(InputManager, 'parse_preset_param', )
@patch.object(InputManager, 'load_presets')
def test_load_preset_list(mock_load_presets, mock_parse_preset_param, mock_read_yaml_file, im_instance):
    mock_load_presets.return_value = {'file1/presetA': {'key': 'value'},
                                      'file1/presetB': {'key2': 'value2'},
                                      'file2/presetC': {'key3': 'value3'}}
    mock_parse_preset_param.side_effect = [('file1', 'presetA'),
                                           ('file1', 'presetB'),
                                           ('file2', 'presetC')]

    presets = im_instance.load_preset_list('preset_list_file')

    assert 'file1/presetA' in presets
    assert 'file1/presetB' in presets
    assert 'file2/presetC' in presets

    expected_presets_list = {
        'file1': ['presetA', 'presetB'],
        'file2': ['presetC']
    }
    mock_load_presets.assert_called_once_with(expected_presets_list)

    mock_parse_preset_param.assert_any_call('file1/presetA')
    mock_parse_preset_param.assert_any_call('file1/presetB')
    mock_parse_preset_param.assert_any_call('file2/presetC')


@patch('GenEC.utils.read_yaml_file', return_value={})
def test_load_preset_list_with_empty_yaml(mock_read_yaml, im_instance):
    with pytest.raises(KeyError, match="'presets'"):
        im_instance.load_preset_list('empty_preset_list')


@patch.object(InputManager, 'load_preset_file', side_effect=[MOCK_LOADED_PRESETS_FILE_1, MOCK_LOADED_PRESETS_FILE_2])
def test_load_presets_with_valid_data(mock_load_preset_file, im_instance):
    presets_list = {
        'file1': ['presetA', 'presetB'],
        'file2': ['presetB']
    }

    result = im_instance.load_presets(presets_list)

    assert len(result) == 3
    assert 'file1/presetA' in result
    assert 'file1/presetB' in result
    assert 'file2/presetB' in result
    assert result['file1/presetA'] == {'key': 'value'}
    assert result['file1/presetB'] == {'key2': 'value2'}
    assert result['file2/presetB'] == {'key3': 'value3'}


@patch.object(InputManager, 'load_preset_file', side_effect=[MOCK_LOADED_PRESETS_FILE_1, MOCK_LOADED_PRESETS_FILE_2])
def test_load_presets_with_missing_preset(mock_load_preset_file, im_instance):
    presets_list = {
        'file1': ['presetA', 'presetX'],
        'file2': ['presetB']
    }

    result = im_instance.load_presets(presets_list)
    assert len(result) == 2
    assert 'file1/presetA' in result
    assert 'file1/presetX' not in result
    assert 'file2/presetB' in result
    assert result['file1/presetA'] == {'key': 'value'}
    assert result['file2/presetB'] == {'key3': 'value3'}


@patch.object(InputManager, 'load_preset_file', return_value={})
def test_load_presets_with_empty_file(mock_load_preset_file, im_instance):
    presets_list = {
        'file1': ['presetA'],
    }
    with pytest.raises(ValueError, match='None of the provided presets were found.'):
        im_instance.load_presets(presets_list)


@patch.object(InputManager, 'load_preset_file', side_effect=[MOCK_LOADED_PRESETS_FILE_1])
def test_load_presets_with_invalid_data(mock_load_preset_file, im_instance):
    presets_list = {
        'file1': ['invalidPreset'],
    }
    with pytest.raises(ValueError, match='None of the provided presets were found.'):
        im_instance.load_presets(presets_list)


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


@pytest.mark.parametrize('mock_side_effect, mock_output', [
    (['regex_1', 'y', 'regex_2', 'done'], ['regex_1', 'regex_2']),
    (['regex_1', 'n'], ['regex_1']),
    (['regex_1', 'Y', 'regex_2', 'YeS', 'regex_3', ''], ['regex_1', 'regex_2', 'regex_3']),
])
@patch.object(InputManager, 'ask_open_question')
def test_request_COMBI_SEARCH_filter_type(mock_input, mock_side_effect, mock_output, im_instance):
    mock_input.side_effect = mock_side_effect
    im_instance.config[ConfigOptions.TEXT_FILTER_TYPE.value] = TextFilterTypes.COMBI_SEARCH.value
    assert im_instance.request_text_filter() == mock_output


@pytest.mark.parametrize('filter_type', [
    (TextFilterTypes.KEYWORD.value),
    (TextFilterTypes.SPLIT_KEYWORDS.value)])
def test_request_unsupported_filter_type(im_instance, filter_type):
    im_instance.config[ConfigOptions.TEXT_FILTER_TYPE.value] = filter_type
    with pytest.raises(ValueError, match='Unsupported filter type: %s' % filter_type):
        im_instance.request_text_filter()
