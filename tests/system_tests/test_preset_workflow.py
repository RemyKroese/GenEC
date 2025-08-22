"""System tests for preset workflow functionality."""

import filecmp
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from GenEC import main as genec_main

ASSETS_DIR: Path = Path('tests/system_tests/assets').resolve()
OUTPUT_TYPES = ['txt', 'csv', 'json', 'yaml']


def run_preset_workflow_test(
    tmp_path: Path,
    expected_output_subdir: str,
    preset_name: str,
    preset_file: str,
    expected_output_base: Path,
    source_file: Path,
    extra_cli_args: list[str]
) -> None:
    """Run preset workflow test for all filter types."""
    output_dir = tmp_path / 'output'
    presets_dir = ASSETS_DIR / 'input' / 'presets'
    preset_path = f'{preset_file}/{preset_name}'
    expected_output_directory = expected_output_base / expected_output_subdir

    # Build CLI arguments
    cli_args = [
        'main.py', 'preset',
        '--source', str(source_file),
        '--preset', preset_path,
        '--presets-directory', str(presets_dir),
        '--output-directory', str(output_dir),
        '--output-types', *OUTPUT_TYPES,
        *extra_cli_args
    ]

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
def test_preset_regex_extract_only(tmp_path: Path) -> None:
    """Test preset workflow with regex extractor, extract only."""
    run_preset_workflow_test(
        tmp_path=tmp_path,
        expected_output_subdir='extract_only',
        preset_name='preset_a',
        preset_file='preset_file1',
        expected_output_base=ASSETS_DIR / 'preset_expected_output_regex',
        source_file=ASSETS_DIR / 'input' / 'source' / 'regex_input_1.txt',
        extra_cli_args=[]
    )


@pytest.mark.system
def test_preset_regex_extract_and_compare(tmp_path: Path) -> None:
    """Test preset workflow with regex extractor, extract and compare."""
    run_preset_workflow_test(
        tmp_path=tmp_path,
        expected_output_subdir='extract_and_compare',
        preset_name='preset_a',
        preset_file='preset_file1',
        expected_output_base=ASSETS_DIR / 'preset_expected_output_regex',
        source_file=ASSETS_DIR / 'input' / 'source' / 'regex_input_1.txt',
        extra_cli_args=['--reference', str(ASSETS_DIR / 'input' / 'source' / 'regex_input_1.txt')]
    )


@pytest.mark.system
def test_preset_regex_list_extract_only(tmp_path: Path) -> None:
    """Test preset workflow with regex-list extractor, extract only."""
    run_preset_workflow_test(
        tmp_path=tmp_path,
        expected_output_subdir='extract_only',
        preset_name='regex_list_extract_only',
        preset_file='regex_list_preset',
        expected_output_base=ASSETS_DIR / 'preset_expected_output_regex_list',
        source_file=ASSETS_DIR / 'input' / 'source' / 'regex_list_input_1.txt',
        extra_cli_args=[]
    )


@pytest.mark.system
def test_preset_regex_list_extract_and_compare(tmp_path: Path) -> None:
    """Test preset workflow with regex-list extractor, extract and compare."""
    run_preset_workflow_test(
        tmp_path=tmp_path,
        expected_output_subdir='extract_and_compare',
        preset_name='regex_list_extract_only',
        preset_file='regex_list_preset',
        expected_output_base=ASSETS_DIR / 'preset_expected_output_regex_list',
        source_file=ASSETS_DIR / 'input' / 'source' / 'regex_list_input_1.txt',
        extra_cli_args=['--reference', str(ASSETS_DIR / 'input' / 'reference' / 'regex_list_input_1.txt')]
    )
