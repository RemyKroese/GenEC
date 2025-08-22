from __future__ import annotations

from typing import Any
from pathlib import Path
import pytest
from unittest.mock import patch, call, Mock
from rich.console import Console

from GenEC.core.output_manager import OutputManager
from GenEC.core.types.output import Entry, DataExtract, DataCompare

MOCK_RESULTS_COMPARISON: list[Entry] = [
    {'preset': 'preset1', 'target': 'file1.txt', 'data': {'1': DataCompare(source=1, reference=1, difference=0)}},
    {'preset': 'preset2', 'target': 'file2.txt', 'data': {'2': DataCompare(source=1, reference=1, difference=0)}},
    {'preset': 'preset3', 'target': 'file3.txt', 'data': {'3': DataCompare(source=1, reference=1, difference=0)}},
]

MOCK_RESULTS_EXTRACTION: list[Entry] = [
    {'preset': 'preset1', 'target': 'file1.txt', 'data': {'1': DataExtract(source=1)}},
    {'preset': 'preset2', 'target': 'file2.txt', 'data': {'2': DataExtract(source=1)}},
    {'preset': 'preset3', 'target': 'file3.txt', 'data': {'3': DataExtract(source=1)}},
]

MOCK_RESULTS_GROUPED_COMPARISON: dict[str, list[Entry]] = {'group1': MOCK_RESULTS_COMPARISON}
MOCK_RESULTS_GROUPED_EXTRACTION: dict[str, list[Entry]] = {'group1': MOCK_RESULTS_EXTRACTION}

MOCK_ASCII_TABLE: str = 'ASCII_TABLE'
MOCK_OUTPUT_DIRECTORY: Path = Path('directory/path')  # now a Path object
JSON_RESULTS_PATH: Path = MOCK_OUTPUT_DIRECTORY / 'results.json'
TXT_RESULTS_PATH: Path = MOCK_OUTPUT_DIRECTORY / 'results.txt'


@pytest.fixture
def om_instance() -> OutputManager:
    return OutputManager()


@pytest.mark.unit
@pytest.mark.parametrize('mock_results, is_comparison', [
    (MOCK_RESULTS_GROUPED_COMPARISON, True),
    (MOCK_RESULTS_GROUPED_EXTRACTION, False),
])
@pytest.mark.parametrize('output_types', [
    ['txt'],
    ['json'],
    ['yaml', 'csv'],
    ['txt', 'json', 'yaml', 'csv']
])
@patch.object(Console, 'print')
@patch('GenEC.utils.write_output')
def test_process_various_output_types(mock_write_output: Mock, mock_print: Mock, mock_results: dict[str, list[Entry]], is_comparison: bool, output_types: list[str], om_instance: OutputManager) -> None:
    om_instance.output_directory = MOCK_OUTPUT_DIRECTORY
    om_instance.output_types = output_types
    om_instance.should_print_results = True

    patch_target: str = ('GenEC.utils.create_comparison_table'
                    if is_comparison else 'GenEC.utils.create_extraction_table')

    with patch(patch_target, return_value=MOCK_ASCII_TABLE) as mock_create_table:
        om_instance.process(mock_results, root='', is_comparison=is_comparison)

        expected_create_calls: list[Any] = []
        expected_txt_output: list[str] = []
        for entry in mock_results['group1']:
            expected_create_calls.append(call(entry['data'], entry['preset'], entry['target']))

            expected_txt_output.append(MOCK_ASCII_TABLE)

        mock_create_table.assert_has_calls(expected_create_calls, any_order=False)
        assert mock_create_table.call_count == len(expected_create_calls)

        mock_print.call_count == len(expected_create_calls)

        # Build expected_output_path using pathlib to mirror your code logic
        root_path: str = Path('').name  # empty string here
        root_path_without_extension: str = Path(root_path).stem  # also empty string
        expected_output_path: Path = MOCK_OUTPUT_DIRECTORY / root_path_without_extension / 'group1' / 'result'

        mock_write_output.assert_called_once_with(
            mock_results['group1'], expected_txt_output, expected_output_path, output_types
        )


@pytest.mark.unit
@pytest.mark.parametrize('should_print', [True, False])
@patch.object(Console, 'print')
@patch('GenEC.utils.write_output')
def test_process_no_output_directory_no_write(mock_write_output: Mock, mock_print: Mock, should_print: bool, om_instance: OutputManager) -> None:
    om_instance.output_directory = None
    om_instance.output_types = ['txt', 'json']
    om_instance.should_print_results = should_print

    with patch('GenEC.utils.create_extraction_table', return_value=MOCK_ASCII_TABLE) as mock_create_table:
        om_instance.process(MOCK_RESULTS_GROUPED_EXTRACTION, root='')
        assert mock_create_table.call_count == len(MOCK_RESULTS_GROUPED_EXTRACTION['group1'])
        if should_print:
             assert mock_print.call_count == len(MOCK_RESULTS_GROUPED_EXTRACTION['group1'] * 2)  # newline prints double the calls
        else:
            mock_print.assert_not_called()
        mock_write_output.assert_not_called()
