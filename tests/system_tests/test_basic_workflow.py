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
    source_file: str = 'file1.txt',
    reference_file: Optional[str] = None,
    extra_cli_args: Optional[list[str]] = None
) -> None:
    if extra_cli_args is None:
        extra_cli_args = []
    if reference_file is None:
        reference_file = source_file
    mock_input.side_effect = input_side_effect

    source_path = ASSETS_DIR / 'input' / source_file
    output_dir = tmp_path / 'output'

    test_args = [
        'main.py', 'basic',
        '--source', str(source_path),
        '--output-directory', str(output_dir),
        '--output-types', *OUTPUT_TYPES,
        *extra_cli_args
    ]

    with patch.object(sys, 'argv', test_args):
        genec_main.main()

    source_name = Path(source_file).stem
    for ext in OUTPUT_TYPES:
        generated_file = output_dir / source_name / f'result.{ext}'
        expected_file = EXPECTED_OUTPUT_DIR / expected_output_subdir / f'result.{ext}'
        assert generated_file.exists(), f'Missing generated file: {generated_file}'
        assert filecmp.cmp(generated_file, expected_file, shallow=False), f"File content mismatch for: {ext}"


@pytest.mark.system
@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_basic_workflow_regex_extract_only(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
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
def test_basic_workflow_regex_extract_and_compare(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
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


@pytest.mark.system
@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_basic_workflow_regex_list_extract_only(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
    input_side_effect = [
        '\\n',                         # cluster split character
        '3',                           # filter type: Regex List
        r'\| [A-Za-z]+ \|',            # first regex pattern
        'yes',                         # add another pattern
        r'([A-Za-z]+)',                # second regex pattern (extraction)
        'no',                          # no more patterns
        ''                             # skip subsection slicing
    ]

    input_side_effect.append('no')

    expected_output_dir = ASSETS_DIR / 'basic_expected_output_regex_list'

    mock_input.side_effect = input_side_effect
    source_path = ASSETS_DIR / 'input' / 'source' / 'input_1.txt'
    output_dir = tmp_path / 'output'

    test_args = [
        'main.py', 'basic',
        '--source', str(source_path),
        '--output-directory', str(output_dir),
        '--output-types', *OUTPUT_TYPES
    ]

    with patch.object(sys, 'argv', test_args):
        genec_main.main()

    source_name = Path('source/input_1.txt').stem  # This gives us 'input_1'
    for ext in OUTPUT_TYPES:
        generated_file = output_dir / source_name / f'result.{ext}'
        expected_file = expected_output_dir / 'extract_only' / f'result.{ext}'
        assert generated_file.exists(), f'Missing generated file: {generated_file}'
        assert filecmp.cmp(generated_file, expected_file, shallow=False), f"File content mismatch for: {ext}"


@pytest.mark.system
@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_basic_workflow_regex_list_extract_and_compare(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
    # Suppress unused parameter warning
    _ = mock_stdout

    input_side_effect = [
        '\\n',                         # cluster split character
        '3',                           # filter type: Regex List
        r'\| [A-Za-z]+ \|',            # first regex pattern
        'yes',                         # add another pattern
        r'([A-Za-z]+)',                # second regex pattern (extraction)
        'no',                          # no more patterns
        ''                             # skip subsection slicing
    ]

    input_side_effect.append('no')

    # Use specific expected output directory for regex-list tests
    expected_output_dir = ASSETS_DIR / 'basic_expected_output_regex_list'

    mock_input.side_effect = input_side_effect
    source_path = ASSETS_DIR / 'input' / 'source' / 'input_1.txt'
    output_dir = tmp_path / 'output'

    test_args = [
        'main.py', 'basic',
        '--source', str(source_path),
        '--output-directory', str(output_dir),
        '--output-types', *OUTPUT_TYPES,
        '--reference', str(ASSETS_DIR / 'input' / 'reference' / 'input_1.txt')
    ]

    with patch.object(sys, 'argv', test_args):
        genec_main.main()

    source_name = Path('source/input_1.txt').stem  # This gives us 'input_1'
    for ext in OUTPUT_TYPES:
        generated_file = output_dir / source_name / f'result.{ext}'
        expected_file = expected_output_dir / 'extract_and_compare' / f'result.{ext}'
        assert generated_file.exists(), f'Missing generated file: {generated_file}'
        assert filecmp.cmp(generated_file, expected_file, shallow=False), f"File content mismatch for: {ext}"
