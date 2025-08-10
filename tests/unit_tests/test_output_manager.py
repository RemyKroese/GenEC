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
@patch('builtins.print')
@patch('GenEC.utils.write_to_json_file')
@patch('GenEC.utils.write_to_txt_file')
def test_process_print_only(mock_write_to_txt_file, mock_write_to_json_file, mock_print,
                            mock_results, is_comparison, om_instance):
    patch_target = ('GenEC.utils.create_comparison_ascii_table'
                    if is_comparison else 'GenEC.utils.create_extraction_ascii_table')

    with patch(patch_target, return_value=MOCK_ASCII_TABLE) as mock_create_table:
        om_instance.process(mock_results, root='', is_comparison=is_comparison)

        expected_calls = []
        expected_print = ''
        for entry in mock_results['group1']:
            title = f"{entry['preset']} - {entry['target']}" if entry['target'] else entry['preset']
            expected_calls.append(call(entry['data'], title))
            expected_print += MOCK_ASCII_TABLE + '\n\n'

        mock_create_table.assert_has_calls(expected_calls, any_order=False)
        assert mock_create_table.call_count == len(expected_calls)
        mock_print.assert_called_once_with(expected_print)

        mock_write_to_txt_file.assert_not_called()
        mock_write_to_json_file.assert_not_called()


@pytest.mark.parametrize('mock_results, is_comparison', [
    (MOCK_RESULTS_GROUPED_COMPARISON, True),
    (MOCK_RESULTS_GROUPED_EXTRACTION, False),
])
@patch('builtins.print')
@patch('GenEC.utils.write_to_json_file')
@patch('GenEC.utils.write_to_txt_file')
def test_process_write_only(mock_write_to_txt_file, mock_write_to_json_file, mock_print,
                            mock_results, is_comparison, om_instance):
    om_instance.output_directory = MOCK_OUTPUT_DIRECTORY
    om_instance.should_print_results = False

    patch_target = ('GenEC.utils.create_comparison_ascii_table'
                    if is_comparison else 'GenEC.utils.create_extraction_ascii_table')

    with patch(patch_target, return_value=MOCK_ASCII_TABLE) as mock_create_table:
        om_instance.process(mock_results, root='', is_comparison=is_comparison)

        expected_calls = []
        expected_print = ''
        for entry in mock_results['group1']:
            title = f"{entry['preset']} - {entry['target']}" if entry['target'] else entry['preset']
            expected_calls.append(call(entry['data'], title))
            expected_print += MOCK_ASCII_TABLE + '\n\n'

        mock_create_table.assert_has_calls(expected_calls, any_order=False)
        assert mock_create_table.call_count == len(expected_calls)

        expected_txt_path = os.path.join(MOCK_OUTPUT_DIRECTORY, os.path.basename(os.path.normpath('')), 'group1', 'result.txt')
        expected_json_path = os.path.join(MOCK_OUTPUT_DIRECTORY, os.path.basename(os.path.normpath('')), 'group1', 'result.json')

        mock_write_to_txt_file.assert_called_once_with(expected_print, expected_txt_path)
        mock_write_to_json_file.assert_called_once_with(mock_results['group1'], expected_json_path)

        mock_print.assert_not_called()


@pytest.mark.parametrize('mock_results, is_comparison', [
    (MOCK_RESULTS_GROUPED_COMPARISON, True),
    (MOCK_RESULTS_GROUPED_EXTRACTION, False),
])
@patch('builtins.print')
@patch('GenEC.utils.write_to_json_file')
@patch('GenEC.utils.write_to_txt_file')
def test_process_write_and_print(mock_write_to_txt_file, mock_write_to_json_file, mock_print,
                                 mock_results, is_comparison, om_instance):
    om_instance.output_directory = MOCK_OUTPUT_DIRECTORY
    om_instance.should_print_results = True

    patch_target = ('GenEC.utils.create_comparison_ascii_table'
                    if is_comparison else 'GenEC.utils.create_extraction_ascii_table')

    with patch(patch_target, return_value=MOCK_ASCII_TABLE) as mock_create_table:
        om_instance.process(mock_results, root='', is_comparison=is_comparison)

        expected_calls = []
        expected_print = ''
        for entry in mock_results['group1']:
            title = f"{entry['preset']} - {entry['target']}" if entry['target'] else entry['preset']
            expected_calls.append(call(entry['data'], title))
            expected_print += MOCK_ASCII_TABLE + '\n\n'

        mock_create_table.assert_has_calls(expected_calls, any_order=False)
        assert mock_create_table.call_count == len(expected_calls)

        mock_print.assert_called_once_with(expected_print)

        expected_txt_path = os.path.join(MOCK_OUTPUT_DIRECTORY, os.path.basename(os.path.normpath('')), 'group1', 'result.txt')
        expected_json_path = os.path.join(MOCK_OUTPUT_DIRECTORY, os.path.basename(os.path.normpath('')), 'group1', 'result.json')

        mock_write_to_txt_file.assert_called_once_with(expected_print, expected_txt_path)
        mock_write_to_json_file.assert_called_once_with(mock_results['group1'], expected_json_path)
