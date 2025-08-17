"""Command-line interface for GenEC workflows."""

import argparse
from typing import cast, Optional, Sequence, Union
from pathlib import Path
import sys


# Pyinstaller workaround
if getattr(sys, 'frozen', False):  # pragma: no cover
    project_path = Path(sys.executable).parent
else:
    project_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_path))

from GenEC.core import workflows, Workflows  # noqa: E402  # pylint: disable=wrong-import-position
from GenEC.utils import print_footer         # noqa: E402  # pylint: disable=wrong-import-position


def parse_target_variables(pairs: Sequence[str]) -> dict[str, str]:
    """
    Parse a sequence of 'key=value' strings into a dictionary.

    Parameters
    ----------
    pairs : Sequence[str]
        List of strings, each in the format 'key=value'.

    Returns
    -------
    dict[str, str]
        Dictionary mapping keys to values from the input sequence.

    Raises
    ------
    argparse.ArgumentTypeError
        If a string does not contain '=' or has an empty key.
    """
    result: dict[str, str] = {}
    for pair in pairs:
        if '=' not in pair:
            raise argparse.ArgumentTypeError(f'Invalid format for path-var [{pair}]. Expected key=value.')
        key, value = pair.split('=', 1)
        if not key:
            raise argparse.ArgumentTypeError(f'Empty key in path-var [{pair}].')
        result[key] = value
    return result


class TargetVariablesAction(argparse.Action):
    """
    Parse key=value pairs from the command line into a dictionary.

    This action updates the namespace attribute with a dictionary of
    key-value pairs provided as command-line arguments.

    Parameters
    ----------
    option_strings : list[str]
        List of option strings, e.g., ['-v', '--target-variables'].
    dest : str
        The name of the attribute to hold the parsed dictionary.
    nargs : int, optional
        Number of arguments consumed. Default is None.
    """

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Optional[Union[str, Sequence[str]]],
        option_string: Optional[str] = None,
    ) -> None:
        """
        Parse values and update the namespace dictionary.

        Parameters
        ----------
        parser : argparse.ArgumentParser
            The argument parser invoking this action.
        namespace : argparse.Namespace
            The namespace object to update with parsed key-value pairs.
        values : Optional[Union[str, Sequence[str]]]
            A string or list of 'key=value' pairs to parse.
        option_string : Optional[str], optional
            The option string that triggered this action, by default None
        """
        current_dict = getattr(namespace, self.dest, {}) or {}
        parsed = parse_target_variables(cast(Sequence[str], values))
        current_dict.update(parsed)
        setattr(namespace, self.dest, current_dict)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the GenEC workflows.

    Returns
    -------
    argparse.Namespace
        Namespace containing parsed arguments including workflow selection,
        file paths, output options, and presets.
    """
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
                               default=project_path / 'GenEC' / 'presets',
                               help='Directory where presets are stored. default: %(default)s')

    parser = argparse.ArgumentParser(
        prog='GenEC',
        description='Extract specific data from files and compare the differences between them.')
    subparsers = parser.add_subparsers(dest='workflow', required=True)

    # Basic workflow
    subparsers.add_parser(name=Workflows.BASIC.value, parents=[common],
                          help='Define extraction method at run-time.')

    # Preset workflow
    preset = subparsers.add_parser(name=Workflows.PRESET.value, parents=[common, common_preset],
                                   help='Define extraction method through a preset.')
    preset.add_argument('-p', '--preset', type=str, required=True,
                        help='Preset to use as analysis parameters.')

    # Preset-list workflow
    preset_list = subparsers.add_parser(name=Workflows.PRESET_LIST.value, parents=[common, common_preset],
                                        help='Define multiple extraction methods through a preset list.')
    preset_list.add_argument('-l', '--preset-list', type=str, required=True,
                             help='A list of presets to perform a larger scale analysis.')
    preset_list.add_argument('-v', '--target-variables', type=str, nargs='+',
                             action=TargetVariablesAction, metavar='VARIABLE=VALUE',
                             help='Variable=value pairs for dynamic path substitution in preset-list workflow.')

    args = parser.parse_args()
    if (args.output_directory is None) != (args.output_types is None):
        parser.error('Arguments --output-directory and --output-types must both be provided or neither.')
    return args


def main():
    """
    Execute the GenEC command-line interface.

    Parses command-line arguments and runs the selected workflow.
    """
    args = parse_arguments()
    workflows.get_workflow(args.workflow, args).run()

    print_footer()


if __name__ == '__main__':
    main()
