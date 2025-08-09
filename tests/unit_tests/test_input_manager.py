from io import StringIO
import pytest
from unittest.mock import patch, mock_open

from GenEC.core import ConfigOptions, TextFilterTypes, PositionalFilterType
from GenEC.core.manage_io import InputManager, PresetConfigInitialized


EMPTY_CONFIG = PresetConfigInitialized(
            cluster_filter=None,
            text_filter_type=None,
            text_filter=None,
            should_slice_clusters=None,
            src_start_cluster_text=None,
            source_end_cluster_text=None,
            ref_start_cluster_text=None,
            ref_end_cluster_text=None)

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
def im_instance() -> InputManager:
    return InputManager()


@patch.object(InputManager, 'load_preset', return_value={'key': 'value'})
@patch.object(InputManager, 'parse_preset_param', return_value=('file.yaml', 'presetA'))
def test_init_with_preset_type(mock_parse_preset_param, mock_load_preset):
    input_manager = InputManager({'type': 'preset', 'value': 'fake_path'})
    assert input_manager.preset_file == 'file.yaml'
    assert input_manager.preset_name == 'presetA'
    assert input_manager.config == {'key': 'value'}
    assert not hasattr(input_manager, 'presets')


@patch.object(InputManager, 'load_presets')
def test_init_with_preset_list_type(mock_load_presets):
    input_manager = InputManager({'type': 'preset-list', 'value': 'fake_list'})
    assert input_manager.preset_file == ''
    assert input_manager.preset_name == ''
    assert input_manager.config == EMPTY_CONFIG


def test_init_with_invalid_type():
    with pytest.raises(ValueError, match='not a valid preset parameter type'):
        InputManager({'type': 'invalid', 'value': 'something'})


def test_init_with_no_parameters(im_instance):
    assert im_instance.preset_file == ''
    assert im_instance.preset_name == ''
    assert im_instance.config == EMPTY_CONFIG


@pytest.mark.parametrize('preset_param, expected_result', [
    ('main_preset', ('main_preset', None)),
    ('folder/main_preset', ('folder', 'main_preset'))])
def test_parse_preset_param(preset_param, expected_result):
    assert InputManager.parse_preset_param(preset_param) == expected_result


@patch('GenEC.utils.read_yaml_file')
def test_load_presets_direct(mock_read_yaml_file, im_instance):
    # Simulate a preset-list file with two entries
    mock_read_yaml_file.return_value = {
        'presets': ['file1/presetA', 'file2/presetB']
    }
    # Patch load_preset_file on the real instance
    with patch.object(im_instance, 'load_preset_file', side_effect=[{'presetA': {'key': 'valueA'}}, {'presetB': {'key': 'valueB'}}]):
        result = im_instance.load_presets('mock_preset_list')
        assert isinstance(result, list)
        assert any(p.preset == 'file1/presetA' and p.config == {'key': 'valueA'} for p in result)
        assert any(p.preset == 'file2/presetB' and p.config == {'key': 'valueB'} for p in result)


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
    with pytest.raises(FileNotFoundError):
        im_instance.load_preset_file('mock_file')


@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open, read_data='')
def test_load_preset_file_empty_file(mock_open_file, mock_exists, im_instance):
    with pytest.raises(ValueError):
        im_instance.load_preset_file('mock_file')


@pytest.mark.parametrize('preset_data', [
    (SINGLE_PRESET_DATA),
    (MULTIPLE_PRESETS_DATA)
])
@patch('os.path.exists', return_value=True)
@patch('builtins.open', new_callable=mock_open)
@patch('yaml.safe_load')
def test_load_preset_file_valid_file(mock_safe_load, mock_open_file, mock_exists, im_instance, preset_data):
    mock_safe_load.return_value = preset_data
    result = im_instance.load_preset_file('mock_file')
    assert result == preset_data


@patch.object(InputManager, 'load_preset_file')
def test_load_presets_function(mock_load_preset_file, im_instance):
    # Setup mock returns for two files
    mock_load_preset_file.side_effect = [MOCK_LOADED_PRESETS_FILE_1, MOCK_LOADED_PRESETS_FILE_2]
    presets_per_file = {
        'file1': ['presetA', 'presetB'],
        'file2': ['presetB']
    }
    result = im_instance._collect_presets(presets_per_file)
    assert len(result) == 3
    assert any(p.preset == 'file1/presetA' and p.config == {'key': 'value'} for p in result)
    assert any(p.preset == 'file1/presetB' and p.config == {'key2': 'value2'} for p in result)
    assert any(p.preset == 'file2/presetB' and p.config == {'key3': 'value3'} for p in result)


def test_group_presets_by_file(im_instance):
    entries = ['file1/presetA', 'file1/presetB', 'file2/presetC', 'file2/presetD']
    result = im_instance._group_presets_by_file(entries)
    assert result == {
        'file1': ['presetA', 'presetB'],
        'file2': ['presetC', 'presetD']
    }

def test_group_presets_by_file_if_false(im_instance):
    # Include entries without a file name to trigger the else branch
    entries = ['presetA', 'file1/presetB', 'presetC']
    result = im_instance._group_presets_by_file(entries)
    # Expect entries without a file name to be grouped under '' (empty string)
    assert result == {'file1': ['presetB']}


@patch.object(InputManager, 'load_preset_file')
def test_collect_presets_missing_preset(mock_load_preset_file, im_instance):
    mock_load_preset_file.return_value = {'presetA': {'key': 'value'}}
    presets_per_file = {'file1': ['presetA', 'presetX']}
    result = im_instance._collect_presets(presets_per_file)
    assert len(result) == 1
    assert result[0].preset == 'file1/presetA'
    assert result[0].config == {'key': 'value'}


@patch.object(InputManager, 'load_preset_file')
def test_collect_presets_all_found(mock_load_preset_file, im_instance):
    # All preset_names are found in loaded_presets, so else branch is not triggered
    mock_load_preset_file.side_effect = [
        {'presetA': {'key': 'valueA'}, 'presetB': {'key': 'valueB'}},
        {'presetC': {'key': 'valueC'}}
    ]
    presets_per_file = {'file1': ['presetA', 'presetB'], 'file2': ['presetC']}
    result = im_instance._collect_presets(presets_per_file)
    assert len(result) == 3
    assert any(p.preset == 'file1/presetA' and p.config == {'key': 'valueA'} for p in result)
    assert any(p.preset == 'file1/presetB' and p.config == {'key': 'valueB'} for p in result)
    assert any(p.preset == 'file2/presetC' and p.config == {'key': 'valueC'} for p in result)


@patch.object(InputManager, 'load_preset_file')
def test_collect_presets_raises_value_error(mock_load_preset_file, im_instance):
    # Simulate missing preset in loaded_presets to trigger ValueError
    mock_load_preset_file.return_value = {'presetA': {'key': 'value'}}
    presets_per_file = {'file1': ['presetB', 'presetX']}
    # The implementation should raise ValueError for 'presetX'
    with pytest.raises(ValueError):
        im_instance._collect_presets(presets_per_file)


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

    assert im_instance.request_text_filter() == PositionalFilterType(separator=mock_output[0], line=mock_output[1], occurrence=mock_output[2])


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
