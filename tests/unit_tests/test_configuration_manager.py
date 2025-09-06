"""Clean unit tests for GenEC ConfigurationManager individual methods."""
# pylint: disable=protected-access

from __future__ import annotations

from typing import Any
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from GenEC.core.configuration_manager import BasicConfigurationManager, PresetConfigurationManager, BatchConfigurationManager
from GenEC.core.configuration import RegexConfiguration, PositionalConfiguration, RegexListConfiguration
from GenEC.core.specs import PositionalFilterType, DEFAULT_PRESETS_DIRECTORY


def create_test_preset_data() -> dict[str, dict[str, Any]]:
    """Create standard test preset data."""
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
    """Create multiple test presets."""
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
    """Create BasicConfigurationManager instance for testing."""
    instance = BasicConfigurationManager()
    instance.presets_directory = Path('/fake/presets')
    instance.configurations = []
    return instance


class TestConfigurationManagerConstructor:
    """Test ConfigurationManager constructor behavior."""

    @pytest.mark.unit
    def test_constructor_default_presets_directory(self) -> None:
        """Test constructor with default presets directory."""
        manager = BasicConfigurationManager()
        assert manager.presets_directory == DEFAULT_PRESETS_DIRECTORY

    @pytest.mark.unit
    def test_constructor_with_custom_presets_directory(self) -> None:
        """Test constructor with custom presets directory."""
        custom_path = '/custom/preset/path'
        manager = BasicConfigurationManager(presets_directory=custom_path)
        assert manager.presets_directory == Path(custom_path)


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
        c_instance.presets_directory = Path('/fake/presets')
        mock_read_yaml.return_value = create_test_preset_data()

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

    @pytest.mark.unit
    @patch.object(BasicConfigurationManager, 'load_preset_file')
    def test_load_preset_with_subdirectory_path(self, mock_load_file: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test loading preset with subdirectory path format."""
        mock_load_file.return_value = create_multiple_presets_data()

        result = c_instance.load_preset('subdir/test_file/sub_preset_A')

        mock_load_file.assert_called_once_with('subdir/test_file')
        expected = create_multiple_presets_data()['sub_preset_A']
        assert result == expected

    @pytest.mark.unit
    @patch.object(BasicConfigurationManager, 'load_preset_file')
    def test_load_preset_with_deep_subdirectory_path(self, mock_load_file: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test loading preset with deeply nested subdirectory path format."""
        mock_load_file.return_value = create_test_preset_data()

        result = c_instance.load_preset('level1/level2/level3/preset_file/main_preset')

        mock_load_file.assert_called_once_with('level1/level2/level3/preset_file')
        expected = create_test_preset_data()['main_preset']
        assert result == expected

    @pytest.mark.unit
    @patch.object(BasicConfigurationManager, 'load_preset_file')
    def test_load_preset_subdirectory_just_name(self, mock_load_file: Mock, c_instance: BasicConfigurationManager) -> None:
        """Test loading preset with subdirectory in filename but no preset name."""
        mock_load_file.return_value = create_test_preset_data()

        result = c_instance.load_preset('subdir/main_preset')

        mock_load_file.assert_called_once_with('subdir')
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


class TestBasicConfigurationManagerInteractive:
    """Test interactive configuration building methods."""

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_mpc_question')
    def test_build_interactive_configuration_regex(self, mock_ask_mpc: Mock, mock_ask_open: Mock) -> None:
        """Test building interactive configuration with regex filter."""
        mock_ask_mpc.return_value = 'Regex'
        mock_ask_open.side_effect = [r'\s+', 'test.*', 'n']

        manager = BasicConfigurationManager()
        config = manager._build_interactive_configuration()

        assert config.cluster_filter == r'\s+'
        assert config.text_filter == 'test.*'
        assert config.should_slice_clusters is False
        assert config.filter_type == 'Regex'

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_mpc_question')
    def test_build_interactive_configuration_regex_list(self, mock_ask_mpc: Mock, mock_ask_open: Mock) -> None:
        """Test building interactive configuration with regex list filter."""
        mock_ask_mpc.return_value = 'Regex-list'
        mock_ask_open.side_effect = [
            r'\n',              # cluster filter
            'pattern1',         # first regex
            'yes',              # continue adding
            'pattern2',         # second regex
            'no',               # stop adding
            'n'                 # should slice clusters
        ]

        manager = BasicConfigurationManager()
        config = manager._build_interactive_configuration()

        assert config.cluster_filter == r'\n'
        assert config.text_filter == ['pattern1', 'pattern2']
        assert config.should_slice_clusters is False
        assert config.filter_type == 'Regex-list'

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_mpc_question')
    def test_build_interactive_configuration_positional(self, mock_ask_mpc: Mock, mock_ask_open: Mock) -> None:
        """Test building interactive configuration with positional filter."""
        mock_ask_mpc.return_value = 'Positional'
        mock_ask_open.side_effect = [
            '',                 # empty cluster filter -> defaults to \n
            '=',                # separator
            '2',                # line
            '3',                # occurrence
            'no'                # don't slice clusters
        ]

        manager = BasicConfigurationManager()
        config = manager._build_interactive_configuration()

        assert config.cluster_filter == r'\n'
        assert isinstance(config.text_filter, PositionalFilterType)
        assert config.text_filter.separator == '='
        assert config.text_filter.line == 2
        assert config.text_filter.occurrence == 3
        assert config.should_slice_clusters is False

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_mpc_question')
    def test_build_interactive_configuration_with_slicing(self, mock_ask_mpc: Mock, mock_ask_open: Mock) -> None:
        """Test interactive configuration with cluster slicing enabled."""
        mock_ask_mpc.return_value = 'Regex'
        mock_ask_open.side_effect = [
            r'\n',              # cluster filter
            'test.*',           # regex pattern
            'yes',              # enable slicing
            'start_marker',     # src start
            'end_marker',       # src end
            'ref_start',        # ref start
            'ref_end'           # ref end
        ]

        manager = BasicConfigurationManager()
        config = manager._build_interactive_configuration()

        assert config.should_slice_clusters is True
        assert config.src_start_cluster_text == 'start_marker'
        assert config.src_end_cluster_text == 'end_marker'
        assert config.ref_start_cluster_text == 'ref_start'
        assert config.ref_end_cluster_text == 'ref_end'

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_mpc_question')
    def test_build_interactive_configuration_empty_slicing_fields(self, mock_ask_mpc: Mock, mock_ask_open: Mock) -> None:
        """Test interactive configuration with empty slicing fields."""
        mock_ask_mpc.return_value = 'Regex'
        mock_ask_open.side_effect = [
            r'\n',              # cluster filter
            'test.*',           # regex pattern
            'yes',              # enable slicing
            '',                 # empty src start
            '',                 # empty src end
            '',                 # empty ref start
            ''                  # empty ref end
        ]

        manager = BasicConfigurationManager()
        config = manager._build_interactive_configuration()

        assert config.should_slice_clusters is True
        assert config.src_start_cluster_text is None
        assert config.src_end_cluster_text is None
        assert config.ref_start_cluster_text is None
        assert config.ref_end_cluster_text is None

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_mpc_question')
    def test_configure_regex_list_break_on_empty(self, mock_ask_mpc: Mock, mock_ask_open: Mock) -> None:
        """Test regex list configuration breaking on empty pattern."""
        mock_ask_mpc.return_value = 'Regex-list'
        mock_ask_open.side_effect = [
            r'\n',              # cluster filter
            'pattern1',         # first regex
            '',                 # empty pattern - should break
            'n'                 # should slice clusters
        ]

        manager = BasicConfigurationManager()
        config = manager._build_interactive_configuration()

        assert config.text_filter == ['pattern1']

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_mpc_question')
    def test_configure_regex_list_empty_first_pattern(self, mock_ask_mpc: Mock, mock_ask_open: Mock) -> None:
        """Test regex list configuration with empty first pattern."""
        mock_ask_mpc.return_value = 'Regex-list'
        mock_ask_open.side_effect = [
            r'\n',              # cluster filter
            '',                 # empty pattern immediately - should break
            'n'                 # should slice clusters
        ]

        manager = BasicConfigurationManager()
        config = manager._build_interactive_configuration()

        assert config.text_filter == []

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_mpc_question')
    def test_configure_text_filter_unknown_type(self, mock_ask_mpc: Mock, mock_ask_open: Mock) -> None:
        """Test _configure_text_filter with unknown filter type."""
        # Test the implicit return at end of method (line 293->exit coverage)
        mock_ask_mpc.return_value = 'UnknownType'
        mock_ask_open.side_effect = [r'\n']  # cluster filter

        manager = BasicConfigurationManager()
        builder = Mock()

        # This should not raise an error, just not call any configure method
        manager._configure_text_filter(builder, 'UnknownType')

        # None of the configure methods should have been called
        assert not hasattr(builder, 'method_calls') or len([call for call in builder.method_calls if 'configure' in str(call)]) == 0

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_mpc_question')
    def test_configure_positional_validation_errors(self, mock_ask_mpc: Mock, mock_ask_open: Mock) -> None:
        """Test positional filter configuration with validation errors."""
        mock_ask_mpc.return_value = 'Positional'
        mock_ask_open.side_effect = [
            r'\n',              # cluster filter
            '=',                # separator
            '',                 # empty line - should raise error
            '1'                 # occurrence (won't be reached)
        ]

        manager = BasicConfigurationManager()
        with pytest.raises(ValueError, match="Line number is required"):
            manager._build_interactive_configuration()

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_mpc_question')
    def test_configure_positional_occurrence_validation_error(self, mock_ask_mpc: Mock, mock_ask_open: Mock) -> None:
        """Test positional filter configuration with occurrence validation error."""
        mock_ask_mpc.return_value = 'Positional'
        mock_ask_open.side_effect = [
            r'\n',              # cluster filter
            '=',                # separator
            '1',                # line
            ''                  # empty occurrence - should raise error
        ]

        manager = BasicConfigurationManager()
        with pytest.raises(ValueError, match="Occurrence number is required"):
            manager._build_interactive_configuration()


class TestBasicConfigurationManagerPresetCreation:
    """Test preset creation functionality."""

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    @patch('GenEC.utils.write_yaml')
    @patch('pathlib.Path.exists')
    def test_create_new_preset_new_file(self, mock_exists: Mock, mock_write_yaml: Mock, mock_ask_open: Mock) -> None:
        """Test creating preset in new file."""
        mock_ask_open.side_effect = ['test_preset', 'new_file']
        mock_exists.return_value = False

        manager = BasicConfigurationManager()
        manager.configurations = [RegexConfiguration(
            cluster_filter=r'\n',
            text_filter='test.*',
            should_slice_clusters=False,
            preset='',
            target_file='',
            group=''
        )]

        manager.create_new_preset()

        mock_write_yaml.assert_called_once()
        expected_path = manager.presets_directory / 'new_file.yaml'
        mock_write_yaml.assert_called_with({'test_preset': {
            'cluster_filter': r'\n',
            'text_filter_type': 'Regex',
            'text_filter': 'test.*',
            'should_slice_clusters': False
        }}, expected_path)

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    @patch('GenEC.utils.append_to_file')
    @patch('GenEC.utils.convert_to_yaml')
    @patch('pathlib.Path.exists')
    def test_create_new_preset_existing_file(self, mock_exists: Mock, mock_convert_yaml: Mock,
                                           mock_append: Mock, mock_ask_open: Mock) -> None:
        """Test creating preset in existing file."""
        mock_ask_open.side_effect = ['test_preset', 'existing_file']
        mock_exists.return_value = True
        mock_convert_yaml.return_value = 'yaml_data'

        manager = BasicConfigurationManager()
        manager.configurations = [RegexConfiguration(
            cluster_filter=r'\n',
            text_filter='test.*',
            should_slice_clusters=False,
            preset='',
            target_file='',
            group=''
        )]

        manager.create_new_preset()

        expected_path = manager.presets_directory / 'existing_file.yaml'
        assert mock_append.call_count == 2
        mock_append.assert_any_call('\ntest_preset:\n', expected_path)
        mock_append.assert_any_call('yaml_data', expected_path)

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.BasicConfigurationManager.ask_open_question')
    def test_create_new_preset_empty_name_retry(self, mock_ask_open: Mock) -> None:
        """Test preset creation with empty name requiring retry."""
        mock_ask_open.side_effect = ['', '  ', 'valid_preset', 'test_file']

        manager = BasicConfigurationManager()
        manager.configurations = [RegexConfiguration(
            cluster_filter=r'\n',
            text_filter='test.*',
            should_slice_clusters=False,
            preset='',
            target_file='',
            group=''
        )]

        with patch('GenEC.utils.write_yaml'), patch('pathlib.Path.exists', return_value=False):
            manager.create_new_preset()

        assert mock_ask_open.call_count == 4

    @pytest.mark.unit
    def test_create_new_preset_no_configuration(self) -> None:
        """Test preset creation with no configuration raises error."""
        manager = BasicConfigurationManager()

        with pytest.raises(ValueError, match="No configuration available"):
            manager.create_new_preset()

    @pytest.mark.unit
    def test_get_preset_data_with_positional_config(self) -> None:
        """Test preset data generation with positional configuration."""
        manager = BasicConfigurationManager()
        positional_filter = PositionalFilterType(separator='=', line=1, occurrence=2)
        manager.configurations = [PositionalConfiguration(
            cluster_filter=r'\n',
            text_filter=positional_filter,
            should_slice_clusters=True,
            src_start_cluster_text='start',
            src_end_cluster_text='end',
            ref_start_cluster_text='ref_start',
            ref_end_cluster_text='ref_end',
            preset='test',
            target_file='file.txt',
            group='group1'
        )]

        result = manager._get_preset_data()

        expected = {
            'cluster_filter': r'\n',
            'text_filter_type': 'Positional',
            'text_filter': {'separator': '=', 'line': 1, 'occurrence': 2},
            'should_slice_clusters': True,
            'src_start_cluster_text': 'start',
            'src_end_cluster_text': 'end',
            'ref_start_cluster_text': 'ref_start',
            'ref_end_cluster_text': 'ref_end'
        }
        assert result == expected


class TestPresetConfigurationManager:
    """Test PresetConfigurationManager functionality."""

    @pytest.mark.unit
    @patch('GenEC.core.configuration_manager.PresetConfigurationManager.load_preset')
    def test_build_preset_configuration(self, mock_load_preset: Mock) -> None:
        """Test building preset configuration."""
        mock_load_preset.return_value = {
            'cluster_filter': r'\s+',
            'text_filter_type': 'Regex',
            'text_filter': 'test.*',
            'should_slice_clusters': False
        }

        manager = PresetConfigurationManager(preset='test_preset')
        config = manager._build_preset_configuration('test_preset', 'target.txt')

        assert config.cluster_filter == r'\s+'
        assert config.text_filter == 'test.*'
        assert config.preset == 'test_preset'
        assert config.target_file == 'target.txt'

    @pytest.mark.unit
    def test_convert_initialized_to_config(self) -> None:
        """Test converting initialized config dict to configuration."""
        manager = PresetConfigurationManager()
        initialized = {
            'cluster_filter': r'\n',
            'text_filter_type': 'Regex-list',
            'text_filter': ['pattern1', 'pattern2'],
            'should_slice_clusters': True,
            'src_start_cluster_text': 'start',
            'src_end_cluster_text': 'end',
            'ref_start_cluster_text': None,
            'ref_end_cluster_text': None
        }

        config = manager._convert_initialized_to_config(initialized)

        assert isinstance(config, RegexListConfiguration)
        assert config.cluster_filter == r'\n'
        assert config.text_filter == ['pattern1', 'pattern2']
        assert config.should_slice_clusters is True
        assert config.src_start_cluster_text == 'start'
        assert config.src_end_cluster_text == 'end'
        assert config.ref_start_cluster_text is None
        assert config.ref_end_cluster_text is None

    @pytest.mark.unit
    def test_convert_initialized_to_config_minimal(self) -> None:
        """Test converting minimal initialized config."""
        manager = PresetConfigurationManager()
        initialized = {
            'cluster_filter': r'\n',
            'text_filter_type': 'Regex',
            'text_filter': 'test.*',
            'should_slice_clusters': False
        }

        config = manager._convert_initialized_to_config(initialized)

        assert isinstance(config, RegexConfiguration)
        assert config.cluster_filter == r'\n'
        assert config.text_filter == 'test.*'
        assert config.should_slice_clusters is False

    @pytest.mark.unit
    def test_convert_initialized_to_config_with_none_values(self) -> None:
        """Test converting config with None values for optional fields."""
        manager = PresetConfigurationManager()
        initialized = {
            'cluster_filter': r'\n',      # Required, not None
            'text_filter_type': 'Regex',  # Required, not None
            'text_filter': 'pattern',     # Required, not None
            'should_slice_clusters': False, # Required, not None
            'src_start_cluster_text': None, # Optional - test None handling
            'src_end_cluster_text': None,   # Optional - test None handling
            'ref_start_cluster_text': None, # Optional - test None handling
            'ref_end_cluster_text': None    # Optional - test None handling
        }

        # This should handle None values gracefully for optional fields
        config = manager._convert_initialized_to_config(initialized)

        # Verify required fields are set
        assert config.cluster_filter == r'\n'
        assert config.text_filter == 'pattern'
        assert config.should_slice_clusters is False

        # Verify optional fields with None values are handled correctly
        assert config.src_start_cluster_text is None
        assert config.src_end_cluster_text is None
        assert config.ref_start_cluster_text is None
        assert config.ref_end_cluster_text is None

    @pytest.mark.unit
    def test_convert_initialized_to_config_missing_fields(self) -> None:
        """Test converting config with missing optional fields."""
        manager = PresetConfigurationManager()
        # Test with only required fields - no optional slicing fields at all
        initialized = {
            'cluster_filter': r'\n',
            'text_filter_type': 'Regex',
            'text_filter': 'pattern',
            'should_slice_clusters': False
        }

        config = manager._convert_initialized_to_config(initialized)

        # All optional fields should default to None when missing
        assert config.src_start_cluster_text is None
        assert config.src_end_cluster_text is None
        assert config.ref_start_cluster_text is None
        assert config.ref_end_cluster_text is None


class TestBatchConfigurationManager:
    """Test BatchConfigurationManager functionality."""

    @pytest.mark.unit
    @patch('GenEC.utils.read_yaml_file')
    @patch('GenEC.core.configuration_manager.BatchConfigurationManager.load_preset')
    def test_create_preset_list_configs(self, mock_load_preset: Mock, mock_read_yaml: Mock) -> None:
        """Test creating configurations from preset list."""
        mock_read_yaml.return_value = {
            'group1': [
                {'preset': 'file/preset1', 'target': 'file1.txt'},
                {'preset': 'file/preset2', 'target': 'file2.txt'}
            ]
        }
        mock_load_preset.return_value = {
            'cluster_filter': r'\n',
            'text_filter_type': 'Regex',
            'text_filter': 'test.*',
            'should_slice_clusters': False
        }

        manager = BatchConfigurationManager()
        configs = manager._create_preset_list_configs('test_list')

        assert len(configs) == 2
        assert configs[0].target_file == 'file1.txt'
        assert configs[0].group == 'group1'
        assert configs[1].target_file == 'file2.txt'
        assert configs[1].group == 'group1'

    @pytest.mark.unit
    @patch('GenEC.utils.read_yaml_file')
    @patch('GenEC.core.configuration_manager.BatchConfigurationManager.load_preset')
    def test_create_preset_list_configs_with_variables(self, mock_load_preset: Mock, mock_read_yaml: Mock) -> None:
        """Test creating configurations with target variables."""
        mock_read_yaml.return_value = {
            'group1': [
                {'preset': 'file/preset1', 'target': '{loc}/{prefix}_1.txt'}
            ]
        }
        mock_load_preset.return_value = {
            'cluster_filter': r'\n',
            'text_filter_type': 'Regex',
            'text_filter': 'test.*',
            'should_slice_clusters': False
        }

        target_variables = {'loc': 'data', 'prefix': 'test'}
        manager = BatchConfigurationManager()
        configs = manager._create_preset_list_configs('test_list', target_variables)

        assert len(configs) == 1
        assert configs[0].target_file == 'data/test_1.txt'

    @pytest.mark.unit
    @patch('GenEC.utils.read_yaml_file')
    @patch('GenEC.core.configuration_manager.BatchConfigurationManager.load_preset')
    @patch('GenEC.core.configuration_manager.console')
    def test_create_preset_list_configs_skip_invalid_preset(self, mock_console: Mock, mock_load_preset: Mock, mock_read_yaml: Mock) -> None:
        """Test skipping invalid presets during configuration creation."""
        mock_read_yaml.return_value = {
            'group1': [
                {'preset': 'file/valid_preset', 'target': 'file1.txt'},
                {'preset': 'file/invalid_preset', 'target': 'file2.txt'}
            ]
        }

        def load_preset_side_effect(preset: str) -> dict[str, Any]:
            if 'invalid' in preset:
                raise ValueError("Invalid preset")
            return {
                'cluster_filter': r'\n',
                'text_filter_type': 'Regex',
                'text_filter': 'test.*',
                'should_slice_clusters': False
            }

        mock_load_preset.side_effect = load_preset_side_effect

        manager = BatchConfigurationManager()
        configs = manager._create_preset_list_configs('test_list')

        assert len(configs) == 1
        assert configs[0].target_file == 'file1.txt'
        mock_console.print.assert_called_once()

    @pytest.mark.unit
    @patch('GenEC.utils.read_yaml_file')
    @patch('GenEC.core.configuration_manager.BatchConfigurationManager.load_preset')
    def test_create_preset_list_configs_no_valid_presets(self, mock_load_preset: Mock, mock_read_yaml: Mock) -> None:
        """Test error when no valid presets are found."""
        mock_read_yaml.return_value = {
            'group1': [
                {'preset': 'file/invalid_preset', 'target': 'file1.txt'}
            ]
        }
        mock_load_preset.side_effect = ValueError("Invalid preset")

        manager = BatchConfigurationManager()

        with pytest.raises(ValueError, match="None of the provided presets were found"):
            manager._create_preset_list_configs('test_list')

    @pytest.mark.unit
    def test_convert_initialized_to_config_with_none_values(self) -> None:
        """Test converting config with None values for optional fields."""
        manager = BatchConfigurationManager()
        initialized = {
            'cluster_filter': r'\n',      # Required, not None
            'text_filter_type': 'Regex',  # Required, not None
            'text_filter': 'pattern',     # Required, not None
            'should_slice_clusters': False, # Required, not None
            'src_start_cluster_text': None, # Optional - test None handling
            'src_end_cluster_text': None,   # Optional - test None handling
            'ref_start_cluster_text': None, # Optional - test None handling
            'ref_end_cluster_text': None    # Optional - test None handling
        }

        # This should handle None values gracefully for optional fields
        config = manager._convert_initialized_to_config(initialized)

        # Verify required fields are set
        assert config.cluster_filter == r'\n'
        assert config.text_filter == 'pattern'
        assert config.should_slice_clusters is False

        # Verify optional fields with None values are handled correctly
        assert config.src_start_cluster_text is None
        assert config.src_end_cluster_text is None
        assert config.ref_start_cluster_text is None
        assert config.ref_end_cluster_text is None

    @pytest.mark.unit
    def test_convert_initialized_to_config_missing_fields(self) -> None:
        """Test converting config with missing optional fields."""
        manager = BatchConfigurationManager()
        # Test with only required fields - no optional slicing fields at all
        initialized = {
            'cluster_filter': r'\n',
            'text_filter_type': 'Regex',
            'text_filter': 'pattern',
            'should_slice_clusters': False
        }

        config = manager._convert_initialized_to_config(initialized)

        # All optional fields should default to None when missing
        assert config.src_start_cluster_text is None
        assert config.src_end_cluster_text is None
        assert config.ref_start_cluster_text is None
        assert config.ref_end_cluster_text is None


class TestConfigurationManagerErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.unit
    @patch('GenEC.utils.read_yaml_file')
    def test_load_preset_file_invalid_format(self, mock_read_yaml: Mock) -> None:
        """Test loading preset file with invalid format."""
        mock_read_yaml.return_value = "not a dict"

        manager = BasicConfigurationManager()

        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(ValueError, match="Invalid preset file format"):
                manager.load_preset_file('invalid_format')

    @pytest.mark.unit
    @patch.object(BasicConfigurationManager, 'load_preset_file')
    def test_load_preset_nonexistent_preset_in_file(self, mock_load_file: Mock) -> None:
        """Test loading nonexistent preset from file."""
        mock_load_file.return_value = {'preset1': {}, 'preset2': {}}

        manager = BasicConfigurationManager()

        with pytest.raises(ValueError, match="Preset 'nonexistent' not found"):
            manager.load_preset('file/nonexistent')

    @pytest.mark.unit
    @patch.object(BasicConfigurationManager, 'load_preset_file')
    @patch.object(BasicConfigurationManager, 'ask_mpc_question')
    def test_load_preset_multiple_presets_user_selection(self, mock_ask_mpc: Mock, mock_load_file: Mock) -> None:
        """Test user selection when multiple presets exist."""
        mock_load_file.return_value = {
            'preset1': {'text_filter': 'pattern1'},
            'preset2': {'text_filter': 'pattern2'}
        }
        mock_ask_mpc.return_value = 'preset2'

        manager = BasicConfigurationManager()
        result = manager.load_preset('multi_preset_file')

        assert result == {'text_filter': 'pattern2'}
        mock_ask_mpc.assert_called_once_with(
            'Multiple presets found in multi_preset_file. Choose one:',
            ['preset1', 'preset2']
        )
