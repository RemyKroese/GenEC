from collections import Counter
from typing import Any, Callable, Dict, Set, TypeVar, TYPE_CHECKING
import csv
import json
from pathlib import Path
import yaml

from prettytable import PrettyTable  # type: ignore

if TYPE_CHECKING:  # pragma: no cover
    from GenEC.core.config_manager import Configuration
    from GenEC.core.types.output import DataCompare, DataExtract, Entry


ERROR_WRITING_FILE = 'Error writing file {}: {}'


def get_list_each_element_count(elements: list[str]) -> dict[str, int]:
    return dict(Counter(elements))


def read_files(base_path: str, configurations: list['Configuration']) -> dict[str, str]:
    '''
    Reads all unique files referenced by configurations, using base_path as the root.
    Returns a dict mapping target_file to file contents.
    '''
    path = Path(base_path)  # convert to Path once
    unique_files: set[str] = set(c.target_file for c in configurations)
    file_data: dict[str, str] = {}
    for target_file in unique_files:
        if target_file == '':
            file_path = path
        else:
            file_path = path / target_file  # pathlib join with /
        file_data[target_file] = read_file(file_path)
    return file_data


def read_file(file_path: str | Path) -> str:
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f'File {file_path} not found.')
    with file_path.open('r', encoding='utf-8') as data:
        return data.read()


def read_yaml_file(file_path: str | Path):
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f'File {file_path} not found.')
    with file_path.open('r') as file:
        return yaml.safe_load(file)


def create_extraction_ascii_table(data: dict[str, 'DataExtract'], title: str = 'GenEC results') -> str:
    table: Any = PrettyTable()
    table.title = title
    table.field_names = ['Data', 'Source count']
    table.align = 'l'

    for key in data:
        table.add_row([key, data[key]['source']])

    return table.get_string(sortby='Source count', reversesort=True)


def create_comparison_ascii_table(data: dict[str, 'DataCompare'], title: str = 'GenEC results') -> str:
    table: Any = PrettyTable()
    table.title = title
    table.field_names = ['Data', 'Source count', 'Reference count', 'Difference']
    table.align = 'l'

    for key in data:
        table.add_row([key, data[key]['source'], data[key]['reference'], data[key]['difference']])

    return table.get_string(sortby='Difference', reversesort=True)


F = TypeVar('F', bound=Callable[..., None])
_writer_registry: Dict[str, Callable[..., None]] = {}


def sort_entry_data_keys(entry: 'Entry') -> 'Entry':
    data = entry.get('data', {})
    sorted_data = dict(sorted(data.items()))  # sort keys alphabetically
    new_entry = entry.copy()
    new_entry['data'] = sorted_data
    return new_entry


def register_writer(name: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        _writer_registry[name] = func
        return func
    return decorator


def get_writer(name: str):
    try:
        return _writer_registry[name]
    except KeyError:  # pragma: no cover
        raise ValueError(f'Writer [{name}] is not registered.')


@register_writer('json')
def write_json(data: list['Entry'], file_path: str | Path) -> None:
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        data_processed = [sort_entry_data_keys(e) for e in data]
        with file_path.open('w', encoding='utf-8') as file:
            json.dump(data_processed, file, indent=4)
    except OSError as err:  # pragma: no cover
        print(ERROR_WRITING_FILE.format(file_path, err))


@register_writer('yaml')
def write_yaml(data: list['Entry'], file_path: str | Path) -> None:
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        data_processed = [sort_entry_data_keys(e) for e in data]
        with file_path.open('w', encoding='utf-8') as file:
            yaml.dump(data_processed, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except OSError as err:  # pragma: no cover
        print(ERROR_WRITING_FILE.format(file_path, err))


@register_writer('csv')
def write_csv(data: list['Entry'], file_path: str | Path) -> None:
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        all_columns: Set[str] = set()
        rows: list[dict[str, Any]] = []
        for entry in data:
            for data_key, values in entry.get('data', {}).items():
                row: dict[str, Any] = {**entry, 'data': data_key, **values}
                rows.append(row)
                all_columns.update(row.keys())

        rows.sort(key=lambda r: r['data'])

        with file_path.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted(all_columns))
            writer.writeheader()
            writer.writerows(rows)
    except OSError as err:
        print(ERROR_WRITING_FILE.format(file_path, err))


@register_writer('txt')
def write_txt(data: str, file_path: str | Path) -> None:
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('w', encoding='utf-8') as file:
            file.write(data)
    except OSError as err:
        print(ERROR_WRITING_FILE.format(file_path, err))


def write_output(data: list['Entry'], ascii_tables: str, file_path: str, output_types: list[str]):
    for output_type in output_types:
        writer = get_writer(output_type)
        if output_type == 'txt':
            writer(ascii_tables, f"{file_path}.{output_type}")
        else:
            writer(data, f"{file_path}.{output_type}")
