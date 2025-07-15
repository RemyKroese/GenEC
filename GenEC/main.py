#!/usr/bin/env python
import argparse
import os
import sys

PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_PATH)

from GenEC import utils                     # noqa: E402
from GenEC.core import analyze, manage_io   # noqa: E402
from GenEC.core import FileID               # noqa: E402


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Extract specific data from files and ' +
        'compare the differences between these two files based on the data.')

    parser.add_argument('-s', '--source', type=str, required=True,
                        help='Source file to extract data from.')
    parser.add_argument('-r', '--reference', type=str, required=False,
                        help='Reference file to extract data from and compare against source.')
    parser.add_argument('-o', '--output-directory', type=str, required=False,
                        help='Output directory to store results (json and txt).')

    parser.add_argument('-x', '--presets-directory', type=str, required=False,
                        default=os.path.abspath(os.path.join(PROJECT_PATH, 'GenEC', 'presets')),
                        help='Directory where presets are stored. default: %(default)s')

    # Only a preset, or a preset-list should be provided
    preset_group = parser.add_mutually_exclusive_group(required=False)
    preset_group.add_argument('-p', '--preset', type=str, required=False,
                              help='Preset to use as analysis parameters.')
    preset_group.add_argument('-l', '--preset-list', type=str, required=False,
                              help='A list of presets to perform a larger scale analysis.')

    return parser.parse_args()


def main():
    args = parse_arguments()
    source = utils.read_file(args.source)
    ref = utils.read_file(args.reference) if args.reference else None
    preset_param = None
    if args.preset_list:
        preset_param = {'type': 'preset-list', 'value': args.preset_list}
    elif args.preset:
        preset_param = {'type': 'preset', 'value': args.preset}

    input_manager = manage_io.InputManager(preset_param, args.presets_directory)
    input_manager.set_config()
    extractor = analyze.Extractor(input_manager.config)
    output_manager = manage_io.OutputManager(args.output_directory)

    source_filtered_text = extractor.extract_from_data(source, FileID.SOURCE)

    if ref:
        ref_filtered_text = extractor.extract_from_data(ref, FileID.REFERENCE)
        comparer = analyze.Comparer(source_filtered_text, ref_filtered_text)
        results = comparer.compare()
        output_manager.process(results, is_comparison=True)
    else:
        results = utils.get_list_each_element_count(source_filtered_text)
        output_manager.process(results, is_comparison=False)


if __name__ == '__main__':
    main()
