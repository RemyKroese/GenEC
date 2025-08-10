import os
import pytest
from unittest.mock import patch, call

from GenEC.core.manage_io import OutputManager

MOCK_RESULTS_COMPARISON = [
    {'preset': 'preset1', 'target': 'file1.txt', 'data': {'1': {'source': 1, 'reference': 1, 'difference': 0}}},
    {'preset': 'preset2', 'target': 'file2.txt', 'data': {'2': {'source': 1, 'reference': 1, 'difference': 0}}},
    {'preset': 'preset3', 'target': 'file3.txt', 'data': {'3': {'source': 1, 'reference': 1, 'difference': 0}}},
]

MOCK_RESULTS_EXTRACTION = [
    {'preset': 'preset1', 'target': 'file1.txt', 'data': {'1': {'count': 1}}},
    {'preset': 'preset2', 'target': 'file2.txt', 'data': {'2': {'count': 1}}},
    {'preset': 'preset3', 'target': 'file3.txt', 'data': {'3': {'count': 1}}},
]

MOCK_RESULTS_GROUPED_COMPARISON = {'group1': MOCK_RESULTS_COMPARISON}
MOCK_RESULTS_GROUPED_EXTRACTION = {'group1': MOCK_RESULTS_EXTRACTION}

MOCK_ASCII_TABLE = 'ASCII_TABLE'
MOCK_OUTPUT_DIRECTORY = 'directory/path'
JSON_RESULTS_PATH = os.path.join(MOCK_OUTPUT_DIRECTORY, 'results.json')
TXT_RESULTS_PATH = os.path.join(MOCK_OUTPUT_DIRECTORY, 'results.txt')


@pytest.fixture
def om_instance():
    return OutputManager()


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
@patch('builtins.print')
@patch('GenEC.utils.write_output')
def test_process_various_output_types(mock_write_output, mock_print, mock_results, is_comparison, output_types, om_instance):
    om_instance.output_directory = MOCK_OUTPUT_DIRECTORY
    om_instance.output_types = output_types
    om_instance.should_print_results = True

    patch_target = ('GenEC.utils.create_comparison_ascii_table'
                    if is_comparison else 'GenEC.utils.create_extraction_ascii_table')

    with patch(patch_target, return_value=MOCK_ASCII_TABLE) as mock_create_table:
        om_instance.process(mock_results, root='', is_comparison=is_comparison)

        # Build expected calls to create_table
        expected_create_calls = []
        expected_print_str = ''
        for entry in mock_results['group1']:
            title = entry['preset']
            if entry['target']:
                title += f" - {entry['target']}"
            expected_create_calls.append(call(entry['data'], title))
            expected_print_str += MOCK_ASCII_TABLE + '\n\n'

        mock_create_table.assert_has_calls(expected_create_calls, any_order=False)
        assert mock_create_table.call_count == len(expected_create_calls)

        # Assert print is called once with full ascii tables string
        mock_print.assert_called_once_with(expected_print_str)

        # Assert write_output called with entries, ascii_tables string, output_path, and output_types
        expected_output_path = os.path.join(
            MOCK_OUTPUT_DIRECTORY,
            os.path.splitext(os.path.basename(os.path.normpath('')))[0],
            'group1',
            'result'
        )
        mock_write_output.assert_called_once_with(
            mock_results['group1'], expected_print_str, expected_output_path, output_types
        )


@pytest.mark.parametrize('should_print', [True, False])
@patch('builtins.print')
@patch('GenEC.utils.write_output')
def test_process_no_output_directory_no_write(mock_write_output, mock_print, should_print, om_instance):
    om_instance.output_directory = None
    om_instance.output_types = ['txt', 'json']
    om_instance.should_print_results = should_print

    with patch('GenEC.utils.create_extraction_ascii_table', return_value=MOCK_ASCII_TABLE) as mock_create_table:
        om_instance.process(MOCK_RESULTS_GROUPED_EXTRACTION, root='')
        assert mock_create_table.call_count == len(MOCK_RESULTS_GROUPED_EXTRACTION['group1'])
        if should_print:
            mock_print.assert_called_once()
        else:
            mock_print.assert_not_called()
        mock_write_output.assert_not_called()
