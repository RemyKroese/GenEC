"""Clean unit tests for GenEC ConfigurationManager individual methods."""
# pylint: disable=protected-access

from __future__ import annotations

from typing import Any
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from GenEC.core.configuration_manager import BasicConfigurationManager
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
            'should_slice_clusters': False,
            'src_start_cluster_text': '',
            'src_end_cluster_text': '',
            'ref_start_cluster_text': '',
            'ref_end_cluster_text': ''
        },
        'sub_preset_B': {
            'cluster_filter': '',
            'text_filter_type': 'Positional',
            'text_filter': {'separator': '=', 'line': 1, 'occurrence': 2},
            'should_slice_clusters': False,
            'src_start_cluster_text': '',
            'src_end_cluster_text': '',
            'ref_start_cluster_text': '',
            'ref_end_cluster_text': ''
        }
    })
    return base_data


@pytest.fixture
@patch.object(BasicConfigurationManager, '__init__', lambda x, **kwargs: None)
def c_instance() -> BasicConfigurationManager:
    """Create a BasicConfigurationManager instance for testing."""
    instance = BasicConfigurationManager()
    instance.presets_directory = Path('/fake/presets')
    instance.configurations = []
    return instance


class TestConfigurationManagerUserInteraction:
    """Test user interaction methods."""

    @pytest.mark.unit
    @patch('builtins.input')
    def test_ask_open_question(self, mock_input: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test ask_open_question method."""
        mock_input.return_value = 'test_response'
        result = c_instance.ask_open_question('Test question: ')
        assert result == 'test_response'
        mock_input.assert_called_once()

    @pytest.mark.unit
    @patch('builtins.input')
    def test_ask_mpc_question_valid_choice(self, mock_input: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test ask_mpc_question with valid choice."""
        mock_input.return_value = '1'
        options = ['option1', 'option2', 'option3']
        result = c_instance.ask_mpc_question('Choose option:', options)
        assert result == 'option1'

    @pytest.mark.unit
    @patch('builtins.input')
    def test_ask_mpc_question_exit_choice(self, mock_input: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test ask_mpc_question with exit choice."""
        mock_input.return_value = '0'
        options = ['option1', 'option2']

        with pytest.raises(SystemExit):
            c_instance.ask_mpc_question('Choose option:', options)

    @pytest.mark.unit
    @patch('builtins.input')
    def test_get_user_choice_valid(self, mock_input: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test _get_user_choice with valid input."""
        mock_input.return_value = '2'
        result = c_instance._get_user_choice(3)
        assert result == 2

    @pytest.mark.unit
    @patch('builtins.input')
    def test_get_user_choice_invalid_then_valid(self, mock_input: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test _get_user_choice with invalid then valid input."""
        mock_input.side_effect = ['invalid', '10', '2']
        result = c_instance._get_user_choice(3)
        assert result == 2
        assert mock_input.call_count == 3


class TestConfigurationManagerPresetLoading:
    """Test preset loading methods."""

    @pytest.mark.unit
    @patch('GenEC.utils.read_yaml_file')
    @patch.object(BasicConfigurationManager, '__init__', lambda x, **kwargs: None)
    def test_load_preset_file_success(self, mock_read_yaml: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test successful preset file loading."""
        # Manually set the presets_directory since __init__ is mocked
        c_instance.presets_directory = Path('/fake/presets')
        mock_read_yaml.return_value = create_test_preset_data()

        # Mock the file existence check
        with patch('pathlib.Path.exists', return_value=True):
            result = c_instance.load_preset_file('test_preset')

        mock_read_yaml.assert_called_once()
        assert result == create_test_preset_data()

    @pytest.mark.unit
    @patch('GenEC.utils.read_yaml_file')
    def test_load_preset_file_not_found(self, mock_read_yaml: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test preset file not found."""
        with pytest.raises(FileNotFoundError):
            c_instance.load_preset_file('nonexistent')

    @pytest.mark.unit
    @patch.object(BasicConfigurationManager, 'load_preset_file')
    def test_load_preset_with_file_and_name(self, mock_load_file: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test loading preset with file/name format."""
        mock_load_file.return_value = create_multiple_presets_data()

        result = c_instance.load_preset('test_file/sub_preset_A')

        mock_load_file.assert_called_once_with('test_file')
        expected = create_multiple_presets_data()['sub_preset_A']
        assert result == expected

    @pytest.mark.unit
    @patch.object(BasicConfigurationManager, 'load_preset_file')
    def test_load_preset_just_name(self, mock_load_file: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test loading preset with just name (no file specified)."""
        mock_load_file.return_value = create_test_preset_data()

        result = c_instance.load_preset('main_preset')

        mock_load_file.assert_called_once_with('main_preset')
        expected = create_test_preset_data()['main_preset']
        assert result == expected


class TestConfigurationManagerGrouping:
    """Test preset grouping functionality."""

    @pytest.mark.unit
    def test_group_presets_by_file_basic(self, c_instance: BasicConfigurationManager) -> None:
        """Test basic preset grouping by file."""
        grouped_entries = {
            'group_1': [
                {'preset': 'p/preset_numbers', 'target': 'file1.txt'},
                {'preset': 'p/preset_letters', 'target': 'file2.txt'}
            ],
            'group_2': [
                {'preset': 'p/preset_dates', 'target': 'file3.txt'},
                {'preset': 'p/preset_code_value', 'target': 'file2.txt'}
            ]
        }

        results = c_instance.group_presets_by_file(grouped_entries)

        expected = {
            'file1.txt': [
                {'group': 'group_1', 'preset': 'p/preset_numbers', 'target': 'file1.txt'}
            ],
            'file2.txt': [
                {'group': 'group_1', 'preset': 'p/preset_letters', 'target': 'file2.txt'},
                {'group': 'group_2', 'preset': 'p/preset_code_value', 'target': 'file2.txt'}
            ],
            'file3.txt': [
                {'group': 'group_2', 'preset': 'p/preset_dates', 'target': 'file3.txt'}
            ]
        }

        assert results == expected

    @pytest.mark.unit
    def test_group_presets_by_file_with_variables(self, c_instance: BasicConfigurationManager) -> None:
        """Test preset grouping with variable substitution."""
        grouped_entries = {
            'group_1': [
                {'preset': 'p/preset_a', 'target': '{loc}/{prefix}_1.txt'},
                {'preset': 'p/preset_b', 'target': '{loc}/{prefix}_2.txt'}
            ]
        }

        target_variables = {'loc': 'data', 'prefix': 'test'}

        results = c_instance.group_presets_by_file(grouped_entries, target_variables)

        expected = {
            'data/test_1.txt': [
                {'group': 'group_1', 'preset': 'p/preset_a', 'target': 'data/test_1.txt'}
            ],
            'data/test_2.txt': [
                {'group': 'group_1', 'preset': 'p/preset_b', 'target': 'data/test_2.txt'}
            ]
        }

        assert results == expected


class TestConfigurationManagerConfiguration:
    """Test configuration-related methods."""

    @pytest.mark.unit
    @patch.object(BasicConfigurationManager, 'ask_open_question')
    def test_should_store_configuration_yes(self, mock_ask: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test should_store_configuration returns True for yes."""
        mock_ask.return_value = 'yes'

        result = c_instance.should_store_configuration()

        assert result is True

    @pytest.mark.unit
    @patch.object(BasicConfigurationManager, 'ask_open_question')
    def test_should_store_configuration_no(self, mock_ask: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test should_store_configuration returns False for no."""
        mock_ask.return_value = 'no'

        result = c_instance.should_store_configuration()

        assert result is False

    @pytest.mark.unit
    def test_get_preset_data_with_configuration(self, c_instance: BasicConfigurationManager) -> None:
        """Test _get_preset_data with existing configuration."""
        # Create a test configuration
        test_config = RegexConfiguration(
            cluster_filter=r'\n',
            text_filter='test.*pattern',
            should_slice_clusters=False,
            preset='test_preset',
            target_file='test.txt',
            group='test_group'
        )
        c_instance.configurations = [test_config]

        result = c_instance._get_preset_data()

        expected = {
            'cluster_filter': r'\n',
            'text_filter_type': 'Regex',
            'text_filter': 'test.*pattern',
            'should_slice_clusters': False
        }

        assert result == expected

    @pytest.mark.unit
    def test_get_preset_data_no_configuration(self, c_instance: BasicConfigurationManager) -> None:
        """Test _get_preset_data with no configuration returns empty dict."""
        c_instance.configurations = []

        result = c_instance._get_preset_data()

        assert result == {}
