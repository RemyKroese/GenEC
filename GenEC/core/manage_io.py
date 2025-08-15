"""Module for managing the input, and output of the program."""

from pathlib import Path
from typing import cast, Optional, Union

from GenEC import utils
from GenEC.core import PositionalFilterType, ConfigOptions, TextFilterTypes
from GenEC.core.types.preset_config import Initialized
from GenEC.core.types.output import DataCompare, DataExtract, Entry


YES_INPUT = ['yes', 'y']
NO_INPUT = ['no', 'n']


class InputManager:
    """
    Handles all user inputs required for configuring text extraction and comparison.

    This class provides static methods to prompt the user for filters, cluster slicing,
    and cluster text positions, and also validates the input values.

    Raises
    ------
    ValueError
        If an unsupported text filter type is provided when requesting a filter.
    """

    @staticmethod
    def set_cluster_filter(config: Initialized) -> str:
        """
        Get or request the cluster splitting character(s) from the user.

        Parameters
        ----------
        config : Initialized
            The configuration object containing preset values.

        Returns
        -------
        str
            The character(s) used to split text clusters.
        """
        if not config.get(ConfigOptions.CLUSTER_FILTER.value):
            input_string: str = InputManager.ask_open_question(
                'Please indicate the character(s) to split text clusters on (Default: Newline [\\n]): ')
        else:
            input_string: str = cast(str, config[ConfigOptions.CLUSTER_FILTER.value])
        return input_string

    @staticmethod
    def set_text_filter_type(config: Initialized) -> str:
        """
        Get or request the text filter type from the user.

        Parameters
        ----------
        config : Initialized
            The configuration object containing preset values.

        Returns
        -------
        str
            The selected text filter type, e.g., 'regex', 'positional', or 'regex-list'.
        """
        if not config.get(ConfigOptions.TEXT_FILTER_TYPE.value):
            return InputManager.ask_mpc_question('Please choose a filter type:\n', [t.value for t in TextFilterTypes])
        return cast(str, config[ConfigOptions.TEXT_FILTER_TYPE.value])

    @staticmethod
    def set_text_filter(config: Initialized) -> Union[str, PositionalFilterType, list[str]]:
        """
        Get or request the actual text filter based on the selected filter type.

        Parameters
        ----------
        config : Initialized
            The configuration object containing preset values.

        Returns
        -------
        Union[str, PositionalFilterType, list[str]]
            The configured text filter, which can be a regex string, a positional filter object,
            or a list of regex strings.
        """
        if not config.get(ConfigOptions.TEXT_FILTER.value):
            return InputManager.request_text_filter(config)
        return cast(Union[str, PositionalFilterType, list[str]], config[ConfigOptions.TEXT_FILTER.value])

    @staticmethod
    def set_should_slice_clusters(config: Initialized) -> bool:
        """
        Determine if only a subsection of clusters should be compared.

        Parameters
        ----------
        config : Initialized
            The configuration object containing preset values.

        Returns
        -------
        bool
            True if a subsection of clusters should be compared, False otherwise.
        """
        if config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value) is None:  # False is a valid value
            response = InputManager.ask_open_question(
                'Do you want to compare only a subsection of the clusters (press enter to skip)? [yes/y]: ').lower()
            return response in YES_INPUT
        return cast(bool, config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value])

    @staticmethod
    def set_cluster_text(config: Initialized, config_option: str, position: str, src_or_ref: str) -> str:
        """
        Get or request the text within a cluster for a specific subsection.

        Parameters
        ----------
        config : Initialized
            The configuration object containing preset values.
        config_option : str
            The configuration key to check for existing value.
        position : str
            Indicates where the subsection should be within the cluster (e.g., 'start' or 'end').
        src_or_ref : str
            Indicates whether this is source or reference cluster.

        Returns
        -------
        str
            The text input for the cluster subsection.
        """
        if not config.get(config_option):
            return InputManager.ask_open_question(
                f'Text in the {src_or_ref.lower()} cluster where the subsection should {position} (press enter to skip): ')
        return cast(str, config[config_option])

    @staticmethod
    def request_text_filter(config: Initialized) -> Union[str, PositionalFilterType, list[str]]:
        """
        Request a text filter from the user according to the selected filter type.

        Returns
        -------
        Union[str, PositionalFilterType, list[str]]
            The configured text filter, which can be a regex string, a positional filter object,
            or a list of regex strings.

        Raises
        ------
        ValueError
            If the selected text filter type is not supported.
        """
        if config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.REGEX.value:
            return InputManager.ask_open_question('Please provide a regex filter: ')
        elif config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.POSITIONAL.value:
            separator_input = InputManager.ask_open_question('Please provide the separator for counting (default: 1 space character): ')
            positional_text_filter = PositionalFilterType(
                separator=separator_input if separator_input else ' ',
                line=int(InputManager.ask_open_question('Please provide the line number in the cluster: ')),
                occurrence=int(InputManager.ask_open_question('Please provide the occurrence number: ')))
            return positional_text_filter
        elif config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.REGEX_LIST.value:
            regex_list_filters: list[str] = []
            index = 1
            while True:
                regex_list_filters.append(InputManager.ask_open_question(f'Please provide a regex filter for search {index}: '))
                index += 1
                if InputManager.ask_open_question('Do you wish to provide a next search parameter [yes/y]: ').lower() not in YES_INPUT:
                    break
            return regex_list_filters
        else:
            raise ValueError(f'Unsupported filter type: {config.get(ConfigOptions.TEXT_FILTER_TYPE.value)}')

    @staticmethod
    def ask_open_question(prompt: str) -> str:
        """
        Prompt the user with an open-ended question.

        Parameters
        ----------
        prompt : str
            The message to display to the user.

        Returns
        -------
        str
            The user's input.
        """
        return input(prompt)

    @staticmethod
    def ask_mpc_question(prompt: str, options: list[str]) -> str:
        """
        Prompt the user with a multiple-choice question.

        Parameters
        ----------
        prompt : str
            The message to display to the user.
        options : list[str]
            The list of selectable options.

        Returns
        -------
        str
            The selected option from the list.
        """
        print(prompt)
        print('0. Exit')
        for i, option in enumerate(options, 1):
            print(f'{i}. {option}')

        choice = InputManager.get_user_choice(len(options))

        if choice == 0:
            exit()  # Exit the script
        else:
            return options[choice - 1]

    @staticmethod
    def get_user_choice(max_choice: int) -> int:
        """
        Get a numeric choice from the user within a specified range.

        Parameters
        ----------
        max_choice : int
            The maximum valid choice value.

        Returns
        -------
        int
            The user's chosen number within the range [0, max_choice].
        """
        while True:
            try:
                choice = int(input(f'Choose a number [0-{max_choice}]: '))
                if 0 <= choice <= max_choice:
                    return choice
                else:
                    print('Please enter a valid number.')
            except ValueError:
                print('Please enter a valid number.')


class OutputManager:
    """
    Handles formatting, printing, and writing of extracted or compared results.

    This class can optionally write results to files in multiple formats and print
    ASCII tables of the results to the console.
    """

    def __init__(self,
                 output_directory: Optional[str] = None,
                 output_types: Optional[list[str]] = None,
                 should_print_results: bool = True) -> None:
        self.output_directory = Path(output_directory) if output_directory else None
        self.output_types = output_types
        self.should_print_results = should_print_results

    def process(self,
                results: dict[str, list[Entry]],
                root: str,
                file_name: str = 'result',
                is_comparison: bool = False
                ) -> None:
        """
        Process and output extracted or compared results.

        Parameters
        ----------
        results : dict[str, list[Entry]]
            The results grouped by preset or category.
        root : str
            The root directory or identifier of the source data.
        file_name : str, optional
            The base name of output files, by default 'result'.
        is_comparison : bool, optional
            Whether the results are comparison results, by default False.
        """
        for group, entries in results.items():
            ascii_tables = ''
            for entry in entries:
                title = f"{entry['preset']}"
                if entry['target']:
                    title += f" - {entry['target']}"
                if is_comparison:
                    ascii_tables += utils.create_comparison_ascii_table(cast(dict[str, DataCompare], entry['data']), title)
                else:
                    ascii_tables += utils.create_extraction_ascii_table(cast(dict[str, DataExtract], entry['data']), title)
                ascii_tables += '\n\n'
            if self.should_print_results:
                print(ascii_tables)
            if self.output_directory and self.output_types:
                output_path = self._create_output_path(group, root, file_name=file_name)
                utils.write_output(entries, ascii_tables, output_path, self.output_types)

    def _create_output_path(self, group: str, root: str, file_name: str = 'result') -> Path:
        """
        Construct the output file path for a specific group.

        Parameters
        ----------
        group : str
            The group name or category.
        root : str
            The root directory or file identifier of the source data.
        file_name : str, optional
            The base name of the output file, by default 'result'.

        Returns
        -------
        Path
            The complete path to the output file.
        """
        root_path = Path(root).name
        root_path_without_extension = Path(root_path).stem
        group_dir = cast(Path, self.output_directory) / root_path_without_extension / group
        return group_dir / file_name
