from prettytable import PrettyTable
import json
import os


ERROR_WRITING_FILE = 'Error writing file {}: {}'


def read_files(file_paths):
    files = []
    for file in file_paths:
        files.append(read_file(file))
    return files


def read_file(file):
    with open(file, 'r') as data:
        return data.read()


def create_ascii_table(data):
    table = PrettyTable()
    table.title = 'GenEC results'
    table.field_names = ['Text', 'Source count', 'Reference count', 'Difference']
    table.align = 'l'

    for key in data:
        table.add_row([key, data[key]['source'], data[key]['reference'], data[key]['difference']])

    return table.get_string(sortby='Difference', reversesort=True)


def write_to_txt_file(data, file_path):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(data)
    except OSError as err:
        print(ERROR_WRITING_FILE.format(file_path, err))


def write_to_json_file(data, file_path):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
    except OSError as err:
        print(ERROR_WRITING_FILE.format(file_path, err))
