from prettytable import PrettyTable


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
