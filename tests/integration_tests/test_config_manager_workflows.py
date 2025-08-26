"""Clean integration tests for GenEC ConfigManager workflows."""

from typing import Any
from unittest.mock import patch, Mock
import pytest

from GenEC.core.config_manager import ConfigManager
from GenEC.core.configuration import RegexConfiguration


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
            'cluster_filter': r'\n',
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


@pytest.fixture
def c_instance() -> ConfigManager:
    """Create ConfigManager instance for testing."""
    return ConfigManager(auto_configure=False)


class TestConfigManagerWorkflows:
    """Test ConfigManager integration workflows."""

    @pytest.mark.integration
    @patch.object(ConfigManager, 'load_preset_file')
    def test_init_with_preset_type(self, mock_load_preset_file: Mock) -> None:
        """Test initialization with preset type."""
        mock_load_preset_file.return_value = create_test_preset_data()

        preset_param = {'type': 'preset', 'value': 'test_preset'}
        config_manager = ConfigManager(preset_param=preset_param)

        assert len(config_manager.configurations) == 1

    @pytest.mark.integration
    @patch('GenEC.core.configuration_factory.WorkflowConfigurationFactory.create_preset_list_configs')
    @pytest.mark.parametrize('mock_configs, expected_count', [
        ([RegexConfiguration(cluster_filter=r'\n', should_slice_clusters=False, text_filter='test1')], 1),
        ([RegexConfiguration(cluster_filter=r'\n', should_slice_clusters=False, text_filter='test1'),
          RegexConfiguration(cluster_filter=r'\n', should_slice_clusters=False, text_filter='test2')], 2)
    ])
    def test_init_with_preset_list_type(self, mock_create_configs: Mock, mock_configs: list, expected_count: int) -> None:
        """Test initialization with preset-list type."""
        mock_create_configs.return_value = mock_configs

        preset_param = {'type': 'preset-list', 'value': 'test_list'}
        config_manager = ConfigManager(preset_param=preset_param)

        assert len(config_manager.configurations) == expected_count

    @pytest.mark.integration
    def test_init_with_invalid_type(self) -> None:
        """Test initialization with invalid preset type."""
        preset_param = {'type': 'invalid_type', 'value': 'test'}

        with pytest.raises(ValueError, match='is not a valid preset parameter type'):
            ConfigManager(preset_param=preset_param)

    @pytest.mark.integration
    @patch.object(ConfigManager, 'load_preset_file')
    @patch.object(ConfigManager, 'ask_mpc_question')
    def test_load_preset_no_preset_name(self, mockask_mpc_question: Mock, mock_load_preset_file: Mock, c_instance: ConfigManager) -> None:
        """Test loading preset when no preset name is provided."""
        multiple_presets = create_multiple_presets_data()
        mock_load_preset_file.return_value = multiple_presets
        mockask_mpc_question.return_value = preset_name = 'main_preset'
        result = c_instance.load_preset(preset_target='')

        mockask_mpc_question.assert_called_once_with(
            'Multiple presets found in . Choose one:',
            ['main_preset', 'sub_preset_A', 'sub_preset_B']
        )
        assert result == multiple_presets[preset_name]

    @pytest.mark.integration
    @patch.object(ConfigManager, 'load_preset_file')
    def test_load_preset_invalid_preset_name(self, mock_load_preset_file: Mock, c_instance: ConfigManager) -> None:
        """Test loading preset with invalid preset name."""
        test_presets = create_test_preset_data()
        mock_load_preset_file.return_value = test_presets

        with pytest.raises(ValueError, match="Preset 'invalid_preset' not found"):
            c_instance.load_preset('test_file/invalid_preset')

    @pytest.mark.integration
    @patch.object(ConfigManager, 'load_preset_file')
    def test_load_from_single_preset(self, mock_load_preset_file: Mock, c_instance: ConfigManager) -> None:
        """Test loading from file with single preset."""
        test_presets = create_test_preset_data()
        mock_load_preset_file.return_value = test_presets

        result = c_instance.load_preset('test_file')

        assert result == test_presets['main_preset']

    @pytest.mark.integration
    @patch.object(ConfigManager, 'load_preset_file')
    @pytest.mark.parametrize('preset_name', ['main_preset', 'sub_preset_A'])
    def test_load_from_multiple_presets_existing_preset_name(self, mock_load_preset_file: Mock, preset_name: str, c_instance: ConfigManager) -> None:
        """Test loading specific preset from multiple presets."""
        multiple_presets = create_multiple_presets_data()
        mock_load_preset_file.return_value = multiple_presets

        result = c_instance.load_preset(f'test_file/{preset_name}')

        assert result == multiple_presets[preset_name]

    @pytest.mark.integration
    @patch('GenEC.core.configuration_factory.BasicConfigurationFactory.build_interactive')
    def test_set_config_no_preset(self, mock_build: Mock, c_instance: ConfigManager) -> None:
        """Test set_config without preset (interactive mode)."""
        mock_config = RegexConfiguration(
            cluster_filter=r'\n',
            should_slice_clusters=False,
            text_filter='test.*'
        )
        mock_build.return_value = mock_config

        c_instance.set_config()

        mock_build.assert_called_once_with(c_instance)
        assert len(c_instance.configurations) == 1
        assert c_instance.configurations[0] == mock_config
