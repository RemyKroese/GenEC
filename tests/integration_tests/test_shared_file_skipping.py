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

            workflow.run()

            print_calls = mock_console.print.call_args_list
            skip_calls = [call for call in print_calls if call[0] and 'source file' in str(call[0][0]) and 'skipping analysis' in str(call[0][0])]
            assert len(skip_calls) == 3
