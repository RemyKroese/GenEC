"""System tests for basic workflow functionality."""
import filecmp
import sys
from io import StringIO
from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch

import pytest

from GenEC import main as genec_main

ASSETS_DIR: Path = Path('tests/system_tests/assets').resolve()
EXPECTED_OUTPUT_DIR: Path = ASSETS_DIR / 'basic_expected_output'
OUTPUT_TYPES = ['txt', 'csv', 'json', 'yaml']


def run_basic_workflow_test(
    mock_input: Mock,
    mock_stdout: StringIO,
    tmp_path: Path,
    input_side_effect: list[str],
    expected_output_subdir: str,
    extra_cli_args: Optional[list[str]] = None
) -> None:
    if extra_cli_args is None:
        extra_cli_args = []
    mock_input.side_effect = input_side_effect

    source_file = ASSETS_DIR / 'input' / 'file1.txt'
    output_dir = tmp_path / 'output'

    test_args = [
        'main.py', 'basic',
        '--source', str(source_file),
        '--output-directory', str(output_dir),
        '--output-types', *OUTPUT_TYPES,
        *extra_cli_args
    ]

    with patch.object(sys, 'argv', test_args):
        genec_main.main()

    for ext in OUTPUT_TYPES:
        generated_file = output_dir / 'file1' / f'result.{ext}'
        expected_file = EXPECTED_OUTPUT_DIR / expected_output_subdir / f'result.{ext}'
        assert generated_file.exists(), f'Missing generated file: {generated_file}'
        assert filecmp.cmp(generated_file, expected_file, shallow=False), f"File content mismatch for: {ext}"


@pytest.mark.system
@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_basic_workflow_extract_only(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
    input_side_effect = [
        '\\n',                         # cluster split character
        '1',                           # filter type: Regex
        r'\| ([A-Za-z]+) \|',          # regex filter
        ''                             # skip subsection slicing
    ]

    input_side_effect.append('no')

    run_basic_workflow_test(
        mock_input,
        mock_stdout,
        tmp_path,
        input_side_effect,
        expected_output_subdir='extract_only'
    )


@pytest.mark.system
@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_basic_workflow_extract_and_compare(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
    input_side_effect = [
        '\\n',                         # cluster split character
        '1',                           # filter type: Regex
        r'\| ([A-Za-z]+) \|',          # regex filter
        ''                             # skip subsection slicing
    ]

    input_side_effect.append('no')

    run_basic_workflow_test(
        mock_input,
        mock_stdout,
        tmp_path,
        input_side_effect,
        expected_output_subdir='extract_and_compare',
        extra_cli_args=['--reference', str(ASSETS_DIR / 'input' / 'file1.txt')]
    )
