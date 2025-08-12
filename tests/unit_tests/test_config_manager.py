from pathlib import Path
import pytest
from unittest.mock import patch, mock_open

from GenEC.core.config_manager import ConfigManager, Configuration
from GenEC.core.manage_io import InputManager
from GenEC.core.types.preset_config import Initialized


EMPTY_CONFIG = Initialized(
            cluster_filter=None,
            text_filter_type=None,
            text_filter=None,
            should_slice_clusters=None,
            src_start_cluster_text=None,
            src_end_cluster_text=None,
            ref_start_cluster_text=None,
            ref_end_cluster_text=None)

SINGLE_PRESET_DATA = {
    'main_preset': {
        'cluster_filter': '',
        'text_filter_type': 'regex',
        'text_filter': '',
        'should_slice_clusters': False,
        'src_start_cluster_text': '',
        'src_end_cluster_text': '',
        'ref_start_cluster_text': '',
        'ref_end_cluster_text': ''
    }
}

MULTIPLE_PRESETS_DATA = {
    'main_preset': {
        'cluster_filter': '',
        'text_filter_type': 'regex',
        'text_filter': '',
        'should_slice_clusters': False,
        'src_start_cluster_text': '',
        'src_end_cluster_text': '',
        'ref_start_cluster_text': '',
        'ref_end_cluster_text': ''
    },
    'sub_preset_A': {
        'cluster_filter': '',
        'text_filter_type': 'regex',
        'text_filter': '',
        'should_slice_clusters': True,
        'src_start_cluster_text': '',
        'src_end_cluster_text': '',
        'ref_start_cluster_text': '',
        'ref_end_cluster_text': ''
    },
    'sub_preset_B': {
        'cluster_filter': '\\n',
        'text_filter_type': 'regex',
        'text_filter': '[a-zA-z]{4}',
        'should_slice_clusters': False,
        'src_start_cluster_text': '',
        'src_end_cluster_text': '',
        'ref_start_cluster_text': '',
        'ref_end_cluster_text': ''
    }
}


@pytest.fixture  # noqa: E261
def c_instance():  # pylint: disable=all
    real_set_config = ConfigManager.set_config  # store the real method
    with patch.object(ConfigManager, 'set_config', autospec=True) as mock_set_config:  # noqa: F841
        instance = ConfigManager()
    instance.set_config = real_set_config.__get__(instance, ConfigManager)  # restore the real method on the instance
    return instance


def make_entry(file_name, preset_name, target_file):
    return {'preset_file': file_name, 'preset_name': preset_name, 'target_file': target_file}


@pytest.mark.unit
@patch.object(ConfigManager, 'load_preset', return_value={'key': 'value'})
@patch.object(ConfigManager, 'set_config')
def test_init_with_preset_type(mock_load_preset, mock_set_config):
    config_manager = ConfigManager({'type': 'preset', 'value': 'file.yaml/presetA'})
    assert config_manager.configurations == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "mock_presets, expected_count",
    [
        ([Configuration({'key': 'valueA'}, 'file1/presetA', 'file1')], 1),
        ([Configuration({'key': 'valueA'}, 'file1/presetA', 'file1'),
          Configuration({'key': 'valueB'}, 'file2/presetB', 'file2')], 2),
    ]
)
@patch.object(ConfigManager, 'load_presets')
def test_init_with_preset_list_type(mock_load_presets, mock_presets, expected_count):
    mock_load_presets.return_value = mock_presets
    config_manager = ConfigManager({'type': 'preset-list', 'value': 'fake_list'})
    assert isinstance(config_manager.configurations, list)
    assert len(config_manager.configurations) == expected_count
    for i, preset_entry in enumerate(mock_presets):
        assert config_manager.configurations[i].preset == preset_entry.preset
        assert config_manager.configurations[i].config == preset_entry.config
        assert config_manager.configurations[i].target_file == preset_entry.target_file


@pytest.mark.unit
def test_init_with_invalid_type():
    with pytest.raises(ValueError, match='not a valid preset parameter type'):
        ConfigManager({'type': 'invalid', 'value': 'something'})


@pytest.mark.unit
@pytest.mark.parametrize('preset_param, expected_result', [
    ('main_preset', ('main_preset', None)),
    ('folder/main_preset', ('folder', 'main_preset'))])
def test_parse_preset_param(preset_param, expected_result):
    assert ConfigManager.parse_preset_param(preset_param) == expected_result


@pytest.mark.unit
@patch.object(ConfigManager, 'load_preset_file')
@patch.object(InputManager, 'ask_mpc_question')
def test_load_preset_no_preset_name(mock_ask_mpc_question, mock_load_preset_file, c_instance):
    mock_load_preset_file.return_value = MULTIPLE_PRESETS_DATA
    mock_ask_mpc_question.return_value = preset_name = 'main_preset'
    result = c_instance.load_preset(preset_target='')
    assert result == MULTIPLE_PRESETS_DATA[preset_name]


@pytest.mark.unit
@patch.object(ConfigManager, 'load_preset_file')
def test_load_preset_invalid_preset_name(mock_load_preset_file, c_instance):
    mock_load_preset_file.return_value = MULTIPLE_PRESETS_DATA
    with pytest.raises(ValueError):
        c_instance.load_preset(preset_target='preset/presetX')


@pytest.mark.unit
@patch.object(ConfigManager, 'load_preset_file')
def test_load_from_single_preset(mock_load_preset_file, c_instance):
    mock_load_preset_file.return_value = SINGLE_PRESET_DATA
    result = c_instance.load_preset(preset_target='preset/main_preset')
    assert result == SINGLE_PRESET_DATA['main_preset']


@pytest.mark.unit
@pytest.mark.parametrize('preset_name', [
    ('main_preset'),
    ('sub_preset_A')
])
@patch.object(ConfigManager, 'load_preset_file')
def test_load_from_multiple_presets_existing_preset_name(mock_load_preset_file, c_instance, preset_name):
    mock_load_preset_file.return_value = MULTIPLE_PRESETS_DATA
    result = c_instance.load_preset(preset_target=f'preset/{preset_name}')
    assert result == MULTIPLE_PRESETS_DATA[preset_name]


@pytest.mark.unit
@patch('os.path.exists', return_value=False)
def test_load_preset_file_file_not_found(mock_exists, c_instance):
    with pytest.raises(FileNotFoundError):
        c_instance.load_preset_file('mock_file')


@pytest.mark.unit
@patch.object(Path, 'exists', return_value=True)
@patch.object(Path, 'open', new_callable=mock_open, read_data='')
def test_load_preset_file_empty_file(mock_open_file, mock_exists, c_instance):
    with pytest.raises(ValueError):
        c_instance.load_preset_file('mock_file')


@pytest.mark.unit
@pytest.mark.parametrize('preset_data', [
    (SINGLE_PRESET_DATA),
    (MULTIPLE_PRESETS_DATA)
])
@patch.object(Path, 'exists', return_value=True)
@patch.object(Path, 'open', new_callable=mock_open)
@patch('yaml.safe_load')
def test_load_preset_file_valid_file(mock_safe_load, mock_open_file, mock_exists, c_instance, preset_data):
    mock_safe_load.return_value = preset_data
    result = c_instance.load_preset_file('mock_file')
    assert result == preset_data


@pytest.mark.unit
def test_load_presets_grouped(c_instance):
    grouped_entries = {
        'group_1': [
            {'preset': 'p/preset_numbers', 'target': 'file1.txt'},
            {'preset': 'p/preset_letters', 'target': 'file2.txt'}
        ],
        'group_2': [
            {'preset': 'p/preset_dates', 'target': 'file3.txt'},
            {'preset': 'p/preset_code_value', 'target': 'file2.txt'},
            {'preset': 'p/preset_code_value', 'target': 'file3.txt'}
        ]
    }

    results = c_instance._group_presets_by_file(grouped_entries)

    assert results == {
        'file1.txt': [
            {'preset_group': 'group_1', 'preset_file': 'p', 'preset_name': 'preset_numbers', 'target_file': 'file1.txt'}],
        'file2.txt': [
            {'preset_group': 'group_1', 'preset_file': 'p', 'preset_name': 'preset_letters', 'target_file': 'file2.txt'},
            {'preset_group': 'group_2', 'preset_file': 'p', 'preset_name': 'preset_code_value', 'target_file': 'file2.txt'}],
        'file3.txt': [{'preset_group': 'group_2', 'preset_file': 'p', 'preset_name': 'preset_dates', 'target_file': 'file3.txt'},
                      {'preset_group': 'group_2', 'preset_file': 'p', 'preset_name': 'preset_code_value', 'target_file': 'file3.txt'}]}


@pytest.mark.unit
@patch.object(ConfigManager, '_set_cluster_text_options')
@patch('GenEC.utils.read_yaml_file', return_value=SINGLE_PRESET_DATA)
def test_set_config(mock__set_cluster_text_options, mock_read_yaml_file, c_instance):
    c_instance.set_config(preset='main_preset', target_file='targetA.txt')
    c = c_instance.configurations[-1]
    assert c.preset == 'main_preset'
    assert c.target_file == 'targetA.txt'
    assert c.config == SINGLE_PRESET_DATA['main_preset']


@pytest.mark.unit
@patch.object(InputManager, 'set_cluster_filter', return_value=SINGLE_PRESET_DATA['main_preset']['cluster_filter'])
@patch.object(InputManager, 'set_text_filter_type', return_value=SINGLE_PRESET_DATA['main_preset']['text_filter_type'])
@patch.object(InputManager, 'set_text_filter', return_value=SINGLE_PRESET_DATA['main_preset']['text_filter'])
@patch.object(InputManager, 'set_should_slice_clusters', return_value=True)
@patch.object(ConfigManager, '_set_cluster_text_options')
@patch.object(ConfigManager, '_finalize_config', return_value=SINGLE_PRESET_DATA['main_preset'])
def test_set_config_no_preset(mock_set_cluster_filter, mock_set_text_filter_type, mock_set_text_filter,
                              mock_should_slice_clusters, mock_cluster_text_options, mock_finalize_config, c_instance):
    c_instance.set_config()
    c = c_instance.configurations[-1]
    assert c.preset == ''
    assert c.target_file == ''
    mock_cluster_text_options.assert_called()


@pytest.mark.unit
@patch.object(InputManager, 'set_cluster_text', side_effect=['startA', 'endA', 'startB', 'endB'])
def test_set_cluster_text_options(mock_cluster_text, c_instance):
    config = Initialized(
        cluster_filter='\n',
        text_filter_type='regex',
        text_filter='[a-z]+',
        should_slice_clusters=True,
        src_start_cluster_text=None,
        src_end_cluster_text='endA',
        ref_start_cluster_text='startB',
        ref_end_cluster_text='endB')
    c_instance._set_cluster_text_options(config)
    assert config['src_start_cluster_text'] == 'startA'
    assert config['src_end_cluster_text'] == 'endA'
    assert config['ref_start_cluster_text'] == 'startB'
    assert config['ref_end_cluster_text'] == 'endB'


@pytest.mark.unit
@patch.object(InputManager, 'set_cluster_filter', return_value='\n')
@patch.object(InputManager, 'set_text_filter_type', return_value='regex')
@patch.object(InputManager, 'set_text_filter', return_value='[a-z]+')
@patch.object(InputManager, 'set_should_slice_clusters', return_value=True)
def test_set_simple_options(mock_should_slice, mock_text_filter, mock_text_type, mock_cluster_filter, c_instance):
    # All config options missing
    config = Initialized(
        cluster_filter=None,
        text_filter_type=None,
        text_filter=None,
        should_slice_clusters=None,
        src_start_cluster_text=None,
        src_end_cluster_text=None,
        ref_start_cluster_text=None,
        ref_end_cluster_text=None)
    c_instance._set_simple_options(config)
    assert config['cluster_filter'] == '\n'
    assert config['text_filter_type'] == 'regex'
    assert config['text_filter'] == '[a-z]+'
    assert config['should_slice_clusters'] is True


@pytest.mark.unit
@patch.object(ConfigManager, 'load_preset_file')
def test_process_preset_entry_found(mock_load_preset_file, c_instance):
    entry = make_entry('fileA', 'presetA', 'targetA.txt')
    mock_config = {
        'cluster_filter': '\n\n',
        'text_filter_type': 'regex',
        'text_filter': '',
        'should_slice_clusters': False,
        'src_start_cluster_text': '',
        'src_end_cluster_text': '',
        'ref_start_cluster_text': '',
        'ref_end_cluster_text': ''
    }
    mock_load_preset_file.return_value = {'presetA': mock_config}
    result = c_instance._process_preset_entry(entry, entry['target_file'])
    assert isinstance(result, Configuration)
    assert result.preset == 'fileA/presetA'
    assert result.target_file == 'targetA.txt'
    assert result.config['cluster_filter'] == '\n\n'


@pytest.mark.unit
@patch.object(ConfigManager, 'load_preset_file')
def test_process_preset_entry_not_found(mock_load_preset_file, c_instance, capsys):
    entry = make_entry('fileA', 'presetX', 'targetA.txt')
    mock_load_preset_file.return_value = {'presetA': {}}
    result = c_instance._process_preset_entry(entry, entry['target_file'])
    assert result is None
    captured = capsys.readouterr()
    assert 'preset presetX not found in fileA' in captured.out


@pytest.mark.unit
@patch.object(ConfigManager, '_process_preset_entry')
def test_collect_presets_all_found(mock_process_entry, c_instance):
    entry1 = make_entry('fileA', 'presetA', 'targetA.txt')
    entry2 = make_entry('fileB', 'presetB', 'targetB.txt')
    mock_ac1 = Configuration(Initialized(), 'fileA/presetA', 'targetA.txt')
    mock_ac2 = Configuration(Initialized(), 'fileB/presetB', 'targetB.txt')
    mock_process_entry.side_effect = [mock_ac1, mock_ac2]
    presets_per_target = {
        'targetA.txt': [entry1],
        'targetB.txt': [entry2]
    }
    result = c_instance._collect_presets(presets_per_target)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].preset == 'fileA/presetA'
    assert result[1].preset == 'fileB/presetB'


@pytest.mark.unit
@patch.object(ConfigManager, '_process_preset_entry')
def test_collect_presets_some_missing(mock_process_entry, c_instance):
    entry1 = make_entry('fileA', 'presetA', 'targetA.txt')
    entry2 = make_entry('fileB', 'presetB', 'targetB.txt')
    mock_ac1 = Configuration(Initialized(), 'fileA/presetA', 'targetA.txt')
    mock_process_entry.side_effect = [mock_ac1, None]
    presets_per_target = {
        'targetA.txt': [entry1],
        'targetB.txt': [entry2]
    }
    result = c_instance._collect_presets(presets_per_target)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].preset == 'fileA/presetA'


@pytest.mark.unit
@patch.object(ConfigManager, '_process_preset_entry')
def test_collect_presets_none_found(mock_process_entry, c_instance):
    entry1 = make_entry('fileA', 'presetA', 'targetA.txt')
    entry2 = make_entry('fileB', 'presetB', 'targetB.txt')
    mock_process_entry.side_effect = [None, None]
    presets_per_target = {
        'targetA.txt': [entry1],
        'targetB.txt': [entry2]
    }
    with pytest.raises(ValueError, match='None of the provided presets were found.'):
        c_instance._collect_presets(presets_per_target)
