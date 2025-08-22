"""System tests for preset list workflow functionality."""
import filecmp
import sys
from io import StringIO
from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch

import pytest

from GenEC import main as genec_main

ASSETS_DIR: Path = Path('tests/system_tests/assets').resolve()
REGEX_EXPECTED_OUTPUT_DIR: Path = ASSETS_DIR / 'preset_list_expected_output'
REGEX_LIST_EXPECTED_OUTPUT_DIR: Path = ASSETS_DIR / 'preset_list_expected_output_regex_list'
OUTPUT_TYPES = ['txt', 'csv', 'json', 'yaml']
TARGET_VARIABLES_REGEX = ['loc=input', 'prefix=file']
TARGET_VARIABLES_REGEX_LIST = ['prefix=input']

def run_preset_list_test(
    mock_input: Mock,
    mock_stdout: StringIO,
    output_dir: Path,
    expected_output_directory: Path,
    input_folder_name: str = 'assets',
    input_side_effect: list[str] = [],
    extra_cli_args: Optional[list[str]] = None,
    preset_list_name: str = 'preset_list1',
    source_dir: Path = ASSETS_DIR,
    presets_dir: Path = ASSETS_DIR / 'input' / 'presets'
) -> None:
    if extra_cli_args is None:
        extra_cli_args = []
    mock_input.side_effect = input_side_effect

    test_args = [
        'main.py', 'preset-list',
        '--source', str(source_dir),
        '--preset-list', preset_list_name,
        '--presets-directory', str(presets_dir),
        '--output-directory', str(output_dir),
        '--output-types', *OUTPUT_TYPES,
        *extra_cli_args
    ]

    with patch.object(sys, 'argv', test_args):
        genec_main.main()

    for group in ['group_1', 'group_2']:
        for ext in OUTPUT_TYPES:
            generated_file = output_dir / input_folder_name / group / f'result.{ext}'
            expected_file = expected_output_directory / group / f'result.{ext}'
            assert generated_file.exists(), f'Missing generated file: {generated_file}'
            assert filecmp.cmp(generated_file, expected_file, shallow=False), f"File content mismatch for: {group} {ext}"


@pytest.mark.system
@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_preset_list_regex_extract_only(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
    input_side_effect = [
        '\\n',                         # cluster split character
        '1',                           # filter type: Regex
        r'\| ([A-Za-z]+) \|',          # regex filter
        ''                             # skip subsection slicing
    ]

    run_preset_list_test(
        mock_input,
        mock_stdout,
        output_dir = tmp_path / 'output',
        input_side_effect=input_side_effect,
        expected_output_directory= REGEX_EXPECTED_OUTPUT_DIR / 'extract_only' / 'assets',
        extra_cli_args=['--target-variables', *TARGET_VARIABLES_REGEX]
    )


@pytest.mark.system
@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_preset_list_regex_extract_and_compare(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
    input_side_effect = [
        '\\n',                         # cluster split character
        '1',                           # filter type: Regex
        r'\| ([A-Za-z]+) \|',          # regex filter
        ''                             # skip subsection slicing
    ]

    run_preset_list_test(
        mock_input,
        mock_stdout,
        output_dir = tmp_path / 'output',
        input_side_effect=input_side_effect,
        expected_output_directory= REGEX_EXPECTED_OUTPUT_DIR / 'extract_and_compare' / 'assets',
        extra_cli_args=['--reference', str(ASSETS_DIR),
                        '--target-variables', *TARGET_VARIABLES_REGEX]
    )


@pytest.mark.system
@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_preset_list_regex_list_extract_only(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
    """Test preset list workflow with regex-list filtering for extraction only."""

    run_preset_list_test(
        mock_input,
        mock_stdout,
        output_dir = tmp_path / 'output',
        input_folder_name = 'source',
        source_dir= ASSETS_DIR / 'input' / 'source',
        expected_output_directory=REGEX_LIST_EXPECTED_OUTPUT_DIR / 'extract_only' / 'source',
        extra_cli_args=['--target-variables', *TARGET_VARIABLES_REGEX_LIST],
        preset_list_name='preset_list_regex_list',
    )


@pytest.mark.system
@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_preset_list_regex_list_extract_and_compare(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
    """Test preset list workflow with regex-list filtering for extraction and comparison."""

    run_preset_list_test(
        mock_input,
        mock_stdout,
        output_dir = tmp_path / 'output',
        input_folder_name = 'source',
        source_dir= ASSETS_DIR / 'input' / 'source',
        expected_output_directory = REGEX_LIST_EXPECTED_OUTPUT_DIR / 'extract_and_compare' / 'source',
        extra_cli_args=['--reference', str(ASSETS_DIR / 'input' / 'reference'), '--target-variables', *TARGET_VARIABLES_REGEX_LIST],
        preset_list_name='preset_list_regex_list',
    )
