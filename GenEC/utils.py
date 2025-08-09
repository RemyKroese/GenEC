from collections import Counter
from typing import Any
import json
import os

from prettytable import PrettyTable  # type: ignore
import yaml
from GenEC.core import AnalysisConstruct

ERROR_WRITING_FILE = 'Error writing file {}: {}'


def get_list_each_element_count(elements: list[str]) -> dict[str, int]:
    return dict(Counter(elements))


def read_files(base_path: str, analysis_constructs: list[AnalysisConstruct]) -> dict[str, str]:
    """
    Reads all unique files referenced by analysis_constructs, using base_path as the root.
    Returns a dict mapping target_file to file contents.
    """
    unique_files: set[str] = set(ac.target_file for ac in analysis_constructs)
    file_data: dict[str, str] = {}
    for target_file in unique_files:
        if target_file == '':
            file_path = base_path
        else:
            file_path = os.path.join(os.path.dirname(base_path), target_file)
        file_data[target_file] = read_file(file_path)
    return file_data


def read_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'File {file_path} not found.')
    with open(file_path, 'r', encoding='utf-8') as data:
        return data.read()


def read_yaml_file(file_path: str):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'File {file_path} not found.')
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def create_extraction_ascii_table(data: dict[str, dict[str, int]]) -> str:
    table: Any = PrettyTable()
    table.title = 'GenEC results'
    table.field_names = ['Data', 'Source count']
    table.align = 'l'

    for key in data:
        table.add_row([key, data[key]['source']])

    return table.get_string(sortby='Source count', reversesort=True)


def create_comparison_ascii_table(data: dict[str, dict[str, int]]) -> str:
    table: Any = PrettyTable()
    table.title = 'GenEC results'
    table.field_names = ['Data', 'Source count', 'Reference count', 'Difference']
    table.align = 'l'

    for key in data:
        table.add_row([key, data[key]['source'], data[key]['reference'], data[key]['difference']])

    return table.get_string(sortby='Difference', reversesort=True)


def write_to_txt_file(data: str, file_path: str) -> None:
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(data)
    except OSError as err:
        print(ERROR_WRITING_FILE.format(file_path, err))


def write_to_json_file(data: dict[str, dict[str, int]], file_path: str) -> None:
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
    except OSError as err:
        print(ERROR_WRITING_FILE.format(file_path, err))
