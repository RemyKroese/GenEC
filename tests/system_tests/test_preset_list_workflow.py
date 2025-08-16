import filecmp
from io import StringIO
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

from GenEC import main as genec_main

ASSETS_DIR: Path = Path('tests/system_tests/assets').resolve()
EXPECTED_OUTPUT_DIR: Path = ASSETS_DIR / 'preset_list_expected_output'
OUTPUT_TYPES = ['txt', 'csv', 'json', 'yaml']
TARGET_VARIABLES = ['loc=input', 'prefix=file']

def run_preset_list_test(
    mock_input: Mock,
    mock_stdout: StringIO,
    tmp_path: Path,
    input_side_effect: list[str],
    expected_output_table: str,
    expected_output_subdir: str,
    extra_cli_args: list[str] = []
) -> None:
    mock_input.side_effect = input_side_effect

    source_dir = ASSETS_DIR  # note source is a directory here
    presets_dir = ASSETS_DIR / 'input' / 'presets'
    output_dir = tmp_path / 'output'
    preset_list_name = 'preset_list1'

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

    assert expected_output_table in mock_stdout.getvalue()

    for group in ['group_1', 'group_2']:
        for ext in OUTPUT_TYPES:
            generated_file = output_dir / 'assets' / group / f'result.{ext}'
            expected_file = EXPECTED_OUTPUT_DIR / expected_output_subdir / 'assets' / group / f'result.{ext}'
            assert generated_file.exists(), f'Missing generated file: {generated_file}'
            assert filecmp.cmp(generated_file, expected_file, shallow=False), f"File content mismatch for: {group} {ext}"


@pytest.mark.system
@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_preset_list_extract_only(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
    input_side_effect = [
        '\\n',                         # cluster split character
        '1',                           # filter type: Regex
        r'\| ([A-Za-z]+) \|',          # regex filter
        ''                             # skip subsection slicing
    ]
    expected_table = (
        '+-----------------------------------------+\n'
        '| preset_file1/preset_a - input/file1.txt |\n'
        '+---------------+-------------------------+\n'
        '| Data          | Source count            |\n'
        '+---------------+-------------------------+\n'
        '| INFO          | 1174                    |\n'
        '| WARNING       | 322                     |\n'
        '| ERROR         | 157                     |\n'
        '+---------------+-------------------------+\n'
        '\n'
        '+-----------------------------------------+\n'
        '| preset_file1/preset_a - input/file3.txt |\n'
        '+---------------+-------------------------+\n'
        '| Data          | Source count            |\n'
        '+---------------+-------------------------+\n'
        '| INFO          | 1174                    |\n'
        '| WARNING       | 322                     |\n'
        '| ERROR         | 157                     |\n'
        '+---------------+-------------------------+\n'
        '\n\n'
        '+-----------------------------------------+\n'
        '| preset_file1/preset_b - input/file2.txt |\n'
        '+-------------------+---------------------+\n'
        '| Data              | Source count        |\n'
        '+-------------------+---------------------+\n'
        '| SYNC              | 80                  |\n'
        '| SHUTDOWN          | 77                  |\n'
        '| RESTART           | 73                  |\n'
        '| CALIBRATION       | 69                  |\n'
        '| BOOT              | 69                  |\n'
        '+-------------------+---------------------+\n'
        '\n'
        '+-----------------------------------------+\n'
        '| preset_file1/preset_b - input/file4.txt |\n'
        '+-------------------+---------------------+\n'
        '| Data              | Source count        |\n'
        '+-------------------+---------------------+\n'
        '| SYNC              | 80                  |\n'
        '| SHUTDOWN          | 77                  |\n'
        '| RESTART           | 73                  |\n'
        '| CALIBRATION       | 69                  |\n'
        '| BOOT              | 69                  |\n'
        '+-------------------+---------------------+\n'
    )
    run_preset_list_test(
        mock_input,
        mock_stdout,
        tmp_path,
        input_side_effect,
        expected_table,
        expected_output_subdir='extract_only',
        extra_cli_args=['--target-variables', *TARGET_VARIABLES]
    )


@pytest.mark.system
@patch('sys.stdout', new_callable=StringIO)
@patch('builtins.input')
def test_preset_list_extract_and_compare(mock_input: Mock, mock_stdout: StringIO, tmp_path: Path) -> None:
    input_side_effect = [
        '\\n',                         # cluster split character
        '1',                           # filter type: Regex
        r'\| ([A-Za-z]+) \|',          # regex filter
        ''                             # skip subsection slicing
    ]
    expected_table = (
        '+-------------------------------------------------------+\n'
        '|        preset_file1/preset_a - input/file1.txt        |\n'
        '+---------+--------------+-----------------+------------+\n'
        '| Data    | Source count | Reference count | Difference |\n'
        '+---------+--------------+-----------------+------------+\n'
        '| WARNING | 322          | 322             | 0          |\n'
        '| INFO    | 1174         | 1174            | 0          |\n'
        '| ERROR   | 157          | 157             | 0          |\n'
        '+---------+--------------+-----------------+------------+\n'
        '\n'
        '+-------------------------------------------------------+\n'
        '|        preset_file1/preset_a - input/file3.txt        |\n'
        '+---------+--------------+-----------------+------------+\n'
        '| Data    | Source count | Reference count | Difference |\n'
        '+---------+--------------+-----------------+------------+\n'
        '| WARNING | 322          | 322             | 0          |\n'
        '| INFO    | 1174         | 1174            | 0          |\n'
        '| ERROR   | 157          | 157             | 0          |\n'
        '+---------+--------------+-----------------+------------+\n'
        '\n\n'
        '+-----------------------------------------------------------+\n'
        '|          preset_file1/preset_b - input/file2.txt          |\n'
        '+-------------+--------------+-----------------+------------+\n'
        '| Data        | Source count | Reference count | Difference |\n'
        '+-------------+--------------+-----------------+------------+\n'
        '| SYNC        | 80           | 80              | 0          |\n'
        '| SHUTDOWN    | 77           | 77              | 0          |\n'
        '| RESTART     | 73           | 73              | 0          |\n'
        '| CALIBRATION | 69           | 69              | 0          |\n'
        '| BOOT        | 69           | 69              | 0          |\n'
        '+-------------+--------------+-----------------+------------+\n'
        '\n'
        '+-----------------------------------------------------------+\n'
        '|          preset_file1/preset_b - input/file4.txt          |\n'
        '+-------------+--------------+-----------------+------------+\n'
        '| Data        | Source count | Reference count | Difference |\n'
        '+-------------+--------------+-----------------+------------+\n'
        '| SYNC        | 80           | 80              | 0          |\n'
        '| SHUTDOWN    | 77           | 77              | 0          |\n'
        '| RESTART     | 73           | 73              | 0          |\n'
        '| CALIBRATION | 69           | 69              | 0          |\n'
        '| BOOT        | 69           | 69              | 0          |\n'
        '+-------------+--------------+-----------------+------------+\n'
    )
    run_preset_list_test(
        mock_input,
        mock_stdout,
        tmp_path,
        input_side_effect,
        expected_table,
        expected_output_subdir='extract_and_compare',
        extra_cli_args=['--reference', str(ASSETS_DIR),
                        '--target-variables', *TARGET_VARIABLES]
    )
