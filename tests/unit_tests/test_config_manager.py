"""Pure unit tests for GenEC ConfigManager individual methods."""
# pylint: disable=protected-access

from __future__ import annotations

from typing import Any
from pathlib import Path
from unittest.mock import patch, mock_open, Mock
import pytest

from GenEC.core import ConfigOptions, TextFilterTypes
from GenEC.core.config_manager import ConfigManager, LegacyConfiguration
from GenEC.core.types.preset_config import Initialized, Finalized


def create_empty_config() -> Initialized:
    """Helper function to create an empty configuration object."""
    return Initialized(
        cluster_filter=None,
        text_filter_type=None,
        text_filter=None,
        should_slice_clusters=None,
        src_start_cluster_text=None,
        src_end_cluster_text=None,
        ref_start_cluster_text=None,
        ref_end_cluster_text=None
    )


def create_test_preset_data() -> dict[str, dict[str, Any]]:
    """Helper function to create standard test preset data."""
    return {
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


def create_multiple_presets_data() -> dict[str, dict[str, Any]]:
    """Helper function to create multiple test presets."""
    base_data = create_test_preset_data()
    base_data.update({
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
    })
    return base_data


def create_mock_finalized_config() -> Finalized:
    """Helper function to create mock finalized configuration."""
    return {
        'cluster_filter': '\n',
        'text_filter_type': 'regex',
        'text_filter': 'test.*',
        'should_slice_clusters': False,
        'src_start_cluster_text': '',
        'src_end_cluster_text': '',
        'ref_start_cluster_text': '',
        'ref_end_cluster_text': ''
    }


def make_preset_entry(file_name: str, preset_name: str, target_file: str) -> dict[str, str]:
    """Create a test preset entry dictionary."""
    return {'preset_file': file_name, 'preset_name': preset_name, 'target_file': target_file}


@pytest.fixture
def c_instance() -> ConfigManager:
    """Create ConfigManager instance for testing."""
    return ConfigManager(auto_configure=False)


# =============================================================================
# Parameter Parsing Tests (Pure Unit)
# =============================================================================

@pytest.mark.unit
@pytest.mark.parametrize('preset_param, expected_result', [
    ('main_preset', ('main_preset', None)),
    ('folder/main_preset', ('folder', 'main_preset'))])
def test_parse_preset_param(preset_param: str, expected_result: tuple[str, str | None]) -> None:
    """Test parsing of preset parameter string."""
    assert ConfigManager.parse_preset_param(preset_param) == expected_result


# =============================================================================
# Input Collection Method Tests (Pure Unit)
# =============================================================================

@pytest.mark.unit
@patch.object(ConfigManager, 'ask_open_question')
def test_collect_cluster_filter_user_input(mockask_open_question: Mock) -> None:
    """Test cluster filter collection with user input."""
    mockask_open_question.return_value = ';'
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    assert config_manager._collect_cluster_filter(config) == ';'


@pytest.mark.unit
def test_collect_cluster_filter_from_config() -> None:
    """Test cluster filter collection when value exists in config."""
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    config['cluster_filter'] = '\n'
    assert config_manager._collect_cluster_filter(config) == '\n'


@pytest.mark.unit
@patch.object(ConfigManager, 'ask_open_question')
def test_collect_cluster_filter_empty_input_positional_filter(mockask_open_question: Mock) -> None:
    """Test cluster filter default behavior for positional filter with empty user input."""
    mockask_open_question.return_value = ''
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    result = config_manager._collect_cluster_filter(config, filter_type=TextFilterTypes.POSITIONAL.value)
    assert result == '\\n\\n'


@pytest.mark.unit
@patch.object(ConfigManager, 'ask_open_question')
def test_collect_cluster_filter_empty_input_regex_filter(mockask_open_question: Mock) -> None:
    """Test cluster filter default behavior for regex filter with empty user input."""
    mockask_open_question.return_value = ''
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    result = config_manager._collect_cluster_filter(config, filter_type=TextFilterTypes.REGEX.value)
    assert result == '\\n'


@pytest.mark.unit
@patch.object(ConfigManager, 'ask_open_question')
def test_collect_cluster_filter_empty_input_regex_list_filter(mockask_open_question: Mock) -> None:
    """Test cluster filter default behavior for regex-list filter with empty user input."""
    mockask_open_question.return_value = ''
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    result = config_manager._collect_cluster_filter(config, filter_type=TextFilterTypes.REGEX_LIST.value)
    assert result == '\\n'


@pytest.mark.unit
@patch.object(ConfigManager, 'ask_open_question')
def test_collect_cluster_filter_empty_input_no_filter_type(mockask_open_question: Mock) -> None:
    """Test cluster filter default behavior with empty user input and no filter type."""
    mockask_open_question.return_value = ''
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    result = config_manager._collect_cluster_filter(config, filter_type=None)
    assert result == '\\n'


@pytest.mark.unit
@patch.object(ConfigManager, 'ask_mpc_question')
def test_collect_text_filter_type(mockask_mpc_question: Mock) -> None:
    """Test text filter type collection."""
    mockask_mpc_question.return_value = 'regex'
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    assert config_manager._collect_text_filter_type(config) == 'regex'


@pytest.mark.unit
@patch.object(ConfigManager, '_request_text_filter')
def test_collect_text_filter(mock_request_text_filter: Mock) -> None:
    """Test text filter collection delegation to request method."""
    mock_request_text_filter.return_value = 'filter1'
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    assert config_manager._collect_text_filter(config) == 'filter1'


@pytest.mark.unit
@pytest.mark.parametrize('user_input, expected', [
    ('yes', True),
    ('no', False)
])
@patch.object(ConfigManager, 'ask_open_question')
def test_collect_should_slice_clusters(mockask_open_question: Mock, user_input: str, expected: bool) -> None:
    """Test slice clusters collection with different user inputs."""
    mockask_open_question.return_value = user_input
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    assert config_manager._collect_should_slice_clusters(config) == expected


@pytest.mark.unit
@pytest.mark.parametrize('config_option, position, src_or_ref', [
    ('src_start_cluster_text', 'start', 'SRC'),
    ('src_end_cluster_text', 'end', 'SRC'),
    ('ref_start_cluster_text', 'start', 'REF'),
    ('ref_end_cluster_text', 'end', 'REF'),
])
@patch.object(ConfigManager, 'ask_open_question')
def test_collect_cluster_text(mockask_open_question: Mock, config_option: str, position: str, src_or_ref: str) -> None:
    """Test cluster text collection for different positions and sources."""
    mockask_open_question.return_value = 'cluster_text'
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    result = config_manager._collect_cluster_text(config, config_option, position, src_or_ref)
    assert result == 'cluster_text'


# =============================================================================
# User Interaction Method Tests (Pure Unit)
# =============================================================================

@pytest.mark.unit
def testask_open_question() -> None:
    """Test open question prompting."""
    config_manager = ConfigManager(auto_configure=False)
    with patch('builtins.input', return_value='user_input'):
        assert config_manager.ask_open_question('Test prompt: ') == 'user_input'


@pytest.mark.unit
@patch.object(ConfigManager, '_get_user_choice')
def testask_mpc_question_valid_choice(mock_get_user_choice: Mock) -> None:
    """Test multiple choice question with valid selection."""
    mock_get_user_choice.return_value = 1
    config_manager = ConfigManager(auto_configure=False)
    options = ['option1', 'option2']
    assert config_manager.ask_mpc_question('Choose:', options) == 'option1'


@pytest.mark.unit
@patch.object(ConfigManager, '_get_user_choice')
def testask_mpc_question_exit(mock_get_user_choice: Mock) -> None:
    """Test multiple choice question with exit selection."""
    mock_get_user_choice.return_value = 0
    config_manager = ConfigManager(auto_configure=False)
    options = ['option1', 'option2']
    with pytest.raises(SystemExit):
        config_manager.ask_mpc_question('Choose:', options)


@pytest.mark.unit
@patch.object(ConfigManager, '_get_user_choice')
@patch('builtins.input', return_value='invalid')
def testask_mpc_question_invalid_choice(mock_input: Mock, mock_get_user_choice: Mock) -> None:
    """Test multiple choice question handling invalid choice gracefully."""
    mock_get_user_choice.side_effect = [2]
    config_manager = ConfigManager(auto_configure=False)
    options = ['option1', 'option2']
    assert config_manager.ask_mpc_question('Choose:', options) == 'option2'


# =============================================================================
# Text Filter Request Method Tests (Pure Unit)
# =============================================================================

@pytest.mark.unit
@patch.object(ConfigManager, 'ask_open_question')
def test_request_regex_filter_type(mockask_open_question: Mock) -> None:
    """Test regex filter type request."""
    mockask_open_question.return_value = 'my_filter'
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    config['text_filter_type'] = TextFilterTypes.REGEX.value
    assert config_manager._request_text_filter(config) == 'my_filter'


@pytest.mark.unit
@pytest.mark.parametrize('mock_side_effect, expected_output', [
    ([' ', '2', '4'], {'separator': ' ', 'line': 2, 'occurrence': 4}),
    (['', '3', '8'], {'separator': ' ', 'line': 3, 'occurrence': 8}),
    (['ABC', '4', '2'], {'separator': 'ABC', 'line': 4, 'occurrence': 2})
])
@patch.object(ConfigManager, 'ask_open_question')
def test_request_positional_filter_type(mockask_open_question: Mock, mock_side_effect: list[str], expected_output: dict[str, Any]) -> None:
    """Test positional filter type request with different inputs."""
    mockask_open_question.side_effect = mock_side_effect
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    config['text_filter_type'] = TextFilterTypes.POSITIONAL.value
    result = config_manager._request_text_filter(config)
    assert result == expected_output


@pytest.mark.unit
@pytest.mark.parametrize('mock_side_effect, expected_output', [
    (['regex_1', 'y', 'regex_2', 'done'], ['regex_1', 'regex_2']),
    (['regex_1', 'n'], ['regex_1']),
    (['regex_1', 'Y', 'regex_2', 'YeS', 'regex_3', ''], ['regex_1', 'regex_2', 'regex_3']),
])
@patch.object(ConfigManager, 'ask_open_question')
def test_request_regex_list_filter_type(mockask_open_question: Mock, mock_side_effect: list[str], expected_output: list[str]) -> None:
    """Test regex list filter type request with different inputs."""
    mockask_open_question.side_effect = mock_side_effect
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    config['text_filter_type'] = TextFilterTypes.REGEX_LIST.value
    assert config_manager._request_text_filter(config) == expected_output


@pytest.mark.unit
@pytest.mark.parametrize('filter_type', [
    'Keyword_UNSUPPORTED',
    'Split-keywords_UNSUPPORTED'
])
def test_request_unsupported_filter_type(filter_type: str) -> None:
    """Test request for unsupported filter types raises ValueError."""
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    config['text_filter_type'] = filter_type
    with pytest.raises(ValueError):
        config_manager._request_text_filter(config)


# =============================================================================
# Configuration Value Resolution Tests (Pure Unit)
# =============================================================================

@pytest.mark.unit
def test_resolve_config_value_from_config() -> None:
    """Test config value resolution when value exists in config."""
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()
    config['cluster_filter'] = '\n'
    result = config_manager._resolve_config_value(config, ConfigOptions.CLUSTER_FILTER, lambda: 'default')
    assert result == '\n'


@pytest.mark.unit
def test_resolve_config_value_from_prompt() -> None:
    """Test config value resolution when value missing from config."""
    config_manager = ConfigManager(auto_configure=False)
    config = create_empty_config()

    result = config_manager._resolve_config_value(config, ConfigOptions.CLUSTER_FILTER, lambda: 'prompted_value')
    assert result == 'prompted_value'


# =============================================================================
# Preset File Loading Unit Tests
# =============================================================================

@pytest.mark.unit
@patch.object(Path, 'exists', return_value=False)
def test_load_preset_file_file_not_found(mock_exists: Mock, c_instance: ConfigManager) -> None:
    """Test loading preset file when file not found raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        c_instance.load_preset_file('mock_file')


@pytest.mark.unit
@patch.object(Path, 'exists', return_value=True)
@patch.object(Path, 'open', new_callable=mock_open, read_data='')
def test_load_preset_file_empty_file(mock_open_file: Mock, mock_exists: Mock, c_instance: ConfigManager) -> None:
    """Test loading preset file when file is empty raises ValueError."""
    with pytest.raises(ValueError):
        c_instance.load_preset_file('mock_file')


@pytest.mark.unit
@pytest.mark.parametrize('preset_data', [
    create_test_preset_data(),
    create_multiple_presets_data()
])
@patch.object(Path, 'exists', return_value=True)
@patch.object(Path, 'open', new_callable=mock_open)
@patch('yaml.safe_load')
def test_load_preset_file_valid_file(mock_safe_load: Mock, mock_open_file: Mock, mock_exists: Mock,
                                     c_instance: ConfigManager, preset_data: dict[str, dict[str, Any]]) -> None:
    """Test loading preset file with valid file content."""
    mock_safe_load.return_value = preset_data
    result = c_instance.load_preset_file('mock_file')
    assert result == preset_data


# =============================================================================
# Preset List Processing Unit Tests
# =============================================================================

@pytest.mark.unit
def test_load_presets_grouped(c_instance: ConfigManager) -> None:
    """Test loading presets grouped by target file."""
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


# =============================================================================
# Preset Entry Processing Unit Tests
# =============================================================================

@pytest.mark.unit
@patch.object(ConfigManager, 'load_preset_file')
def test_process_preset_entry_found(mock_load_preset_file: Mock, c_instance: ConfigManager) -> None:
    """Test processing preset entry when preset is found."""
    entry = make_preset_entry('fileA', 'presetA', 'targetA.txt')
    mock_config: dict[str, Any] = {
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
    assert isinstance(result, LegacyConfiguration)
    assert result.preset == 'fileA/presetA'
    assert result.target_file == 'targetA.txt'
    # Handle both legacy and new config formats
    if isinstance(result.config, dict):
        assert result.config['cluster_filter'] == '\n\n'
    else:
        assert result.config.cluster_filter == '\n\n'


@pytest.mark.unit
@patch.object(ConfigManager, 'load_preset_file')
def test_process_preset_entry_not_found(mock_load_preset_file: Mock, c_instance: ConfigManager, capsys: pytest.CaptureFixture[str]) -> None:
    """Test processing preset entry when preset is not found."""
    entry = make_preset_entry('fileA', 'presetX', 'targetA.txt')
    mock_load_preset_file.return_value = {'presetA': {}}
    result = c_instance._process_preset_entry(entry, entry['target_file'])
    assert result is None
    captured = capsys.readouterr()
    assert 'PRESET ERROR: Invalid preset fileA/presetX' in captured.out
    assert 'Skipping preset presetX from fileA' in captured.out


# =============================================================================
# Configuration Option Setting Unit Tests
# =============================================================================

@pytest.mark.unit
@patch.object(ConfigManager, '_collect_cluster_text', side_effect=['startA', 'endA', 'startB', 'endB'])
def test_set_cluster_text_options(mock_cluster_text: Mock, c_instance: ConfigManager) -> None:
    """Test setting cluster text options for configuration."""
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
@patch.object(ConfigManager, '_collect_cluster_filter', return_value='\n')
@patch.object(ConfigManager, '_collect_text_filter_type', return_value='regex')
@patch.object(ConfigManager, '_collect_text_filter', return_value='[a-z]+')
@patch.object(ConfigManager, '_collect_should_slice_clusters', return_value=True)
def test_set_simple_options(mock_should_slice: Mock, mock_text_filter: Mock, mock_text_type: Mock,
                            mock_cluster_filter: Mock, c_instance: ConfigManager) -> None:
    """Test setting simple configuration options."""
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


# Collect presets unit tests

@pytest.mark.unit
@patch.object(ConfigManager, '_process_preset_entry')
def test_collect_presets_all_found(mock_process_entry: Mock, c_instance: ConfigManager) -> None:
    """Test collecting presets when all presets are found."""
    entry1 = make_preset_entry('fileA', 'presetA', 'targetA.txt')
    entry2 = make_preset_entry('fileB', 'presetB', 'targetB.txt')
    mock_finalized_config = create_mock_finalized_config()
    mock_ac1 = LegacyConfiguration(mock_finalized_config, 'fileA/presetA', 'targetA.txt')
    mock_ac2 = LegacyConfiguration(mock_finalized_config, 'fileB/presetB', 'targetB.txt')
    mock_process_entry.side_effect = [mock_ac1, mock_ac2]
    presets_per_target = {
        'targetA.txt': [entry1],
        'targetB.txt': [entry2]
    }
    # pylint: disable=protected-access
    result = c_instance._collect_presets(presets_per_target)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].preset == 'fileA/presetA'
    assert result[1].preset == 'fileB/presetB'


@pytest.mark.unit
@patch.object(ConfigManager, '_process_preset_entry')
def test_collect_presets_some_missing(mock_process_entry: Mock, c_instance: ConfigManager) -> None:
    """Test collecting presets when some presets are missing."""
    entry1 = make_preset_entry('fileA', 'presetA', 'targetA.txt')
    entry2 = make_preset_entry('fileB', 'presetB', 'targetB.txt')
    mock_finalized_config = create_mock_finalized_config()
    mock_ac1 = LegacyConfiguration(mock_finalized_config, 'fileA/presetA', 'targetA.txt')
    mock_process_entry.side_effect = [mock_ac1, None]
    presets_per_target = {
        'targetA.txt': [entry1],
        'targetB.txt': [entry2]
    }
    # pylint: disable=protected-access
    result = c_instance._collect_presets(presets_per_target)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].preset == 'fileA/presetA'


@pytest.mark.unit
@patch.object(ConfigManager, '_process_preset_entry')
def test_collect_presets_none_found(mock_process_entry: Mock, c_instance: ConfigManager) -> None:
    """Test collecting presets when none are found raises ValueError."""
    entry1 = make_preset_entry('fileA', 'presetA', 'targetA.txt')
    entry2 = make_preset_entry('fileB', 'presetB', 'targetB.txt')
    mock_process_entry.side_effect = [None, None]
    presets_per_target = {
        'targetA.txt': [entry1],
        'targetB.txt': [entry2]
    }
    with pytest.raises(ValueError, match='None of the provided presets were found.'):
        # pylint: disable=protected-access
        c_instance._collect_presets(presets_per_target)
