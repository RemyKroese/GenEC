"""Unit tests for GenEC configuration factories."""

from __future__ import annotations

from unittest.mock import Mock, patch
from typing import Any
from pathlib import Path

import pytest

from GenEC.core.configuration_factory import (
    BasicConfigurationFactory, WorkflowConfigurationFactory, PresetConfigurationFactory
)
from GenEC.core.configuration import RegexConfiguration, RegexListConfiguration, PositionalConfiguration
from GenEC.core.specs import PositionalFilterType, TextFilterTypes


class TestBasicConfigurationFactory:
    """Test cases for BasicConfigurationFactory class."""

    def test_build_interactive_regex_filter(self) -> None:
        """Test building regex configuration interactively."""
        config_manager = Mock()
        config_manager.ask_mpc_question.return_value = TextFilterTypes.REGEX.value
        config_manager.ask_open_question.side_effect = [r'\n', 'test_pattern', 'no']

        config = BasicConfigurationFactory.build_interactive(config_manager)

        assert isinstance(config, RegexConfiguration)
        assert config.cluster_filter == r'\n'
        assert config.text_filter == 'test_pattern'
        assert config.should_slice_clusters is False

        # Verify correct prompts were called
        config_manager.ask_mpc_question.assert_called_once()
        assert config_manager.ask_open_question.call_count == 3

    def test_build_interactive_regex_filter_empty_cluster_filter_uses_default(self) -> None:
        """Test that empty cluster filter defaults to newline."""
        config_manager = Mock()
        config_manager.ask_mpc_question.return_value = TextFilterTypes.REGEX.value
        config_manager.ask_open_question.side_effect = ['', 'test_pattern', 'no']

        config = BasicConfigurationFactory.build_interactive(config_manager)

        assert config.cluster_filter == r'\n'  # Default when empty

    def test_build_interactive_regex_list_filter(self) -> None:
        """Test building regex list configuration interactively."""
        config_manager = Mock()
        config_manager.ask_mpc_question.return_value = TextFilterTypes.REGEX_LIST.value
        config_manager.ask_open_question.side_effect = [
            '\\n\\n',  # cluster_filter
            'pattern1',  # first pattern
            'yes',  # continue adding patterns
            'pattern2',  # second pattern
            'no',  # don't continue
            'yes',  # should_slice_clusters
            'src_start',  # src_start_cluster_text
            'src_end',  # src_end_cluster_text
            'ref_start',  # ref_start_cluster_text
            'ref_end'  # ref_end_cluster_text
        ]

        config = BasicConfigurationFactory.build_interactive(config_manager)

        assert isinstance(config, RegexListConfiguration)
        assert config.cluster_filter == '\\n\\n'
        assert config.text_filter == ['pattern1', 'pattern2']
        assert config.should_slice_clusters is True

    def test_build_interactive_regex_list_filter_empty_pattern_stops(self) -> None:
        """Test that empty pattern stops regex list input."""
        config_manager = Mock()
        config_manager.ask_mpc_question.return_value = TextFilterTypes.REGEX_LIST.value
        config_manager.ask_open_question.side_effect = [
            r'\n',  # cluster_filter
            'pattern1',  # first pattern
            'yes',  # continue adding patterns
            '',  # empty pattern - stops input
            'no'  # should_slice_clusters
        ]

        config = BasicConfigurationFactory.build_interactive(config_manager)

        assert config.text_filter == ['pattern1']

    def test_build_interactive_positional_filter(self) -> None:
        """Test building positional configuration interactively."""
        config_manager = Mock()
        config_manager.ask_mpc_question.return_value = TextFilterTypes.POSITIONAL.value
        config_manager.ask_open_question.side_effect = [
            '\\n\\n',  # cluster_filter
            '=',  # separator
            '2',  # line
            '1',  # occurrence
            'yes',  # should_slice_clusters
            'src_start',  # src_start_cluster_text
            'src_end',  # src_end_cluster_text
            'ref_start',  # ref_start_cluster_text
            'ref_end'  # ref_end_cluster_text
        ]

        config = BasicConfigurationFactory.build_interactive(config_manager)

        assert isinstance(config, PositionalConfiguration)
        assert config.cluster_filter == '\\n\\n'
        assert config.text_filter.separator == '='
        assert config.text_filter.line == 2
        assert config.text_filter.occurrence == 1
        assert config.should_slice_clusters is True

    def test_build_interactive_positional_filter_missing_line_raises_error(self) -> None:
        """Test that missing line number raises ValueError."""
        config_manager = Mock()
        config_manager.ask_mpc_question.return_value = TextFilterTypes.POSITIONAL.value
        config_manager.ask_open_question.side_effect = ['\\n\\n', '=', '', '1', 'no']

        with pytest.raises(ValueError, match="Line number is required for positional filter"):
            BasicConfigurationFactory.build_interactive(config_manager)

    def test_build_interactive_positional_filter_missing_occurrence_raises_error(self) -> None:
        """Test that missing occurrence number raises ValueError."""
        config_manager = Mock()
        config_manager.ask_mpc_question.return_value = TextFilterTypes.POSITIONAL.value
        config_manager.ask_open_question.side_effect = ['\\n\\n', '=', '2', '', 'no']

        with pytest.raises(ValueError, match="Occurrence number is required for positional filter"):
            BasicConfigurationFactory.build_interactive(config_manager)

    def test_build_interactive_with_cluster_slicing(self) -> None:
        """Test building configuration with cluster slicing enabled."""
        config_manager = Mock()
        config_manager.ask_mpc_question.return_value = TextFilterTypes.REGEX.value
        config_manager.ask_open_question.side_effect = [
            r'\n',  # cluster_filter
            'test_pattern',  # regex_pattern
            'yes',  # should_slice_clusters
            'src_start',  # src_start_cluster_text
            'src_end',  # src_end_cluster_text
            'ref_start',  # ref_start_cluster_text
            'ref_end'  # ref_end_cluster_text
        ]

        config = BasicConfigurationFactory.build_interactive(config_manager)

        assert config.should_slice_clusters is True
        assert config.src_start_cluster_text == 'src_start'
        assert config.src_end_cluster_text == 'src_end'
        assert config.ref_start_cluster_text == 'ref_start'
        assert config.ref_end_cluster_text == 'ref_end'

    def test_build_interactive_with_cluster_slicing_empty_values_become_none(self) -> None:
        """Test that empty cluster slicing values become None."""
        config_manager = Mock()
        config_manager.ask_mpc_question.return_value = TextFilterTypes.REGEX.value
        config_manager.ask_open_question.side_effect = [
            r'\n',  # cluster_filter
            'test_pattern',  # regex_pattern
            'yes',  # should_slice_clusters
            '',  # empty src_start_cluster_text
            '',  # empty src_end_cluster_text
            '',  # empty ref_start_cluster_text
            ''  # empty ref_end_cluster_text
        ]

        config = BasicConfigurationFactory.build_interactive(config_manager)

        assert config.src_start_cluster_text is None
        assert config.src_end_cluster_text is None
        assert config.ref_start_cluster_text is None
        assert config.ref_end_cluster_text is None


class TestWorkflowConfigurationFactory:
    """Test cases for WorkflowConfigurationFactory class."""

    def test_create_basic_config(self) -> None:
        """Test creating basic workflow configuration."""
        config_manager = Mock()
        expected_config = Mock(spec=RegexConfiguration)

        with patch.object(BasicConfigurationFactory, 'build_interactive', return_value=expected_config):
            result = WorkflowConfigurationFactory.create_basic_config(config_manager)

        assert result is expected_config

    def test_create_preset_config(self) -> None:
        """Test creating preset workflow configuration."""
        config_manager = Mock()
        extraction_config = Mock()
        extraction_config.cluster_filter = r'\n'
        extraction_config.should_slice_clusters = False
        extraction_config.filter_type = TextFilterTypes.REGEX.value
        extraction_config.text_filter = 'test_pattern'
        extraction_config.src_start_cluster_text = None
        extraction_config.src_end_cluster_text = None
        extraction_config.ref_start_cluster_text = None
        extraction_config.ref_end_cluster_text = None

        with patch.object(PresetConfigurationFactory, 'build_from_preset', return_value=extraction_config):
            config = WorkflowConfigurationFactory.create_preset_config(
                config_manager, 'test_preset', 'test_file.txt'
            )

        assert isinstance(config, RegexConfiguration)
        assert config.preset == 'test_preset'
        assert config.target_file == 'test_file.txt'
        assert config.group == ''
        assert config.cluster_filter == r'\n'
        assert config.text_filter == 'test_pattern'

    def test_create_preset_config_with_default_target_file(self) -> None:
        """Test creating preset configuration with default empty target file."""
        config_manager = Mock()
        extraction_config = Mock()
        extraction_config.cluster_filter = r'\n'
        extraction_config.should_slice_clusters = False
        extraction_config.filter_type = TextFilterTypes.REGEX.value
        extraction_config.text_filter = 'test_pattern'
        extraction_config.src_start_cluster_text = None
        extraction_config.src_end_cluster_text = None
        extraction_config.ref_start_cluster_text = None
        extraction_config.ref_end_cluster_text = None

        with patch.object(PresetConfigurationFactory, 'build_from_preset', return_value=extraction_config):
            config = WorkflowConfigurationFactory.create_preset_config(config_manager, 'test_preset')

        assert config.target_file == ''

    @patch('GenEC.utils.read_yaml_file')
    def test_create_preset_list_configs(self, mock_read_yaml: Mock) -> None:
        """Test creating preset list configurations."""
        config_manager = Mock()
        config_manager.presets_directory = Path('/test/presets')
        config_manager.group_presets_by_file.return_value = {
            'file1.txt': [
                {'preset': 'preset_file/preset1', 'group': 'group1'},
                {'preset': 'preset_file/preset2', 'group': 'group2'}
            ],
            'file2.txt': [
                {'preset': 'preset_file/preset3'}  # No group specified
            ]
        }

        mock_read_yaml.return_value = {'preset_list': 'data'}

        extraction_config = Mock()
        extraction_config.cluster_filter = r'\n'
        extraction_config.should_slice_clusters = True
        extraction_config.filter_type = TextFilterTypes.REGEX.value
        extraction_config.text_filter = 'pattern'
        extraction_config.src_start_cluster_text = 'start'
        extraction_config.src_end_cluster_text = 'end'
        extraction_config.ref_start_cluster_text = 'ref_start'
        extraction_config.ref_end_cluster_text = 'ref_end'

        with patch.object(PresetConfigurationFactory, 'build_from_preset', return_value=extraction_config):
            configs = WorkflowConfigurationFactory.create_preset_list_configs(
                config_manager, 'test_presets', {'var1': 'value1'}
            )

        assert len(configs) == 3

        # Check first config
        assert configs[0].preset == 'preset_file/preset1'
        assert configs[0].target_file == 'file1.txt'
        assert configs[0].group == 'group1'

        # Check second config
        assert configs[1].preset == 'preset_file/preset2'
        assert configs[1].target_file == 'file1.txt'
        assert configs[1].group == 'group2'

        # Check third config (no group)
        assert configs[2].preset == 'preset_file/preset3'
        assert configs[2].target_file == 'file2.txt'
        assert configs[2].group == ''

        # Verify YAML file was read
        mock_read_yaml.assert_called_once_with(Path('/test/presets/test_presets.yaml'))

    @patch('GenEC.utils.read_yaml_file')
    def test_create_preset_list_configs_with_preset_error(self, mock_read_yaml: Mock) -> None:
        """Test handling of preset loading errors in preset list."""
        config_manager = Mock()
        config_manager.presets_directory = Path('/test/presets')
        config_manager.group_presets_by_file.return_value = {
            'file1.txt': [
                {'preset': 'good_preset', 'group': 'group1'},
                {'preset': 'bad_preset', 'group': 'group2'}
            ]
        }

        mock_read_yaml.return_value = {'preset_list': 'data'}

        # Mock one successful and one failing preset
        def side_effect(config_mgr: Any, preset: str) -> Any:
            if preset == 'bad_preset':
                raise ValueError('Preset error')
            extraction_config = Mock()
            extraction_config.cluster_filter = r'\n'
            extraction_config.should_slice_clusters = False
            extraction_config.filter_type = TextFilterTypes.REGEX.value
            extraction_config.text_filter = 'pattern'
            extraction_config.src_start_cluster_text = None
            extraction_config.src_end_cluster_text = None
            extraction_config.ref_start_cluster_text = None
            extraction_config.ref_end_cluster_text = None
            return extraction_config

        with patch.object(PresetConfigurationFactory, 'build_from_preset', side_effect=side_effect):
            with patch('GenEC.core.configuration_factory.Console') as mock_console_class:
                mock_console_instance = Mock()
                mock_console_class.return_value = mock_console_instance

                configs = WorkflowConfigurationFactory.create_preset_list_configs(
                    config_manager, 'test_presets'
                )

        # Should only have 1 config (the good one)
        assert len(configs) == 1
        assert configs[0].preset == 'good_preset'

        # Should have printed error message
        mock_console_instance.print.assert_called_once()

    @patch('GenEC.utils.read_yaml_file')
    def test_create_preset_list_configs_no_valid_presets_raises_error(self, mock_read_yaml: Mock) -> None:
        """Test that having no valid presets raises ValueError."""
        config_manager = Mock()
        config_manager.presets_directory = Path('/test/presets')
        config_manager.group_presets_by_file.return_value = {
            'file1.txt': [{'preset': 'bad_preset'}]
        }

        mock_read_yaml.return_value = {'preset_list': 'data'}

        with patch.object(PresetConfigurationFactory, 'build_from_preset', side_effect=ValueError('Error')):
            with patch('GenEC.core.configuration_factory.Console'):
                with pytest.raises(ValueError, match='None of the provided presets were found.'):
                    WorkflowConfigurationFactory.create_preset_list_configs(config_manager, 'test_presets')


class TestPresetConfigurationFactory:
    """Test cases for PresetConfigurationFactory class."""

    def test_build_from_preset(self) -> None:
        """Test building configuration from preset."""
        config_manager = Mock()
        initialized_config = {
            'cluster_filter': r'\n',
            'should_slice_clusters': True,
            'text_filter_type': TextFilterTypes.REGEX.value,
            'text_filter': 'test_pattern',
            'src_start_cluster_text': 'start',
            'src_end_cluster_text': 'end',
            'ref_start_cluster_text': 'ref_start',
            'ref_end_cluster_text': 'ref_end'
        }

        config_manager.load_preset.return_value = initialized_config

        config = PresetConfigurationFactory.build_from_preset(config_manager, 'test_preset')

        assert isinstance(config, RegexConfiguration)
        assert config.cluster_filter == r'\n'
        assert config.should_slice_clusters is True
        assert config.text_filter == 'test_pattern'
        assert config.src_start_cluster_text == 'start'
        assert config.src_end_cluster_text == 'end'
        assert config.ref_start_cluster_text == 'ref_start'
        assert config.ref_end_cluster_text == 'ref_end'

        config_manager.load_preset.assert_called_once_with('test_preset')

    def test_convert_initialized_to_new_config_regex(self) -> None:
        """Test converting initialized config dict to regex configuration."""
        initialized = {
            'cluster_filter': r'\n',
            'should_slice_clusters': False,
            'text_filter_type': TextFilterTypes.REGEX.value,
            'text_filter': 'test_pattern'
        }

        config = PresetConfigurationFactory._convert_initialized_to_new_config(initialized)

        assert isinstance(config, RegexConfiguration)
        assert config.cluster_filter == r'\n'
        assert config.should_slice_clusters is False
        assert config.text_filter == 'test_pattern'

    def test_convert_initialized_to_new_config_regex_list(self) -> None:
        """Test converting initialized config dict to regex list configuration."""
        initialized = {
            'cluster_filter': '\\n\\n',
            'should_slice_clusters': True,
            'text_filter_type': TextFilterTypes.REGEX_LIST.value,
            'text_filter': ['pattern1', 'pattern2']
        }

        config = PresetConfigurationFactory._convert_initialized_to_new_config(initialized)

        assert isinstance(config, RegexListConfiguration)
        assert config.cluster_filter == '\\n\\n'
        assert config.should_slice_clusters is True
        assert config.text_filter == ['pattern1', 'pattern2']

    def test_convert_initialized_to_new_config_positional(self) -> None:
        """Test converting initialized config dict to positional configuration."""
        positional_filter = PositionalFilterType(separator='=', line=2, occurrence=1)
        initialized = {
            'cluster_filter': '\\n\\n',
            'should_slice_clusters': False,
            'text_filter_type': TextFilterTypes.POSITIONAL.value,
            'text_filter': positional_filter
        }

        config = PresetConfigurationFactory._convert_initialized_to_new_config(initialized)

        assert isinstance(config, PositionalConfiguration)
        assert config.cluster_filter == '\\n\\n'
        assert config.should_slice_clusters is False
        assert config.text_filter == positional_filter

    def test_convert_initialized_to_new_config_with_none_values(self) -> None:
        """Test converting config with None values (missing optional fields)."""
        initialized = {
            'cluster_filter': r'\n',
            'should_slice_clusters': False,
            'text_filter_type': TextFilterTypes.REGEX.value,
            'text_filter': 'pattern',
            'src_start_cluster_text': None,
            'src_end_cluster_text': None,
            'ref_start_cluster_text': None,
            'ref_end_cluster_text': None
        }

        config = PresetConfigurationFactory._convert_initialized_to_new_config(initialized)

        assert config.src_start_cluster_text is None
        assert config.src_end_cluster_text is None
        assert config.ref_start_cluster_text is None
        assert config.ref_end_cluster_text is None

    def test_convert_initialized_to_new_config_missing_optional_fields(self) -> None:
        """Test converting config with missing optional fields."""
        initialized = {
            'cluster_filter': r'\n',
            'should_slice_clusters': False,
            'text_filter_type': TextFilterTypes.REGEX.value,
            'text_filter': 'pattern'
            # Optional fields are missing entirely
        }

        config = PresetConfigurationFactory._convert_initialized_to_new_config(initialized)

        assert isinstance(config, RegexConfiguration)
        assert config.cluster_filter == r'\n'
        assert config.text_filter == 'pattern'
        # Missing optional fields should result in None values
        assert config.src_start_cluster_text is None
        assert config.src_end_cluster_text is None
        assert config.ref_start_cluster_text is None
        assert config.ref_end_cluster_text is None

    def test_convert_initialized_to_new_config_partial_optional_fields(self) -> None:
        """Test converting config with some optional fields present."""
        initialized = {
            'cluster_filter': r'\n',
            'should_slice_clusters': True,
            'text_filter_type': TextFilterTypes.REGEX.value,
            'text_filter': 'pattern',
            'src_start_cluster_text': 'start_text',
            'ref_start_cluster_text': 'ref_start_text'
            # src_end_cluster_text and ref_end_cluster_text are missing
        }

        config = PresetConfigurationFactory._convert_initialized_to_new_config(initialized)

        assert config.src_start_cluster_text == 'start_text'
        assert config.ref_start_cluster_text == 'ref_start_text'
        assert config.src_end_cluster_text is None
        assert config.ref_end_cluster_text is None
