"""System tests for preset list workflow functionality."""
import filecmp
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from GenEC import main as genec_main

ASSETS_DIR: Path = Path('tests/system_tests/assets').resolve()
OUTPUT_TYPES = ['txt', 'csv', 'json', 'yaml']

def run_preset_list_test(
    tmp_path: Path,
    preset_list_name: str,
    expected_output_subdir: str,
    expected_output_base: Path,
    extra_cli_args: list[str],
    source_dir: Path = ASSETS_DIR,
    input_folder_name: str = 'assets'
) -> None:
    """Run preset list workflow test with optimized parameters."""
    output_dir = tmp_path / 'output'
    presets_dir = ASSETS_DIR / 'input' / 'presets'

    expected_output_directory = expected_output_base / expected_output_subdir / input_folder_name

    # Build CLI arguments
    cli_args = [
        'main.py', 'preset-list',
        '--source', str(source_dir),
        '--preset-list', preset_list_name,
        '--presets-directory', str(presets_dir),
        '--output-directory', str(output_dir),
        '--output-types', *OUTPUT_TYPES,
        *extra_cli_args
    ]

    with patch.object(sys, 'argv', cli_args):
        genec_main.main()

    # Verify results
    for group in ['group_1', 'group_2']:
        for ext in OUTPUT_TYPES:
            generated_file = output_dir / input_folder_name / group / f'result.{ext}'
            expected_file = expected_output_directory / group / f'result.{ext}'
            assert generated_file.exists(), f'Missing generated file: {generated_file}'
            assert filecmp.cmp(generated_file, expected_file, shallow=False), f"File content mismatch for: {group} {ext}"


@pytest.mark.system
def test_preset_list_regex_extract_only(tmp_path: Path) -> None:
    """Test preset list workflow with regex filtering for extraction only."""
    run_preset_list_test(
        tmp_path=tmp_path,
        preset_list_name='preset_list1',
        expected_output_subdir='extract_only',
        expected_output_base=ASSETS_DIR / 'preset_list_expected_output_regex',
        extra_cli_args=['--target-variables', 'loc=input', 'prefix=regex_input']
    )


@pytest.mark.system
def test_preset_list_regex_extract_and_compare(tmp_path: Path) -> None:
    """Test preset list workflow with regex filtering for extraction and comparison."""
    run_preset_list_test(
        tmp_path=tmp_path,
        preset_list_name='preset_list1',
        expected_output_subdir='extract_and_compare',
        expected_output_base=ASSETS_DIR / 'preset_list_expected_output_regex',
        extra_cli_args=['--reference', str(ASSETS_DIR), '--target-variables', 'loc=input', 'prefix=regex_input']
    )


@pytest.mark.system
def test_preset_list_regex_list_extract_only(tmp_path: Path) -> None:
    """Test preset list workflow with regex-list filtering for extraction only."""
    run_preset_list_test(
        tmp_path=tmp_path,
        preset_list_name='preset_list_regex_list',
        expected_output_subdir='extract_only',
        expected_output_base=ASSETS_DIR / 'preset_list_expected_output_regex_list',
        extra_cli_args=['--target-variables', 'prefix=regex_list_input'],
        source_dir=ASSETS_DIR / 'input' / 'source',
        input_folder_name='source'
    )


@pytest.mark.system
def test_preset_list_regex_list_extract_and_compare(tmp_path: Path) -> None:
    """Test preset list workflow with regex-list filtering for extraction and comparison."""
    run_preset_list_test(
        tmp_path=tmp_path,
        preset_list_name='preset_list_regex_list',
        expected_output_subdir='extract_and_compare',
        expected_output_base=ASSETS_DIR / 'preset_list_expected_output_regex_list',
        extra_cli_args=['--reference', str(ASSETS_DIR / 'input' / 'reference'), '--target-variables', 'prefix=regex_list_input'],
        source_dir=ASSETS_DIR / 'input' / 'source',
        input_folder_name='source'
    )
