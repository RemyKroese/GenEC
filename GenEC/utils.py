from collections import Counter
from typing import Any
import json
import os

from prettytable import PrettyTable  # type: ignore
import yaml

ERROR_WRITING_FILE = 'Error writing file {}: {}'


def get_list_each_element_count(elements: list[str]) -> dict[str, int]:
    return dict(Counter(elements))


def read_files(file_paths: list[str]) -> list[str]:
    files: list[str] = []
    for file in file_paths:
        files.append(read_file(file))
    return files


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
