import os
import pytest
from unittest.mock import patch

from GenEC.core.manage_io import OutputManager

MOCK_RESULTS = {
    '1': {'source': 1, 'reference': 1, 'difference': 0},
    '2': {'source': 1, 'reference': 1, 'difference': 0},
    '3': {'source': 1, 'reference': 1, 'difference': 0}
}

MOCK_ASCII_TABLE = 'ASCII_TABLE'
MOCK_OUTPUT_DIRECTORY = 'directory/path'
JSON_RESULTS_PATH = os.path.join(MOCK_OUTPUT_DIRECTORY, 'results.json')
TXT_RESULTS_PATH = os.path.join(MOCK_OUTPUT_DIRECTORY, 'results.txt')


@pytest.fixture
def om_instance():
    return OutputManager()


@patch('builtins.print')
@patch('GenEC.core.manage_io.utils.write_to_json_file')
@patch('GenEC.core.manage_io.utils.write_to_txt_file')
@patch('GenEC.core.manage_io.utils.create_ascii_table', return_value=MOCK_ASCII_TABLE)
def test_process_print_only(mock_create_ascii_table, mock_write_to_txt_file, mock_write_to_json_file, mock_print, om_instance):
    om_instance.process(MOCK_RESULTS)

    mock_create_ascii_table.assert_called_once_with(MOCK_RESULTS)
    mock_print.assert_called_once_with(MOCK_ASCII_TABLE)

    mock_write_to_txt_file.assert_not_called()
    mock_write_to_json_file.assert_not_called()


@patch('builtins.print')
@patch('GenEC.core.manage_io.utils.write_to_json_file')
@patch('GenEC.core.manage_io.utils.write_to_txt_file')
@patch('GenEC.core.manage_io.utils.create_ascii_table', return_value=MOCK_ASCII_TABLE)
def test_process_write_only(mock_create_ascii_table, mock_write_to_txt_file, mock_write_to_json_file, mock_print, om_instance):
    om_instance.output_directory = MOCK_OUTPUT_DIRECTORY
    om_instance.should_print_results = False
    om_instance.process(MOCK_RESULTS)

    mock_create_ascii_table.assert_called_once_with(MOCK_RESULTS)
    mock_write_to_txt_file.assert_called_once_with(MOCK_ASCII_TABLE, TXT_RESULTS_PATH)
    mock_write_to_json_file.assert_called_once_with(MOCK_RESULTS, JSON_RESULTS_PATH)

    mock_print.assert_not_called()


@patch('builtins.print')
@patch('GenEC.core.manage_io.utils.write_to_json_file')
@patch('GenEC.core.manage_io.utils.write_to_txt_file')
@patch('GenEC.core.manage_io.utils.create_ascii_table', return_value=MOCK_ASCII_TABLE)
def test_process_write_and_print(mock_create_ascii_table, mock_write_to_txt_file, mock_write_to_json_file, mock_print, om_instance):
    om_instance.output_directory = MOCK_OUTPUT_DIRECTORY
    om_instance.process(MOCK_RESULTS)

    mock_create_ascii_table.assert_called_once_with(MOCK_RESULTS)
    mock_print.assert_called_once_with(MOCK_ASCII_TABLE)
    mock_write_to_txt_file.assert_called_once_with(MOCK_ASCII_TABLE, TXT_RESULTS_PATH)
    mock_write_to_json_file.assert_called_once_with(MOCK_RESULTS, JSON_RESULTS_PATH)
