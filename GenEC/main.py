#!/usr/bin/env python
import argparse
from collections import defaultdict
import os
import sys
from typing import Optional

PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_PATH)

from GenEC import utils                                             # noqa: E402
from GenEC.core import FileID                                       # noqa: E402
from GenEC.core.analyze import Extractor, Comparer                  # noqa: E402
from GenEC.core.config_manager import ConfigManager, Configuration  # noqa: E402
from GenEC.core.manage_io import OutputManager                      # noqa: E402
from GenEC.core.types.output import DataExtract, Entry              # noqa: E402


def parse_arguments() -> argparse.Namespace:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('-s', '--source', type=str, required=True,
                        help='Source file to extract data from.')
    common.add_argument('-r', '--reference', type=str, required=False,
                        help='Reference file to extract data from and compare against source.')
    common.add_argument('-o', '--output-directory', type=str, required=False,
                        help='Output directory to store results (json and txt).')
    common.add_argument('-t', '--output-types', type=str, nargs='+', required=False,
                        choices=['csv', 'json', 'txt', 'yaml'],
                        help='Output file types to generate. Provide at least one if --output-directory is set.')

    common_preset = argparse.ArgumentParser(add_help=False)
    common_preset.add_argument('-x', '--presets-directory', type=str, required=False,
                               default=os.path.abspath(os.path.join(PROJECT_PATH, 'GenEC', 'presets')),
                               help='Directory where presets are stored. default: %(default)s')

    parser = argparse.ArgumentParser(
        prog='GenEC',
        description='Extract specific data from files and ' +
        'compare the differences between these two files based on the data.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # basic workflow: analysis construction through CLI
    subparsers.add_parser(name='basic', parents=[common],
                          help='Define extraction method at run-time.')

    # preset workflow: analysis construction through a preset yaml file
    preset = subparsers.add_parser(name='preset', parents=[common, common_preset],
                                   help='Define extraction method through a preset.')
    preset.add_argument('-p', '--preset', type=str, required=True,
                        help='Preset to use as analysis parameters.')

    # preset-list workflow: Bulk analysis construction through a preset-list yaml file
    preset_list = subparsers.add_parser(name='preset-list', parents=[common, common_preset],
                                        help='Define multiple extraction methods through a preset list.')
    preset_list.add_argument('-l', '--preset-list', type=str, required=True,
                             help='A list of presets to perform a larger scale analysis.')

    args = parser.parse_args()
    if (args.output_directory is None) != (args.output_types is None):
        parser.error('Arguments --output-directory and --output-types must both be provided or neither.')
    return args


def build_preset_param(args: argparse.Namespace) -> Optional[dict[str, str]]:
    if hasattr(args, 'preset_list') and args.preset_list:
        return {'type': 'preset-list', 'value': args.preset_list}
    elif hasattr(args, 'preset') and args.preset:
        return {'type': 'preset', 'value': args.preset}
    return None


def run_analysis(
        configurations: list[Configuration],
        source_data: dict[str, str],
        ref_data: Optional[dict[str, str]] = None
        ) -> defaultdict[str, list[Entry]]:
    results: defaultdict[str, list[Entry]] = defaultdict(list)
    extractor = Extractor()

    for configuration in configurations:
        source_text = source_data.get(configuration.target_file, '')
        source_filtered = extractor.extract_from_data(configuration.config, source_text, FileID.SOURCE)

        if ref_data:  # extract and compare
            ref_text = ref_data.get(configuration.target_file, '')
            ref_filtered = extractor.extract_from_data(configuration.config, ref_text, FileID.REFERENCE)
            comparer = Comparer(source_filtered, ref_filtered)
            result = comparer.compare()
            results[configuration.group].append(Entry(
                preset=configuration.preset,
                target=configuration.target_file,
                data=result))
        else:  # extract only
            result = utils.get_list_each_element_count(source_filtered)
            output_result: dict[str, DataExtract] = {key: {'source': value} for key, value in result.items()}
            results[configuration.group].append(Entry(
                preset=configuration.preset,
                target=configuration.target_file,
                data=output_result))
    return results


def main():
    args = parse_arguments()
    preset_param = build_preset_param(args)

    config_manager = ConfigManager(preset_param, args.presets_directory if hasattr(args, 'presets_directory') else None)

    source_data = utils.read_files(args.source, config_manager.configurations)
    ref_data = utils.read_files(args.reference, config_manager.configurations) if args.reference else None

    results = run_analysis(config_manager.configurations, source_data, ref_data)

    output_manager = OutputManager(args.output_directory, args.output_types)
    output_manager.process(results, root=args.source, is_comparison=bool(ref_data))


if __name__ == '__main__':
    main()
