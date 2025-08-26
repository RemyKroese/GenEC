"""Utilities for file reading, data extraction, comparison, and writing outputs in multiple formats."""

from collections import Counter
from datetime import datetime
from typing import Any, Callable, Optional, Set, TypeVar, TYPE_CHECKING
import csv
import json
from pathlib import Path

from rich.box import MINIMAL_HEAVY_HEAD
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import yaml

from GenEC.core import MetaData

if TYPE_CHECKING:  # pragma: no cover
    from GenEC.core.configuration import BaseConfiguration
    from GenEC.core.types.output import DataCompare, DataExtract, Entry


ERROR_WRITING_FILE = 'Error writing file {}: {}'


def print_footer() -> None:
    """Print footer with project metadata."""
    console = Console()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    footer = Text()
    footer.append('\n')
    footer.append(f'{MetaData.TOOL.value} {MetaData.VERSION.value} - Generated on {now}\n', style="bold green")
    footer.append(f'{MetaData.REPOSITORY.value}', style="dim cyan")
    console.print(footer)


def get_list_each_element_count(elements: list[str]) -> dict[str, int]:
    """
    Count occurrences of each element in a list.

    Parameters
    ----------
    elements : list[str]
        List of elements to count.

    Returns
    -------
    dict[str, int]
        Dictionary mapping each unique element to its count.
    """
    return dict(Counter(elements))


def read_files(base_path: str, configurations: list['BaseConfiguration']) -> dict[str, str]:
    """
    Read multiple files based on provided configurations.

    Parameters
    ----------
    base_path : str
        Base directory path for files.
    configurations : list[Configuration]
        List of configuration objects specifying target files.

    Returns
    -------
    dict[str, str]
        Dictionary mapping file names to their contents.
    """
    path = Path(base_path)
    unique_files: set[str] = set(c.target_file for c in configurations)
    file_data: dict[str, str] = {}
    for target_file in unique_files:
        file_path = path if target_file == '' else path / target_file
        file_data[target_file] = read_file(file_path)
    return file_data


def read_file(file_path: Path) -> str:
    """
    Read the content of a text file.

    Parameters
    ----------
    file_path : Path
        Path to the file.

    Returns
    -------
    str
        File content as a string.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f'File {file_path} not found.')
    with file_path.open('r', encoding='utf-8') as data:
        return data.read()


def read_yaml_file(file_path: Path) -> Any:
    """
    Read the content of a YAML file with comprehensive error handling.

    Parameters
    ----------
    file_path : Path
        Path to the YAML file.

    Returns
    -------
    Any
        Parsed YAML content.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    UnicodeDecodeError
        If the file cannot be decoded as UTF-8.
    yaml.YAMLError
        If the YAML content is malformed.
    """
    if not file_path.exists():
        raise FileNotFoundError(f'File {file_path} not found.')

    try:
        with file_path.open('r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            e.encoding, e.object, e.start, e.end,
            f'File {file_path} is not valid UTF-8. Please ensure the file is saved with UTF-8 encoding.'
        ) from e
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f'Invalid YAML format in {file_path}: {e}') from e


def append_to_file(data: str, file_path: Path) -> None:
    """
    Write string data to a text file.

    Parameters
    ----------
    data : str
        String content to write.
    file_path : Path
        Path to the output text file.
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('a', encoding='utf-8') as file:
            file.write(data)
    except OSError as err:
        print(ERROR_WRITING_FILE.format(file_path, err))


def _stylized_difference(difference: int) -> Text:
    """
    Stylize the color for the "difference" value of a result.

    Parameters
    ----------
    value : int
        Difference value

    Returns
    -------
    Text
        Rich text object with the stylized difference value
    """
    colors = {0: 'green'}
    color = colors.get(difference, 'bright_blue' if difference > 0 else 'orange1')
    return Text(str(difference), style=color)


def _build_table_title(preset: str, target_file: str) -> Optional[Text]:
    """
    Construct a rich Text object for the table title.

    Parameters
    ----------
    preset : str
        Preset name, can be empty.
    target_file : str
        Target file path, can be empty.

    Returns
    -------
    Optional[Text]
        Rich Text object for table title, or None if both preset and target_file are empty.
    """
    lines: list[tuple[str, str]] = []
    if preset:
        lines.append((f'Preset:      {preset}', 'bold yellow'))
    if target_file:
        lines.append((f'Target file: {target_file}', 'italic cyan'))

    if not lines:
        return None

    title = Text(justify='left')
    for content, style in lines:
        newline = "\n" if content != lines[-1][0] else ''
        title.append(content + newline, style=style)
    return title


def create_extraction_table(data: dict[str, 'DataExtract'], preset: str, target_file: str) -> Panel:
    """
    Create a Rich table from extracted data.

    Parameters
    ----------
    data : dict[str, DataExtract]
        Dictionary of extracted data with source counts.
    preset : str
        Preset name, can be empty.
    target_file : str
        Target file path, can be empty.

    Returns
    -------
    Table
        Rich table displaying the extracted data with optional title showing preset and target file.
    """
    title = _build_table_title(preset, target_file)

    table = Table(title=title, header_style='Bold Magenta')
    table.box = MINIMAL_HEAVY_HEAD
    table.row_styles = ['white', 'grey50']

    # Columns
    table.add_column('Data', justify='left', style='italic bold cyan', min_width=30, max_width=80, overflow='ellipsis')
    table.add_column('(count)\nSource', justify='right', min_width=8, max_width=20, overflow='ellipsis')

    sorted_items = sorted(data.items(), key=lambda x: x[1]['source'], reverse=True)
    for key, value in sorted_items:
        table.add_row(str(key), str(value['source']))

    return Panel(table, expand=False)


def create_comparison_table(data: dict[str, 'DataCompare'], preset: str, target_file: str) -> Panel:
    """
    Create a Rich table comparing source and reference data.

    Parameters
    ----------
    data : dict[str, DataCompare]
        Dictionary of comparison data including source, reference, and difference counts.
    preset : str
        Preset name, can be empty.
    target_file : str
        Target file path, can be empty.

    Returns
    -------
    Table
        Rich table displaying comparison data with optional title showing preset and target file.
    """
    title = _build_table_title(preset, target_file)

    table = Table(title=title, header_style='Bold Magenta')
    table.box = MINIMAL_HEAVY_HEAD
    table.row_styles = ['white', 'grey50']

    table.add_column('Data', justify='left', style='italic bold cyan', min_width=30, max_width=80, overflow='ellipsis')
    table.add_column('(count)\nSource', justify='right', min_width=8, max_width=20, overflow='ellipsis')
    table.add_column('(count)\nReference', justify='right', min_width=8, max_width=20, overflow='ellipsis')
    table.add_column('Difference', justify='right', min_width=8, max_width=20, overflow='ellipsis')

    sorted_items = sorted(data.items(), key=lambda x: x[1]['difference'], reverse=True)
    for key, value in sorted_items:
        table.add_row(
            str(key),
            str(value['source']),
            str(value['reference']),
            _stylized_difference(value['difference'])
        )

    return Panel(table, expand=False)


F = TypeVar('F', bound=Callable[..., None])
_writer_registry: dict[str, Callable[..., None]] = {}


def sort_entry_data_keys(entry: 'Entry') -> 'Entry':
    """
    Return a copy of the entry with its 'data' keys sorted alphabetically.

    Parameters
    ----------
    entry : Entry
        Original entry dictionary.

    Returns
    -------
    Entry
        Copy of the entry with sorted 'data' dictionary.
    """
    data = entry.get('data', {})
    sorted_data = dict(sorted(data.items()))
    new_entry = entry.copy()
    new_entry['data'] = sorted_data
    return new_entry


def register_writer(name: str) -> Callable[[F], F]:
    """
    Register a new output writer function.

    Parameters
    ----------
    name : str
        Name of the writer.

    Returns
    -------
    Callable[[F], F]
        Decorator that registers the function.
    """
    def decorator(func: F) -> F:
        _writer_registry[name] = func
        return func
    return decorator


def get_writer(name: str) -> Callable[..., None]:
    """
    Retrieve a registered writer function by name.

    Parameters
    ----------
    name : str
        Name of the writer.

    Returns
    -------
    Callable
        The registered writer function.

    Raises
    ------
    ValueError
        If the writer is not registered.
    """
    try:
        return _writer_registry[name]
    except KeyError as exc:  # pragma: no cover
        raise ValueError(f'Writer [{name}] is not registered.') from exc


@register_writer('json')
def write_json(data: Any, file_path: Path) -> None:
    """
    Write data to a JSON file.

    Parameters
    ----------
    data : list[Entry]
        List of entries to write.
    file_path : Path
        Path to the output JSON file.
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
    except OSError as err:  # pragma: no cover
        print(ERROR_WRITING_FILE.format(file_path, err))


@register_writer('yaml')
def write_yaml(data: Any, file_path: Path) -> None:
    """
    Write data to a YAML file.

    Parameters
    ----------
    data : list[Entry]
        List of entries to write.
    file_path : Path
        Path to the output YAML file.
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('w', encoding='utf-8') as file:
            yaml.dump(data, file, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except OSError as err:  # pragma: no cover
        print(ERROR_WRITING_FILE.format(file_path, err))


@register_writer('csv')
def write_csv(data: list['Entry'], file_path: Path) -> None:
    """
    Write data to a CSV file.

    Parameters
    ----------
    data : list[Entry]
        List of entries to write.
    file_path : Path
        Path to the output CSV file.
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        all_columns: Set[str] = set()
        rows: list[dict[str, Any]] = []
        for entry in data:
            for data_key, values in entry.get('data', {}).items():
                row: dict[str, Any] = {**entry, 'data': data_key, **values}
                rows.append(row)
                all_columns.update(row.keys())

        with file_path.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted(all_columns))
            writer.writeheader()
            writer.writerows(rows)
    except OSError as err:
        print(ERROR_WRITING_FILE.format(file_path, err))


@register_writer('txt')
def write_txt(tables: list[Panel], file_path: Path) -> None:
    """
    Write string data to a text file.

    Parameters
    ----------
    data : list[Table]
        List of tables to write.
    file_path : Path
        Path to the output text file.
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('w', encoding='utf-8') as file:
            console = Console(file=file, width=120)
            for table in tables:
                console.print(table)
                console.print()
    except OSError as err:
        print(ERROR_WRITING_FILE.format(file_path, err))


def write_output(data: list['Entry'], ascii_tables: list[Panel], file_path: Path, output_types: list[str]) -> None:
    """
    Write output data in multiple formats.

    Parameters
    ----------
    data : list[Entry]
        List of entries to write.
    ascii_tables : list[Table]
        ASCII table representation of the data.
    file_path : Path
        Base path for output files.
    output_types : list[str]
        List of output formats to write (e.g., 'json', 'yaml', 'csv', 'txt').
    """
    for output_type in output_types:
        writer = get_writer(output_type)
        file_path_with_extension = file_path.with_suffix(f'.{output_type}')
        if output_type == 'txt':
            writer(ascii_tables, file_path_with_extension)
        else:
            writer(data, file_path_with_extension)


def convert_to_yaml(data: Any) -> str:
    """
    Convert an object to yaml.

    Parameters
    ----------
    data : Any
        Any data object

    Returns
    -------
    str
        yaml string
    """
    return yaml.dump(data, sort_keys=False, default_flow_style=False, allow_unicode=True)


def normalize_cluster_filter(cluster_filter: str) -> str:
    """
    Normalize the cluster filter string by decoding unicode escapes.

    Parameters
    ----------
    cluster_filter : Optional[str]
        The raw cluster filter string.

    Returns
    -------
    str
        The normalized cluster filter string.
    """
    return cluster_filter.encode('utf-8').decode('unicode_escape')
