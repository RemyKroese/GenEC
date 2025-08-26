"""Integration tests for GenEC ConfigManager workflows."""

from __future__ import annotations

from typing import Any
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock, Mock

from GenEC.core.config_manager import ConfigManager, LegacyConfiguration
from GenEC.core.types.preset_config import Initialized, Finalized
import GenEC.utils as utils


def create_test_preset_data() -> dict[str, dict[str, Any]]:
    """Helper function to create standard test preset data."""
    return {
        'main_preset': {
            'cluster_filter': '',
            'text_filter_type': 'Regex',
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
            'text_filter_type': 'Regex',
            'text_filter': '',
            'should_slice_clusters': True,
            'src_start_cluster_text': '',
            'src_end_cluster_text': '',
            'ref_start_cluster_text': '',
            'ref_end_cluster_text': ''
        },
        'sub_preset_B': {
            'cluster_filter': '\\n',
            'text_filter_type': 'Regex',
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
        'text_filter_type': 'Regex',
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


@pytest.fixture  # noqa: E261
def c_instance() -> ConfigManager:  # pylint: disable=all
    """Create ConfigManager instance for testing."""
    real_set_config = ConfigManager.set_config  # store the real method
    with patch.object(ConfigManager, 'set_config', autospec=True):
        instance: ConfigManager = ConfigManager()
    # Restore the real method on the instance using proper assignment
    setattr(instance, 'set_config', real_set_config.__get__(instance, ConfigManager))
    return instance


# =============================================================================
# ConfigManager Initialization Integration Tests
# =============================================================================

@pytest.mark.integration
@patch.object(ConfigManager, 'load_preset', return_value={'key': 'value'})
@patch.object(ConfigManager, 'set_config')
def test_init_with_preset_type(mock_load_preset: Mock, mock_set_config: Mock) -> None:
    """Test ConfigManager initialization with preset type."""
    config_manager = ConfigManager({'type': 'preset', 'value': 'file.yaml/presetA'})
    assert config_manager.configurations == []


@pytest.mark.integration
@pytest.mark.parametrize(
    "mock_presets, expected_count",
    [
        ([LegacyConfiguration(create_mock_finalized_config(), 'file1/presetA', 'file1')], 1),
        ([LegacyConfiguration(create_mock_finalized_config(), 'file1/presetA', 'file1'),
          LegacyConfiguration(create_mock_finalized_config(), 'file2/presetB', 'file2')], 2),
    ]
)
@patch.object(ConfigManager, 'load_presets')
def test_init_with_preset_list_type(mock_load_presets: Mock, mock_presets: list[LegacyConfiguration], expected_count: int) -> None:
    """Test ConfigManager initialization with preset list type."""
    mock_load_presets.return_value = mock_presets
    config_manager = ConfigManager({'type': 'preset-list', 'value': 'fake_list'})
    assert isinstance(config_manager.configurations, list)
    assert len(config_manager.configurations) == expected_count
    for i, preset_entry in enumerate(mock_presets):
        assert config_manager.configurations[i].preset == preset_entry.preset
        assert config_manager.configurations[i].config == preset_entry.config
        assert config_manager.configurations[i].target_file == preset_entry.target_file


@pytest.mark.integration
def test_init_with_invalid_type() -> None:
    """Test ConfigManager initialization with invalid type raises ValueError."""
    with pytest.raises(ValueError, match='not a valid preset parameter type'):
        ConfigManager({'type': 'invalid', 'value': 'something'})


# =============================================================================
# Preset Loading Integration Tests
# =============================================================================

@pytest.mark.integration
@patch.object(ConfigManager, 'load_preset_file')
@patch.object(ConfigManager, 'ask_mpc_question')
def test_load_preset_no_preset_name(mockask_mpc_question: Mock, mock_load_preset_file: Mock, c_instance: ConfigManager) -> None:
    """Test loading preset when no preset name is provided."""
    multiple_presets = create_multiple_presets_data()
    mock_load_preset_file.return_value = multiple_presets
    mockask_mpc_question.return_value = preset_name = 'main_preset'
    result = c_instance.load_preset(preset_target='')
    assert result == multiple_presets[preset_name]


@pytest.mark.integration
@patch.object(ConfigManager, 'load_preset_file')
def test_load_preset_invalid_preset_name(mock_load_preset_file: Mock, c_instance: ConfigManager) -> None:
    """Test loading preset with invalid preset name raises ValueError."""
    mock_load_preset_file.return_value = create_multiple_presets_data()
    with pytest.raises(ValueError):
        c_instance.load_preset(preset_target='preset/presetX')


@pytest.mark.integration
@patch.object(ConfigManager, 'load_preset_file')
def test_load_from_single_preset(mock_load_preset_file: Mock, c_instance: ConfigManager) -> None:
    """Test loading from a single preset file."""
    single_preset = create_test_preset_data()
    mock_load_preset_file.return_value = single_preset
    result = c_instance.load_preset(preset_target='preset/main_preset')
    assert result == single_preset['main_preset']


@pytest.mark.integration
@pytest.mark.parametrize('preset_name', [
    ('main_preset'),
    ('sub_preset_A')
])
@patch.object(ConfigManager, 'load_preset_file')
def test_load_from_multiple_presets_existing_preset_name(mock_load_preset_file: Mock, c_instance: ConfigManager, preset_name: str) -> None:
    """Test loading from multiple presets with existing preset name."""
    multiple_presets = create_multiple_presets_data()
    mock_load_preset_file.return_value = multiple_presets
    result = c_instance.load_preset(preset_target=f'preset/{preset_name}')
    assert result == multiple_presets[preset_name]


# =============================================================================
# Configuration Setting Integration Tests
# =============================================================================

@pytest.mark.integration
@patch.object(ConfigManager, '_set_cluster_text_options')
@patch('GenEC.utils.read_yaml_file')
def test_set_config(mock_read_yaml_file: Mock, mock__set_cluster_text_options: Mock, c_instance: ConfigManager) -> None:
    """Test setting configuration with preset."""
    test_preset_data = create_test_preset_data()
    mock_read_yaml_file.return_value = test_preset_data
    c_instance.set_config(preset='main_preset', target_file='targetA.txt')
    c = c_instance.configurations[-1]
    assert c.preset == 'main_preset'
    assert c.target_file == 'targetA.txt'

    # Compare against the new configuration format (dataclass)
    expected_data = test_preset_data['main_preset']
    assert c.config.cluster_filter == expected_data['cluster_filter']
    assert c.config.filter_type == expected_data['text_filter_type']
    assert c.config.text_filter == expected_data['text_filter']
    assert c.config.should_slice_clusters == expected_data['should_slice_clusters']


@pytest.mark.integration
@patch.object(ConfigManager, 'ask_open_question')
@patch.object(ConfigManager, 'ask_mpc_question')
def test_set_config_no_preset(mock_ask_mpc: Mock, mock_ask_open: Mock, c_instance: ConfigManager) -> None:
    """Test setting configuration without preset using interactive collection."""
    # Mock the interactive prompts to simulate user input
    mock_ask_mpc.return_value = 'Regex'  # Filter type selection
    mock_ask_open.side_effect = [
        '\\n',  # cluster_filter
        'test.*',  # text_filter (regex pattern)
        'n'  # should_slice_clusters (no)
    ]

    c_instance.set_config()
    c = c_instance.configurations[-1]
    assert c.preset == ''
    assert c.target_file == ''
    # Verify that the configuration was created with correct values
    assert hasattr(c.config, 'filter_type')
    assert c.config.filter_type == 'Regex'

# =============================================================================
# Preset Creation Integration Tests
# =============================================================================

@pytest.mark.integration
@patch.object(ConfigManager, 'ask_open_question')
@patch.object(Path, 'exists', return_value=False)
@patch.object(utils, 'write_yaml')
@patch.object(utils, 'write_txt')
def test_create_new_preset_creates_new_file(mock_write_txt: Mock, mock_write_yaml: Mock, mock_exists: Mock, mock_ask_open: Mock, c_instance: ConfigManager) -> None:
    """Test creating new preset when file doesn't exist."""
    mock_ask_open.side_effect = ['my_preset', 'my_preset_file']

    c_instance.configurations = [MagicMock(config={'cluster_filter': '\\n'})]
    c_instance.presets_directory = Path('/fake_dir')

    c_instance.initialized_config = Initialized(
        cluster_filter='\\n',
        text_filter_type=None,
        text_filter=None,
        should_slice_clusters=None,
        src_start_cluster_text=None,
        src_end_cluster_text=None,
        ref_start_cluster_text=None,
        ref_end_cluster_text=None
    )

    c_instance.create_new_preset()

    mock_write_yaml.assert_called_once()
    mock_write_txt.assert_not_called()

    written_data = mock_write_yaml.call_args[0][0]
    assert 'my_preset' in written_data

    expected_config: dict[str, Any] = {
        'cluster_filter': '\\n'
    }
    assert written_data['my_preset'] == expected_config


@pytest.mark.integration
@patch.object(ConfigManager, 'ask_open_question')
@patch.object(Path, 'exists', return_value=True)
@patch.object(utils, 'write_yaml')
@patch.object(utils, 'append_to_file')
def test_create_new_preset_appends_to_existing_file(mock_append_to_file: Mock, mock_write_yaml: Mock, mock_exists: Mock, mock_ask_open: Mock, c_instance: ConfigManager) -> None:
    """Test appending new preset to existing file."""
    mock_ask_open.side_effect = ['my_preset', 'my_preset_file']

    c_instance.configurations = [MagicMock(config={'cluster_filter': '\\n'})]
    c_instance.presets_directory = Path('/fake_dir')

    c_instance.initialized_config = Initialized(
        cluster_filter='\\n',
        text_filter_type=None,
        text_filter=None,
        should_slice_clusters=None,
        src_start_cluster_text=None,
        src_end_cluster_text=None,
        ref_start_cluster_text=None,
        ref_end_cluster_text=None
    )

    c_instance.create_new_preset()

    mock_append_to_file.assert_called_once()
    mock_write_yaml.assert_not_called()


@pytest.mark.integration
@patch.object(ConfigManager, 'ask_open_question')
@patch.object(Path, 'exists', return_value=False)
@patch.object(utils, 'write_yaml')
@patch.object(utils, 'write_txt')
def test_create_new_preset_retries_on_empty_name(mock_write_txt: Mock, mock_write_yaml: Mock, mock_exists: Mock, mock_ask_open: Mock, c_instance: ConfigManager) -> None:
    """Test preset creation retries when empty name is provided."""
    # Simulate empty input first, then a valid preset name
    mock_ask_open.side_effect = ['', '  ', 'final_preset', 'my_preset_file']

    c_instance.configurations = [MagicMock(config={'cluster_filter': '\\n'})]
    c_instance.presets_directory = Path('/fake_dir')

    c_instance.initialized_config = Initialized(
        cluster_filter='\\n',
        text_filter_type=None,
        text_filter=None,
        should_slice_clusters=None,
        src_start_cluster_text=None,
        src_end_cluster_text=None,
        ref_start_cluster_text=None,
        ref_end_cluster_text=None
    )

    c_instance.create_new_preset()

    # Verify that write_yaml is eventually called once
    mock_write_yaml.assert_called_once()
    mock_write_txt.assert_not_called()

    # Verify the preset data passed to write_yaml
    written_data = mock_write_yaml.call_args[0][0]
    assert 'final_preset' in written_data

    expected_config: dict[str, Any] = {
        'cluster_filter': '\\n'
    }
    assert written_data['final_preset'] == expected_config

    # Verify ask_open_question was called multiple times due to retries
    assert mock_ask_open.call_count >= 3
