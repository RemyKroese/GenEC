#!/usr/bin/env python
import argparse
import utils
from core import analyze


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Extract specific data from files and' +
        'and compare the differences between these 2 files based on the data.')

    parser.add_argument('-s', '--source', type=str, required=True,
                        help='Source file to extract data and compare.')
    parser.add_argument('-r', '--reference', type=str, required=True,
                        help='Reference file to extract data and compare.')
    parser.add_argument('-t', '--template', type=str, required=False,
                        help='Template to use as analysis parameters.')

    return parser.parse_args()


def main():
    args = parse_arguments()
    source, ref = utils.read_files([args.source, args.reference])
    input_manager = analyze.InputManager(args.template)
    input_manager.set_config()
    extractor = analyze.Extractor(input_manager.config)
    print('Extracting data from source file...')
    source_filtered_text = extractor.extract_from_data(source, analyze.Files.SOURCE)
    print('Extracting complete.')
    print('Extracting data from reference file...')
    ref_filtered_text = extractor.extract_from_data(ref, analyze.Files.REFERENCE)
    print('Extracting complete.')

    comparer = analyze.Comparer(source_filtered_text, ref_filtered_text)
    differences = comparer.compare()

    print(utils.create_ascii_table(differences))


if __name__ == '__main__':
    main()
