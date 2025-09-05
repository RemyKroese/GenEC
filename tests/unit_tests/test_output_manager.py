"""Unit tests for GenEC OutputManager class."""
from __future__ import annotations

from typing import Any
from pathlib import Path
from unittest.mock import patch, call, Mock
import pytest
from rich.console import Console

from GenEC.core.output_manager import OutputManager
from GenEC.core.specs import ConfigOptions
from GenEC.core.types.output import Entry, DataExtract, DataCompare

MOCK_RESULTS_COMPARISON: list[Entry] = [
    {'preset': 'preset1', 'target': 'file1.txt', 'data': {
        '1': DataCompare(source=1, reference=1, difference=0)}},
    {'preset': 'preset2', 'target': 'file2.txt', 'data': {
        '2': DataCompare(source=1, reference=1, difference=0)}},
    {'preset': 'preset3', 'target': 'file3.txt', 'data': {
        '3': DataCompare(source=1, reference=1, difference=0)}},
]

MOCK_RESULTS_EXTRACTION: list[Entry] = [
    {'preset': 'preset1', 'target': 'file1.txt',
        'data': {'1': DataExtract(source=1)}},
    {'preset': 'preset2', 'target': 'file2.txt',
        'data': {'2': DataExtract(source=1)}},
    {'preset': 'preset3', 'target': 'file3.txt',
        'data': {'3': DataExtract(source=1)}},
]

MOCK_RESULTS_GROUPED_COMPARISON: dict[str, list[Entry]] = {
    'group1': MOCK_RESULTS_COMPARISON}
MOCK_RESULTS_GROUPED_EXTRACTION: dict[str, list[Entry]] = {
    'group1': MOCK_RESULTS_EXTRACTION}

MOCK_ASCII_TABLE: str = 'ASCII_TABLE'
MOCK_OUTPUT_DIRECTORY: Path = Path('directory/path')
JSON_RESULTS_PATH: Path = MOCK_OUTPUT_DIRECTORY / 'results.json'
TXT_RESULTS_PATH: Path = MOCK_OUTPUT_DIRECTORY / 'results.txt'


@pytest.fixture
def om_instance() -> OutputManager:
    return OutputManager()


@pytest.mark.unit
@pytest.mark.parametrize('mock_results', [
    MOCK_RESULTS_GROUPED_COMPARISON,
    MOCK_RESULTS_GROUPED_EXTRACTION,
])
@pytest.mark.parametrize('output_types', [
    ['txt'],
    ['json'],
    ['yaml', 'csv'],
    ['txt', 'json', 'yaml', 'csv']
])
@patch.object(Console, 'print')
@patch('GenEC.utils.write_output')
def test_process_various_output_types(mock_write_output: Mock, mock_print: Mock,
                                      mock_results: dict[str, list[Entry]],
                                      output_types: list[str], om_instance: OutputManager) -> None:
    om_instance.output_directory = MOCK_OUTPUT_DIRECTORY
    om_instance.output_types = output_types
    om_instance.should_print_results = True

    first_entry = next(iter(mock_results.values()))[0]
    first_data_item = next(iter(first_entry['data'].values()))
    is_comparison = 'reference' in first_data_item and 'difference' in first_data_item

    patch_target: str = ('GenEC.utils.create_comparison_table'
                         if is_comparison else 'GenEC.utils.create_extraction_table')

    with patch(patch_target, return_value=MOCK_ASCII_TABLE) as mock_create_table:
        om_instance.process(mock_results, root='')

        expected_create_calls: list[Any] = []
        expected_txt_output: list[str] = []
        for entry in mock_results['group1']:
            expected_create_calls.append(
                call(
                    entry['data'],
                    entry[ConfigOptions.PRESET.value],
                    entry['target']))

            expected_txt_output.append(MOCK_ASCII_TABLE)

        mock_create_table.assert_has_calls(
            expected_create_calls, any_order=False)
        assert mock_create_table.call_count == len(expected_create_calls)

        assert mock_print.call_count == len(expected_create_calls) * 2

        root_path: str = Path('').name
        root_path_without_extension: str = Path(root_path).stem
        expected_output_path: Path = MOCK_OUTPUT_DIRECTORY / root_path_without_extension / 'group1' / 'result'

        mock_write_output.assert_called_once_with(
            mock_results['group1'], expected_txt_output, expected_output_path, output_types
        )


@pytest.mark.unit
@pytest.mark.parametrize('should_print', [True, False])
@patch.object(Console, 'print')
@patch('GenEC.utils.write_output')
def test_process_no_output_directory_no_write(
        mock_write_output: Mock, mock_print: Mock, should_print: bool, om_instance: OutputManager) -> None:
    om_instance.output_directory = None
    om_instance.output_types = ['txt', 'json']
    om_instance.should_print_results = should_print

    with patch('GenEC.utils.create_extraction_table', return_value=MOCK_ASCII_TABLE) as mock_create_table:
        om_instance.process(MOCK_RESULTS_GROUPED_EXTRACTION, root='')
        assert mock_create_table.call_count == len(
            MOCK_RESULTS_GROUPED_EXTRACTION['group1'])
        if should_print:
            assert mock_print.call_count == len(
                MOCK_RESULTS_GROUPED_EXTRACTION['group1']) * 2
        else:
            mock_print.assert_not_called()
        mock_write_output.assert_not_called()


@pytest.mark.unit
def test_create_table_for_entry_mixed_scenarios(om_instance: OutputManager) -> None:
    """Test table creation for mixed comparison and extraction entries."""
    comparison_entry: Entry = {
        'preset': 'test_preset',
        'target': 'test.txt',
        'data': {
            'item1': DataCompare(source=1, reference=2, difference=1),
            'item2': DataCompare(source=3, reference=4, difference=1)
        }
    }

    extraction_entry: Entry = {
        'preset': 'test_preset',
        'target': 'test2.txt',
        'data': {
            'item1': DataExtract(source=10),
            'item2': DataExtract(source=20)
        }
    }

    with patch('GenEC.utils.create_comparison_table') as mock_comp_table, \
         patch('GenEC.utils.create_extraction_table') as mock_ext_table:

        mock_comp_table.return_value = Mock()
        mock_ext_table.return_value = Mock()

        om_instance._create_table_for_entry(comparison_entry)  # pylint: disable=protected-access

        mock_comp_table.assert_called_once_with(
            comparison_entry['data'],
            comparison_entry['preset'],
            comparison_entry['target']
        )

        mock_comp_table.reset_mock()
        mock_ext_table.reset_mock()

        om_instance._create_table_for_entry(extraction_entry)  # pylint: disable=protected-access

        mock_ext_table.assert_called_once_with(
            extraction_entry['data'],
            extraction_entry['preset'],
            extraction_entry['target']
        )


@pytest.mark.unit
def test_process_handles_mixed_entry_types(om_instance: OutputManager) -> None:
    """Test process method with mixed comparison and extraction entries."""
    mixed_entries: dict[str, list[Entry]] = {
        'mixed_group': [
            {
                'preset': 'preset1',
                'target': 'comp_file.txt',
                'data': {
                    'item1': DataCompare(source=1, reference=2, difference=1)
                }
            },
            {
                'preset': 'preset2',
                'target': 'ext_file.txt',
                'data': {
                    'item1': DataExtract(source=100)
                }
            }
        ]
    }

    om_instance.should_print_results = True
    om_instance.output_directory = None

    with patch('GenEC.utils.create_comparison_table', return_value=Mock()) as mock_comp, \
         patch('GenEC.utils.create_extraction_table', return_value=Mock()) as mock_ext, \
         patch('GenEC.core.output_manager.console.print') as mock_print:

        om_instance.process(mixed_entries, root='')

        mock_comp.assert_called_once()
        mock_ext.assert_called_once()

        assert mock_print.call_count == 4
