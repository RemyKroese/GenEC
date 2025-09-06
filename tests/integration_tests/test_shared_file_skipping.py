"""Integration tests for shared file skipping behavior in PresetList workflows."""

import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from GenEC.core.workflows import PresetList
from GenEC.core.configuration_manager import BatchConfigurationManager


@pytest.mark.integration
def test_shared_file_single_skip_message() -> None:
    """Test that files used by multiple presets only show skip message once."""
    assets_dir = Path(__file__).parent.parent / 'system_tests' / 'assets'

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / 'source'
        source_dir.mkdir()

        target_variables = {'loc': 'test_dir', 'prefix': 'missing'}

        workflow = PresetList.__new__(PresetList)
        workflow.source = str(source_dir)
        workflow.reference = None
        workflow.output_directory = None
        workflow.output_types = []

        workflow.configuration_manager = BatchConfigurationManager(
            presets_directory=str(assets_dir / 'input' / 'presets'),
            preset_list='preset_list1',
            target_variables=target_variables
        )
        workflow.configuration_manager.initialize_configuration()

        with patch('GenEC.core.workflows.Console') as mock_console_class:
            mock_console = mock_console_class.return_value
            workflow.console = mock_console

            workflow._get_data(workflow.configuration_manager.configurations)  # pylint: disable=protected-access

            print_calls = mock_console.print.call_args_list
            skip_calls = [call for call in print_calls if call[0] and 'source file' in str(call[0][0]) and 'skipping analysis' in str(call[0][0])]

            assert len(skip_calls) == 4, f"Expected 4 skip messages (one per file) but got {len(skip_calls)}"


@pytest.mark.integration
def test_mixed_file_availability_integration() -> None:
    """Test integration behavior when some target files exist and others don't."""
    assets_dir = Path(__file__).parent.parent / 'system_tests' / 'assets'

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_dir = temp_path / 'source'
        source_dir.mkdir()

        (source_dir / 'test_dir').mkdir()
        (source_dir / 'test_dir' / 'exists_1.txt').write_text('| ITEM1 |\n| ITEM2 |')

        target_variables = {'loc': 'test_dir', 'prefix': 'exists'}

        workflow = PresetList.__new__(PresetList)
        workflow.source = str(source_dir)
        workflow.reference = None
        workflow.output_directory = None
        workflow.output_types = []

        workflow.configuration_manager = BatchConfigurationManager(
            presets_directory=str(assets_dir / 'input' / 'presets'),
            preset_list='preset_list1',
            target_variables=target_variables
        )
        workflow.configuration_manager.initialize_configuration()

        with patch('GenEC.core.workflows.Console') as mock_console_class:
            mock_console = mock_console_class.return_value
            workflow.console = mock_console

            workflow.run()

            print_calls = mock_console.print.call_args_list
            skip_calls = [call for call in print_calls if call[0] and 'source file' in str(call[0][0]) and 'skipping analysis' in str(call[0][0])]
            assert len(skip_calls) == 3


@pytest.mark.integration
def test_subdirectory_preset_list_file_skipping() -> None:
    """Test that preset-list files in subdirectories work correctly with file skipping."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create presets directory structure
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
    target: 'regex_input_1.txt'
  - preset: 'parent_preset/parent_preset'
    target: 'regex_input_2.txt'"""

        (subdir / 'subdirectory_preset_list.yaml').write_text(preset_list_content, encoding='utf-8')

        # Create source directory with one existing file
        source_dir = temp_path / 'source'
        source_dir.mkdir()
        (source_dir / 'regex_input_1.txt').write_text('123\n456\n789', encoding='utf-8')

        workflow = PresetList.__new__(PresetList)
        workflow.source = str(source_dir)
        workflow.reference = None
        workflow.output_directory = None
        workflow.output_types = []

        # Use the subdirectory preset list
        workflow.configuration_manager = BatchConfigurationManager(
            presets_directory=str(presets_dir),
            preset_list='subdir/subdirectory_preset_list'
        )
        workflow.configuration_manager.initialize_configuration()

        with patch('GenEC.core.workflows.Console') as mock_console_class:
            mock_console = mock_console_class.return_value
            workflow.console = mock_console

            # This should work without errors despite missing files
            workflow._get_data(workflow.configuration_manager.configurations)  # pylint: disable=protected-access

            # Verify console output includes both successful processing and skip messages
            print_calls = mock_console.print.call_args_list
            assert len(print_calls) > 0

            # Should have skip messages for missing files
            skip_calls = [call for call in print_calls if call[0] and 'skipping analysis' in str(call[0][0])]
            assert len(skip_calls) >= 1  # At least one file should be missing
