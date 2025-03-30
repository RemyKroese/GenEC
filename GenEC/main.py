#!/usr/bin/env python
import argparse
import os
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
    parser.add_argument('-p', '--preset', type=str, required=False,
                        help='Preset to use as analysis parameters.')
    parser.add_argument('-o', '--output_folder', type=str, required=False,
                        help='Output folder to store results.')

    return parser.parse_args()


def main():
    args = parse_arguments()
    source, ref = utils.read_files([args.source, args.reference])
    input_manager = analyze.InputManager(args.preset)
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

    ascii_table = utils.create_ascii_table(differences)
    print(ascii_table)

    if args.output_folder:
        utils.write_to_txt_file(ascii_table, os.path.join(args.output_folder, 'results.txt'))
        utils.write_to_json_file(differences, os.path.join(args.output_folder, 'results.json'))


if __name__ == '__main__':
    main()
