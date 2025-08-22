"""System tests for basic workflow functionality."""
import filecmp
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from GenEC import main as genec_main

ASSETS_DIR: Path = Path('tests/system_tests/assets').resolve()
OUTPUT_TYPES = ['txt', 'csv', 'json', 'yaml']


def run_basic_workflow_test(
    tmp_path: Path,
    input_side_effect: list[str],
    expected_output_subdir: str,
    expected_output_base: Path,
    source_file: Path,
    extra_cli_args: list[str]
) -> None:
    """Run basic workflow test with optimized parameters."""
    output_dir = tmp_path / 'output'
    expected_output_directory = expected_output_base / expected_output_subdir

    # Build CLI arguments
    cli_args = [
        'main.py', 'basic',
        '--source', str(source_file),
        '--output-directory', str(output_dir),
        '--output-types', *OUTPUT_TYPES,
        *extra_cli_args
    ]

    with patch('builtins.input') as mock_input:
        mock_input.side_effect = input_side_effect
        with patch.object(sys, 'argv', cli_args):
            genec_main.main()

    # Verify results
    source_name = source_file.stem
    for ext in OUTPUT_TYPES:
        generated_file = output_dir / source_name / f'result.{ext}'
        expected_file = expected_output_directory / f'result.{ext}'
        assert generated_file.exists(), f'Missing generated file: {generated_file}'
        assert filecmp.cmp(generated_file, expected_file, shallow=False), f"File content mismatch for: {ext}"


@pytest.mark.system
def test_basic_workflow_regex_extract_only(tmp_path: Path) -> None:
    """Test basic workflow with regex filtering for extraction only."""
    input_side_effect = [
        '\n',                         # cluster split character
        '1',                           # filter type: Regex
        r'\| ([A-Za-z]+) \|',          # regex filter
        ''                             # skip subsection slicing
    ]
    input_side_effect.append('no')

    run_basic_workflow_test(
        tmp_path=tmp_path,
        input_side_effect=input_side_effect,
        expected_output_subdir='extract_only',
        expected_output_base=ASSETS_DIR / 'basic_expected_output_regex',
        source_file=ASSETS_DIR / 'input' / 'source' / 'regex_input_1.txt',
        extra_cli_args=[]
    )


@pytest.mark.system
def test_basic_workflow_regex_extract_and_compare(tmp_path: Path) -> None:
    """Test basic workflow with regex filtering for extraction and comparison."""
    input_side_effect = [
        '\n',                         # cluster split character
        '1',                           # filter type: Regex
        r'\| ([A-Za-z]+) \|',          # regex filter
        ''                             # skip subsection slicing
    ]
    input_side_effect.append('no')

    run_basic_workflow_test(
        tmp_path=tmp_path,
        input_side_effect=input_side_effect,
        expected_output_subdir='extract_and_compare',
        expected_output_base=ASSETS_DIR / 'basic_expected_output_regex',
        source_file=ASSETS_DIR / 'input' / 'source' / 'regex_input_1.txt',
        extra_cli_args=['--reference', str(ASSETS_DIR / 'input' / 'source' / 'regex_input_1.txt')]
    )


@pytest.mark.system
def test_basic_workflow_regex_list_extract_only(tmp_path: Path) -> None:
    """Test basic workflow with regex-list filtering for extraction only."""
    input_side_effect = [
        '\n',                         # cluster split character
        '3',                           # filter type: Regex List
        r'\| [A-Za-z]+ \|',            # first regex pattern
        'yes',                         # add another pattern
        r'([A-Za-z]+)',                # second regex pattern (extraction)
        'no',                          # no more patterns
        ''                             # skip subsection slicing
    ]
    input_side_effect.append('no')

    run_basic_workflow_test(
        tmp_path=tmp_path,
        input_side_effect=input_side_effect,
        expected_output_subdir='extract_only',
        expected_output_base=ASSETS_DIR / 'basic_expected_output_regex_list',
        source_file=ASSETS_DIR / 'input' / 'source' / 'regex_list_input_1.txt',
        extra_cli_args=[]
    )


@pytest.mark.system
def test_basic_workflow_regex_list_extract_and_compare(tmp_path: Path) -> None:
    """Test basic workflow with regex-list filtering for extraction and comparison."""
    input_side_effect = [
        '\n',                         # cluster split character
        '3',                           # filter type: Regex List
        r'\| [A-Za-z]+ \|',            # first regex pattern
        'yes',                         # add another pattern
        r'([A-Za-z]+)',                # second regex pattern (extraction)
        'no',                          # no more patterns
        ''                             # skip subsection slicing
    ]
    input_side_effect.append('no')

    run_basic_workflow_test(
        tmp_path=tmp_path,
        input_side_effect=input_side_effect,
        expected_output_subdir='extract_and_compare',
        expected_output_base=ASSETS_DIR / 'basic_expected_output_regex_list',
        source_file=ASSETS_DIR / 'input' / 'source' / 'regex_list_input_1.txt',
        extra_cli_args=['--reference', str(ASSETS_DIR / 'input' / 'reference' / 'regex_list_input_1.txt')]
    )


@pytest.mark.system
def test_basic_workflow_positional_extract_only(tmp_path: Path) -> None:
    """Test basic workflow with positional filtering for extraction only."""
    input_side_effect = [
        '\n\n',     # cluster split character (paragraphs)
        '2',          # filter type: Positional
        ': ',          # separator for splitting
        '3',          # line number
        '2',          # occurrence number
        ''            # skip subsection slicing
    ]
    input_side_effect.append('no')

    run_basic_workflow_test(
        tmp_path=tmp_path,
        input_side_effect=input_side_effect,
        expected_output_subdir='extract_only',
        expected_output_base=ASSETS_DIR / 'basic_expected_output_positional',
        source_file=ASSETS_DIR / 'input' / 'source' / 'positional_input_1.txt',
        extra_cli_args=[]
    )


@pytest.mark.system
def test_basic_workflow_positional_extract_and_compare(tmp_path: Path) -> None:
    """Test basic workflow with positional filtering for extraction and comparison."""
    input_side_effect = [
        '\n\n',     # cluster split character (paragraphs)
        '2',          # filter type: Positional
        ': ',          # separator for splitting
        '3',          # line number
        '2',          # occurrence number
        ''            # skip subsection slicing
    ]
    input_side_effect.append('no')

    run_basic_workflow_test(
        tmp_path=tmp_path,
        input_side_effect=input_side_effect,
        expected_output_subdir='extract_and_compare',
        expected_output_base=ASSETS_DIR / 'basic_expected_output_positional',
        source_file=ASSETS_DIR / 'input' / 'source' / 'positional_input_1.txt',
        extra_cli_args=['--reference', str(ASSETS_DIR / 'input' / 'reference' / 'positional_input_1.txt')]
    )
