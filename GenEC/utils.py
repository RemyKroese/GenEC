from collections import Counter
import json
import os
import six
import sys
import yaml

from prettytable import PrettyTable

# Python 2 fallback
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


ERROR_WRITING_FILE = 'Error writing file {}: {}'


def safe_print(s):
    print(type(s))
    if sys.version_info.major < 3 and isinstance(s, str):
        s = s.decode('utf-8')
    print(s)


def get_list_each_element_count(elements):
    return {k: {'count': v} for k, v in Counter(elements).items()}


def read_files(file_paths):
    files = []
    for file in file_paths:
        files.append(read_file(file))
    return files


def read_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError('File {} not found.'.format(file_path))
    with open(file_path, 'r') as data:
        return data.read()


def read_yaml_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError('File {} not found.'.format(file_path))
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)


def create_extraction_ascii_table(data):
    table = PrettyTable()
    table.title = 'GenEC results'
    table.field_names = ['Text', 'Count']
    table.align = 'l'

    for key in data:
        table.add_row([key, data[key]['count']])

    return table.get_string(sortby='Count', reversesort=True)


def create_comparison_ascii_table(data):
    table = PrettyTable()
    table.title = 'GenEC results'
    table.field_names = ['Text', 'Source count', 'Reference count', 'Difference']
    table.align = 'l'

    for key in data:
        table.add_row([key, data[key]['source'], data[key]['reference'], data[key]['difference']])

    return table.get_string(sortby='Difference', reversesort=True)


def write_to_txt_file(data, file_path):
    try:
        ensure_directory_exists(os.path.dirname(file_path))
        with open_with_encoding(file_path, 'w', 'utf-8') as file:
            file.write(data)
    except OSError as err:
        print(six.text_type(ERROR_WRITING_FILE.format(file_path, err)))


def write_to_json_file(data, file_path):
    try:
        ensure_directory_exists(os.path.dirname(file_path))
        with open_with_encoding(file_path, 'wb') as file:
            json.dump(data, file, indent=4)
    except OSError as err:
        print(six.text_type(ERROR_WRITING_FILE.format(file_path, err)))


def ensure_directory_exists(path):
    try:
        os.makedirs(path, exist_ok=True)
    except TypeError:  # Python 2 fallback
        if not os.path.exists(path):
            os.makedirs(path)


def open_with_encoding(file_path, mode, encoding=None):
    try:
        return open(file_path, mode, encoding=encoding)
    except TypeError:  # Python 2 fallback
        import io
        return io.open(file_path, mode, encoding=encoding)
