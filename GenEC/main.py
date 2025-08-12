#!/usr/bin/env python
import argparse
import os
import sys

PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_PATH)

from GenEC.core import workflows, Workflows  # noqa: E402


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
    subparsers = parser.add_subparsers(dest='workflow', required=True)

    # basic workflow: analysis construction through CLI
    subparsers.add_parser(name=Workflows.BASIC.value, parents=[common],
                          help='Define extraction method at run-time.')

    # preset workflow: analysis construction through a preset yaml file
    preset = subparsers.add_parser(name=Workflows.PRESET.value, parents=[common, common_preset],
                                   help='Define extraction method through a preset.')
    preset.add_argument('-p', '--preset', type=str, required=True,
                        help='Preset to use as analysis parameters.')

    # preset-list workflow: Bulk analysis construction through a preset-list yaml file
    preset_list = subparsers.add_parser(name=Workflows.PRESET_LIST.value, parents=[common, common_preset],
                                        help='Define multiple extraction methods through a preset list.')
    preset_list.add_argument('-l', '--preset-list', type=str, required=True,
                             help='A list of presets to perform a larger scale analysis.')

    args = parser.parse_args()
    if (args.output_directory is None) != (args.output_types is None):
        parser.error('Arguments --output-directory and --output-types must both be provided or neither.')
    return args


def main():
    args = parse_arguments()
    workflows.get_workflow(args.workflow, args).run()


if __name__ == '__main__':
    main()
