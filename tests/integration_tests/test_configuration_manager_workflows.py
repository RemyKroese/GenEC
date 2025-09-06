"""Integration tests for GenEC ConfigurationManager workflow integration."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch, Mock
import pytest

from GenEC.core.configuration_manager import (
    BasicConfigurationManager, PresetConfigurationManager, BatchConfigurationManager
)


def create_test_preset() -> dict[str, Any]:
    """Create standard test preset data."""
    return {
        'cluster_filter': '',
        'text_filter_type': 'Regex',
        'text_filter': '',
        'should_slice_clusters': False,
        'src_start_cluster_text': '',
        'src_end_cluster_text': '',
        'ref_start_cluster_text': '',
        'ref_end_cluster_text': ''
    }


@pytest.fixture
@patch.object(PresetConfigurationManager, '__init__', lambda x, **kwargs: None)
def preset_instance() -> PresetConfigurationManager:
    """Create PresetConfigurationManager instance for testing."""
    instance = PresetConfigurationManager()
    instance.configurations = []
    return instance


@pytest.fixture
@patch.object(BatchConfigurationManager, '__init__', lambda x, **kwargs: None)
def batch_instance() -> BatchConfigurationManager:
    """Create BatchConfigurationManager instance for testing."""
    instance = BatchConfigurationManager()
    instance.configurations = []
    return instance


@pytest.mark.integration
@patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_mpc_question')
@patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
def test_basic_initialization_integration(mock_ask_open: Mock, mock_ask_mpc: Mock) -> None:
    """Test basic configuration manager initialization with interactive configuration."""
    mock_ask_mpc.return_value = 'Regex'
    mock_ask_open.side_effect = [r'\n', 'test.*', 'n']

    basic_manager = BasicConfigurationManager()
    basic_manager.initialize_configuration()

    assert len(basic_manager.configurations) == 1
    config = basic_manager.configurations[0]
    assert config.cluster_filter == r'\n'
    assert config.text_filter == 'test.*'
    assert config.should_slice_clusters is False


@pytest.mark.integration
@patch('GenEC.core.configuration_manager.PresetConfigurationManager.load_preset')
def test_preset_initialization_integration_old(mock_load_preset: Mock) -> None:
    """Test preset configuration manager initialization with preset loading."""
    preset_data = {
        'cluster_filter': r'\n',
        'text_filter_type': 'Regex',
        'text_filter': 'test.*',
        'should_slice_clusters': False
    }
    mock_load_preset.return_value = preset_data

    preset_manager = PresetConfigurationManager(preset='test_preset')
    preset_manager.initialize_configuration()

    assert len(preset_manager.configurations) == 1
    config = preset_manager.configurations[0]
    assert config.cluster_filter == r'\n'
    assert config.text_filter == 'test.*'
    assert config.should_slice_clusters is False


@pytest.mark.integration
@patch.object(PresetConfigurationManager, 'load_preset_file')
@patch.object(PresetConfigurationManager, 'ask_mpc_question')
def test_load_preset_no_preset_name(mock_ask_mpc_question: Mock, mock_load_preset_file: Mock,
                                    preset_instance: PresetConfigurationManager) -> None:
    """Test loading preset when no preset name is provided."""
    multiple_presets = {
        'main_preset': create_test_preset(),
        'sub_preset_A': create_test_preset(),
        'sub_preset_B': create_test_preset()
    }
    mock_load_preset_file.return_value = multiple_presets
    mock_ask_mpc_question.return_value = preset_name = 'main_preset'

    result = preset_instance.load_preset(preset_target='')

    mock_ask_mpc_question.assert_called_once_with(
        'Multiple presets found in . Choose one:',
        ['main_preset', 'sub_preset_A', 'sub_preset_B']
    )
    assert result == multiple_presets[preset_name]


@pytest.mark.integration
@patch.object(PresetConfigurationManager, 'load_preset_file')
def test_load_preset_invalid_preset_name(mock_load_preset_file: Mock, preset_instance: PresetConfigurationManager) -> None:
    """Test loading preset with invalid preset name."""
    test_presets = {'main_preset': create_test_preset()}
    mock_load_preset_file.return_value = test_presets

    with pytest.raises(ValueError, match="Preset 'invalid_preset' not found"):
        preset_instance.load_preset('test_file/invalid_preset')


@pytest.mark.integration
@patch.object(PresetConfigurationManager, 'load_preset_file')
def test_load_from_single_preset(mock_load_preset_file: Mock, preset_instance: PresetConfigurationManager) -> None:
    """Test loading from file with single preset."""
    test_presets = {'main_preset': create_test_preset()}
    mock_load_preset_file.return_value = test_presets

    result = preset_instance.load_preset('test_file')

    assert result == test_presets['main_preset']


@pytest.mark.integration
@patch.object(PresetConfigurationManager, 'load_preset_file')
@pytest.mark.parametrize('preset_name', ['main_preset', 'sub_preset_A'])
def test_load_from_multiple_presets_existing_preset_name(mock_load_preset_file: Mock,
                                                         preset_name: str, preset_instance: PresetConfigurationManager) -> None:
    """Test loading specific preset from multiple presets."""
    multiple_presets = {
        'main_preset': create_test_preset(),
        'sub_preset_A': create_test_preset()
    }
    mock_load_preset_file.return_value = multiple_presets

    result = preset_instance.load_preset(f'test_file/{preset_name}')

    assert result == multiple_presets[preset_name]


@pytest.mark.integration
@patch('GenEC.core.configuration_manager.BatchConfigurationManager.group_presets_by_file')
@patch('GenEC.utils.read_yaml_file')
def test_batch_initialization_integration(mock_read_yaml: Mock, mock_group_presets: Mock) -> None:
    """Test batch configuration manager initialization with preset list loading."""
    mock_read_yaml.return_value = {'group1': [{'preset': 'file/preset1', 'target': 'file1.txt'}]}
    mock_group_presets.return_value = {'file1.txt': [{'preset': 'file/preset1', 'target': 'file1.txt', 'group': 'group1'}]}

    with patch.object(BatchConfigurationManager, 'load_preset') as mock_load_preset:
        mock_load_preset.return_value = create_test_preset()

        batch_manager = BatchConfigurationManager(preset_list='test_list')
        batch_manager.initialize_configuration()

        assert len(batch_manager.configurations) == 1
        config = batch_manager.configurations[0]
        assert config.cluster_filter == ''
        assert config.text_filter == ''
        assert config.should_slice_clusters is False


@pytest.mark.integration
def test_load_preset_from_subdirectory() -> None:
    """Test loading presets from subdirectories in presets directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        presets_dir = temp_path / 'presets'
        subdir = presets_dir / 'subdir'
        subdir.mkdir(parents=True)

        # Create test preset file
        preset_content = """subdirectory_preset:
  cluster_filter: '\\n'
  text_filter_type: 'Regex'
  text_filter: '([0-9]+)'
  should_slice_clusters: false"""

        (subdir / 'subdirectory_test.yaml').write_text(preset_content, encoding='utf-8')

        preset_manager = PresetConfigurationManager(
            presets_directory=str(presets_dir),
            preset='subdir/subdirectory_test/subdirectory_preset'
        )

        preset_manager.initialize_configuration()

        assert len(preset_manager.configurations) == 1
        config = preset_manager.configurations[0]
        assert config.cluster_filter == '\\n'
        assert config.text_filter == '([0-9]+)'
        assert config.filter_type == 'Regex'


@pytest.mark.integration
def test_load_preset_from_deep_subdirectory() -> None:
    """Test loading presets from deeply nested subdirectories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        presets_dir = temp_path / 'presets'
        deep_subdir = presets_dir / 'subdir' / 'deeper'
        deep_subdir.mkdir(parents=True)

        # Create test preset file
        preset_content = """deep_preset:
  cluster_filter: '\\n'
  text_filter_type: 'Regex'
  text_filter: 'deep_([0-9]+)'
  should_slice_clusters: false"""

        (deep_subdir / 'deep_preset.yaml').write_text(preset_content, encoding='utf-8')

        preset_manager = PresetConfigurationManager(
            presets_directory=str(presets_dir),
            preset='subdir/deeper/deep_preset/deep_preset'
        )

        preset_manager.initialize_configuration()

        assert len(preset_manager.configurations) == 1
        config = preset_manager.configurations[0]
        assert config.cluster_filter == '\\n'
        assert config.text_filter == 'deep_([0-9]+)'
        assert config.filter_type == 'Regex'


@pytest.mark.integration
def test_preset_list_with_subdirectories() -> None:
    """Test preset-list functionality with subdirectory presets."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        presets_dir = temp_path / 'presets'
        subdir = presets_dir / 'subdir'
        subdir.mkdir(parents=True)

        # Create subdirectory preset file
        subdirectory_preset_content = """subdirectory_preset:
  cluster_filter: '\\n'
  text_filter_type: 'Regex'
  text_filter: '([0-9]+)'
  should_slice_clusters: false"""

        (subdir / 'subdirectory_test.yaml').write_text(subdirectory_preset_content, encoding='utf-8')

        # Create parent directory preset file
        parent_preset_content = """parent_preset:
  cluster_filter: '\\n'
  text_filter_type: 'Regex'
  text_filter: '[0-9]+'
  should_slice_clusters: false"""

        (presets_dir / 'parent_preset.yaml').write_text(parent_preset_content, encoding='utf-8')

        # Create preset-list file
        preset_list_content = """subdir_preset_list:
  - preset: 'subdir/subdirectory_test/subdirectory_preset'
    target: 'file1.txt'
  - preset: 'parent_preset/parent_preset'
    target: 'file2.txt'"""

        (subdir / 'subdirectory_preset_list.yaml').write_text(preset_list_content, encoding='utf-8')

        batch_manager = BatchConfigurationManager(
            presets_directory=str(presets_dir),
            preset_list='subdir/subdirectory_preset_list'
        )

        batch_manager.initialize_configuration()

        # Should load configurations from the preset list
        assert len(batch_manager.configurations) >= 1

        # Check that we can load presets from both subdirectory and parent directory
        config_filters = [config.text_filter for config in batch_manager.configurations]
        assert any('([0-9]+)' in str(filter_val) for filter_val in config_filters)  # subdirectory preset
        assert any('[0-9]+' == str(filter_val) for filter_val in config_filters)  # parent directory preset
