#!/usr/bin/env python
import argparse
import os
import sys
from typing import Optional

PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_PATH)

from GenEC import utils                                    # noqa: E402
from GenEC.core import analyze, manage_io                  # noqa: E402
from GenEC.core import FileID                              # noqa: E402
from GenEC.core.config_manager import ConfigManager        # noqa: E402


def parse_arguments() -> argparse.Namespace:
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


def build_preset_param(args: argparse.Namespace) -> Optional[dict[str, str]]:
    if args.preset_list:
        return {'type': 'preset-list', 'value': args.preset_list}
    if args.preset:
        return {'type': 'preset', 'value': args.preset}
    return None


def main():
    args = parse_arguments()
    preset_param = build_preset_param(args)

    config_manager = ConfigManager(preset_param, args.presets_directory)
    extractor = analyze.Extractor()
    output_manager = manage_io.OutputManager(args.output_directory)

    source_data = utils.read_files(args.source, config_manager.configurations)
    ref_data = utils.read_files(args.reference, config_manager.configurations) if args.reference else None

    for configuration in config_manager.configurations:
        source_text = source_data.get(configuration.target_file, '')
        source_filtered = extractor.extract_from_data(configuration.config, source_text, FileID.SOURCE)
        output_path = os.path.join(configuration.preset, os.path.splitext(configuration.target_file)[0])

        if ref_data:  # extract and compare
            ref_text = ref_data.get(configuration.target_file, '')
            ref_filtered = extractor.extract_from_data(configuration.config, ref_text, FileID.REFERENCE)
            comparer = analyze.Comparer(source_filtered, ref_filtered)
            results = comparer.compare()
            output_manager.process(results, file_name=output_path, is_comparison=True)
        else:  # extract only
            results = utils.get_list_each_element_count(source_filtered)
            output_results = {key: {'source': value} for key, value in results.items()}
            output_manager.process(output_results, file_name=output_path, is_comparison=False)


if __name__ == '__main__':
    main()
