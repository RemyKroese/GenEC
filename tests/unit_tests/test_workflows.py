"""Unit tests for workflows module."""

from unittest.mock import Mock, patch
from pathlib import Path

from GenEC.core.workflows import PresetList
from GenEC.core.configuration import BaseConfiguration


class TestPresetList:
    """Unit tests for PresetList workflow."""

    @patch('GenEC.core.workflows.utils.read_file')
    def test_get_data_skips_missing_files(self, mock_read_file: Mock) -> None:
        """Test that _get_data skips missing target files without crashing."""
        def read_file_side_effect(file_path: Path) -> str:
            if 'missing_file.txt' in str(file_path):
                raise FileNotFoundError(f'File {file_path} not found.')
            return 'file content'

        mock_read_file.side_effect = read_file_side_effect

        workflow = PresetList.__new__(PresetList)
        workflow.source = 'source_dir'
        workflow.reference = 'ref_dir'

        config1 = Mock(spec=BaseConfiguration)
        config1.target_file = 'existing_file.txt'
        config2 = Mock(spec=BaseConfiguration)
        config2.target_file = 'missing_file.txt'
        config3 = Mock(spec=BaseConfiguration)
        config3.target_file = 'another_existing.txt'

        configs = [config1, config2, config3]

        source_data, ref_data = workflow._get_data(configs)  # type: ignore  # pylint: disable=protected-access

        assert 'existing_file.txt' in source_data
        assert 'another_existing.txt' in source_data
        assert 'missing_file.txt' not in source_data
        assert source_data['existing_file.txt'] == 'file content'
        assert source_data['another_existing.txt'] == 'file content'

        assert ref_data is not None
        assert 'existing_file.txt' in ref_data
        assert 'another_existing.txt' in ref_data
        assert 'missing_file.txt' not in ref_data

    @patch('GenEC.core.workflows.utils.read_file')
    def test_get_data_no_reference(self, mock_read_file: Mock) -> None:
        """Test that _get_data works correctly when reference is None."""
        mock_read_file.return_value = 'file content'

        workflow = PresetList.__new__(PresetList)
        workflow.source = 'source_dir'
        workflow.reference = None

        config = Mock(spec=BaseConfiguration)
        config.target_file = 'test_file.txt'
        configs = [config]

        source_data, ref_data = workflow._get_data(configs)  # type: ignore  # pylint: disable=protected-access

        assert 'test_file.txt' in source_data
        assert ref_data is None

    @patch('GenEC.core.workflows.Console')
    @patch('GenEC.core.workflows.utils.read_file')
    def test_get_data_prints_skip_message(self, mock_read_file: Mock, mock_console_class: Mock) -> None:
        """Test that _get_data prints skip message for missing files."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        mock_read_file.side_effect = FileNotFoundError('File not found.')

        workflow = PresetList.__new__(PresetList)
        workflow.source = 'source_dir'
        workflow.reference = None

        config = Mock(spec=BaseConfiguration)
        config.target_file = 'missing_file.txt'
        configs = [config]

        source_data, ref_data = workflow._get_data(configs)  # type: ignore  # pylint: disable=protected-access

        mock_console.print.assert_called()
        call_args = mock_console.print.call_args[0][0]
        assert 'source file' in call_args and 'skipping analysis' in call_args
        assert 'missing_file.txt' in call_args

        assert 'missing_file.txt' not in source_data
        assert ref_data is None

    @patch('GenEC.core.workflows.utils.read_file')
    def test_get_data_skips_reference_when_source_missing(self, mock_read_file: Mock) -> None:
        """Test that reference files are not read when source files are missing."""
        call_log = []

        def read_file_side_effect(file_path: Path) -> str:
            call_log.append(str(file_path))
            if 'source_dir' in str(file_path) and 'missing_file.txt' in str(file_path):
                raise FileNotFoundError(f'Source file {file_path} not found.')
            return 'file content'

        mock_read_file.side_effect = read_file_side_effect

        workflow = PresetList.__new__(PresetList)
        workflow.source = 'source_dir'
        workflow.reference = 'ref_dir'

        config = Mock(spec=BaseConfiguration)
        config.target_file = 'missing_file.txt'
        configs = [config]

        source_data, ref_data = workflow._get_data(configs)  # type: ignore  # pylint: disable=protected-access

        source_calls = [call for call in call_log if 'source_dir' in call]
        assert len(source_calls) == 1

        ref_calls = [call for call in call_log if 'ref_dir' in call]
        assert len(ref_calls) == 0

        assert 'missing_file.txt' not in source_data
        assert ref_data is not None
        assert 'missing_file.txt' not in ref_data

    @patch('GenEC.core.workflows.Console')
    @patch('GenEC.core.workflows.utils.read_file')
    def test_distinct_skip_messages(self, mock_read_file: Mock, mock_console_class: Mock) -> None:
        """Test that distinct messages are shown for source vs reference file missing."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        def read_file_side_effect(file_path: Path) -> str:
            if 'source_dir' in str(file_path) and 'source_missing.txt' in str(file_path):
                raise FileNotFoundError(f'Source file {file_path} not found.')
            if 'ref_dir' in str(file_path) and 'ref_missing.txt' in str(file_path):
                raise FileNotFoundError(f'Reference file {file_path} not found.')
            return 'file content'

        mock_read_file.side_effect = read_file_side_effect

        workflow = PresetList.__new__(PresetList)
        workflow.source = 'source_dir'
        workflow.reference = 'ref_dir'

        config1 = Mock(spec=BaseConfiguration)
        config1.target_file = 'source_missing.txt'

        config2 = Mock(spec=BaseConfiguration)
        config2.target_file = 'ref_missing.txt'

        configs = [config1, config2]

        source_data, ref_data = workflow._get_data(configs)  # type: ignore  # pylint: disable=protected-access

        assert mock_console.print.call_count == 2

        call_messages = [call[0][0] for call in mock_console.print.call_args_list]

        source_missing_messages = [msg for msg in call_messages if 'source file' in msg and 'skipping analysis' in msg]
        reference_missing_messages = [msg for msg in call_messages if 'reference file' in msg and 'skipping comparison' in msg]

        assert len(source_missing_messages) == 1
        assert len(reference_missing_messages) == 1
        assert 'source_missing.txt' in source_missing_messages[0]
        assert 'ref_missing.txt' in reference_missing_messages[0]

        assert 'source_missing.txt' not in source_data
        assert 'ref_missing.txt' in source_data
        assert ref_data is not None
        assert 'ref_missing.txt' not in ref_data
