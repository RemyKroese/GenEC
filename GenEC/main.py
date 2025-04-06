#!/usr/bin/env python
import argparse
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from GenEC import utils                     # noqa: E402
from GenEC.core import analyze, manage_io   # noqa: E402
from GenEC.core import FileID               # noqa: E402


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
    parser.add_argument('-o', '--output_directory', type=str, required=False,
                        help='Output directory to store results.')

    return parser.parse_args()


def main():
    args = parse_arguments()
    source, ref = utils.read_files([args.source, args.reference])
    input_manager = manage_io.InputManager(args.preset)
    input_manager.set_config()

    extractor = analyze.Extractor(input_manager.config)
    source_filtered_text = extractor.extract_from_data(source, FileID.SOURCE)
    ref_filtered_text = extractor.extract_from_data(ref, FileID.REFERENCE)

    comparer = analyze.Comparer(source_filtered_text, ref_filtered_text)
    differences = comparer.compare()

    output_directory = args.output_directory if args.output_directory else None
    output_manager = manage_io.OutputManager(output_directory)
    output_manager.process(differences)


if __name__ == '__main__':
    main()
