"""System tests for preset workflow functionality."""
import filecmp
import sys
from io import StringIO
from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch

import pytest

from GenEC import main as genec_main

ASSETS_DIR: Path = Path('tests/system_tests/assets').resolve()
EXPECTED_OUTPUT_DIR: Path = ASSETS_DIR / 'preset_expected_output'
OUTPUT_TYPES = ['txt', 'csv', 'json', 'yaml']


def run_preset_workflow_test(
    mock_input: Mock,
    mock_stdout: StringIO,
    tmp_path: Path,
    input_side_effect: list[str],
    expected_output_subdir: str,
    source_file: str = 'file1.txt',
    extra_cli_args: Optional[list[str]] = None
) -> None:
    if extra_cli_args is None:
        extra_cli_args = []
    mock_input.side_effect = input_side_effect

    source_path = ASSETS_DIR / 'input' / source_file
    output_dir = tmp_path / 'output'
    presets_dir = ASSETS_DIR / 'input' / 'presets'
    preset_path = 'preset_file1/preset_a'

    test_args = [
        'main.py', 'preset',
        '--source', str(source_path),
        '--preset', preset_path,
        '--presets-directory', str(presets_dir),
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
def test_preset_workflow_regex_extract_only(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
    input_side_effect = [
        '\\n',                         # cluster split character
        '1',                           # filter type: Regex
        r'\| ([A-Za-z]+) \|',          # regex filter
        ''                             # skip subsection slicing
    ]

    run_preset_workflow_test(
        mock_input,
        mock_stdout,
        tmp_path,
        input_side_effect,
        expected_output_subdir='extract_only'
    )


@pytest.mark.system
@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_preset_workflow_regex_extract_and_compare(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
    input_side_effect = [
        '\\n',                         # cluster split character
        '1',                           # filter type: Regex
        r'\| ([A-Za-z]+) \|',          # regex filter
        ''                             # skip subsection slicing
    ]

    run_preset_workflow_test(
        mock_input,
        mock_stdout,
        tmp_path,
        input_side_effect,
        expected_output_subdir='extract_and_compare',
        extra_cli_args=['--reference', str(ASSETS_DIR / 'input' / 'file1.txt')]
    )


def run_preset_workflow_regex_list_test(
    tmp_path: Path,
    expected_output_subdir: str,
    preset_name: str,
    source_file: str = 'source/input_1.txt',
    extra_cli_args: Optional[list[str]] = None
) -> None:
    """Run preset workflow test for regex-list filter type."""
    if extra_cli_args is None:
        extra_cli_args = []

    # Use specific expected output directory for regex-list tests
    expected_output_dir = ASSETS_DIR / 'preset_expected_output_regex_list'

    source_path = ASSETS_DIR / 'input' / source_file
    output_dir = tmp_path / 'output'
    presets_dir = ASSETS_DIR / 'input' / 'presets'
    preset_path = f'regex_list_preset/{preset_name}'

    test_args = [
        'main.py', 'preset',
        '--source', str(source_path),
        '--preset', preset_path,
        '--presets-directory', str(presets_dir),
        '--output-directory', str(output_dir),
        '--output-types', *OUTPUT_TYPES,
        *extra_cli_args
    ]

    with patch.object(sys, 'argv', test_args):
        genec_main.main()

    source_name = Path(source_file).stem
    for ext in OUTPUT_TYPES:
        generated_file = output_dir / source_name / f'result.{ext}'
        expected_file = expected_output_dir / expected_output_subdir / f'result.{ext}'
        assert generated_file.exists(), f'Missing generated file: {generated_file}'
        assert filecmp.cmp(generated_file, expected_file, shallow=False), f"File content mismatch for: {ext}"


@pytest.mark.system
def test_preset_workflow_regex_list_extract_only(tmp_path: Path) -> None:
    run_preset_workflow_regex_list_test(
        tmp_path,
        expected_output_subdir='extract_only',
        preset_name='regex_list_extract_only'
    )


@pytest.mark.system
def test_preset_workflow_regex_list_extract_and_compare(tmp_path: Path) -> None:
    run_preset_workflow_regex_list_test(
        tmp_path,
        expected_output_subdir='extract_and_compare',
        preset_name='regex_list_extract_only',
        extra_cli_args=['--reference', str(ASSETS_DIR / 'input' / 'reference' / 'input_1.txt')]
    )
