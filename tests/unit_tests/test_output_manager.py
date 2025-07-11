import os
import pytest
from unittest.mock import patch

from GenEC.core.manage_io import OutputManager

MOCK_RESULTS_COMPARISON = {
    '1': {'source': 1, 'reference': 1, 'difference': 0},
    '2': {'source': 1, 'reference': 1, 'difference': 0},
    '3': {'source': 1, 'reference': 1, 'difference': 0}
}

MOCK_RESULTS_EXTRACTION = {
    '1': {'count': 1},
    '2': {'count': 1},
    '3': {'count': 1}
}

MOCK_ASCII_TABLE = 'ASCII_TABLE'
MOCK_OUTPUT_DIRECTORY = 'directory/path'
JSON_RESULTS_PATH = os.path.join(MOCK_OUTPUT_DIRECTORY, 'results.json')
TXT_RESULTS_PATH = os.path.join(MOCK_OUTPUT_DIRECTORY, 'results.txt')


@pytest.fixture
def om_instance():
    return OutputManager()


@pytest.mark.parametrize('mock_results, is_comparison', [
    (MOCK_RESULTS_COMPARISON, True),
    (MOCK_RESULTS_EXTRACTION, False),
])
@patch('builtins.print')
@patch('GenEC.utils.write_to_json_file')
@patch('GenEC.utils.write_to_txt_file')
def test_process_print_only(mock_write_to_txt_file, mock_write_to_json_file, mock_print,
                            mock_results, is_comparison, om_instance):
    patch_target = ('GenEC.utils.create_comparison_ascii_table'
                    if is_comparison else 'GenEC.utils.create_extraction_ascii_table')

    with patch(patch_target, return_value=MOCK_ASCII_TABLE) as mock_create_table:
        om_instance.process(mock_results, is_comparison=is_comparison)

        mock_create_table.assert_called_once_with(mock_results)
        mock_print.assert_called_once_with(MOCK_ASCII_TABLE)

        mock_write_to_txt_file.assert_not_called()
        mock_write_to_json_file.assert_not_called()


@pytest.mark.parametrize('mock_results, is_comparison', [
    (MOCK_RESULTS_COMPARISON, True),
    (MOCK_RESULTS_EXTRACTION, False),
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
        om_instance.process(mock_results, is_comparison=is_comparison)

        mock_create_table.assert_called_once_with(mock_results)
        mock_write_to_txt_file.assert_called_once_with(MOCK_ASCII_TABLE, TXT_RESULTS_PATH)
        mock_write_to_json_file.assert_called_once_with(mock_results, JSON_RESULTS_PATH)

        mock_print.assert_not_called()


@pytest.mark.parametrize('mock_results, is_comparison', [
    (MOCK_RESULTS_COMPARISON, True),
    (MOCK_RESULTS_EXTRACTION, False),
])
@patch('builtins.print')
@patch('GenEC.utils.write_to_json_file')
@patch('GenEC.utils.write_to_txt_file')
def test_process_write_and_print(mock_write_to_txt_file, mock_write_to_json_file, mock_print,
                                 mock_results, is_comparison, om_instance):
    om_instance.output_directory = MOCK_OUTPUT_DIRECTORY

    patch_target = ('GenEC.utils.create_comparison_ascii_table'
                    if is_comparison else 'GenEC.utils.create_extraction_ascii_table')

    with patch(patch_target, return_value=MOCK_ASCII_TABLE) as mock_create_table:
        om_instance.process(mock_results, is_comparison=is_comparison)

        mock_create_table.assert_called_once_with(mock_results)
        mock_print.assert_called_once_with(MOCK_ASCII_TABLE)
        mock_write_to_txt_file.assert_called_once_with(MOCK_ASCII_TABLE, TXT_RESULTS_PATH)
        mock_write_to_json_file.assert_called_once_with(mock_results, JSON_RESULTS_PATH)
