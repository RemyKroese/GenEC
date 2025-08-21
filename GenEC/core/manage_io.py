"""Module for managing the input, and output of the program."""

from pathlib import Path
from typing import cast, Optional, Union, TYPE_CHECKING

from rich.console import Console

from GenEC import utils
from GenEC.core import PositionalFilterType, ConfigOptions, TextFilterTypes
from GenEC.core.prompts import Section, Key, create_prompt
from GenEC.core.types.preset_config import Initialized
from GenEC.core.types.output import DataCompare, DataExtract, Entry
from GenEC.core.input_strategies import get_input_strategy

if TYPE_CHECKING:  # pragma: no cover
    from rich.panel import Panel

console = Console()


YES_INPUT = ['yes', 'y']


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
            input_string: str = InputManager.ask_open_question(create_prompt(Section.SET_CONFIG, Key.CLUSTER_FILTER)) or '\\n'
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
            return InputManager.ask_mpc_question(create_prompt(Section.SET_CONFIG, Key.TEXT_FILTER_TYPE), [t.value for t in TextFilterTypes])
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
            response = InputManager.ask_open_question(create_prompt(Section.SET_CONFIG, Key.SHOULD_SLICE_CLUSTERS)).lower()
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
            return InputManager.ask_open_question(create_prompt(Section.SET_CONFIG, Key.CLUSTER_TEXT, cluster=src_or_ref.lower(), position=position))
        return cast(str, config[config_option])

    @staticmethod
    def request_text_filter(config: Initialized) -> Union[str, PositionalFilterType, list[str]]:
        """
        Request a text filter from the user according to the selected filter type.

        Parameters
        ----------
        config : Initialized
            The configuration object containing the filter type.

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
        filter_type = config.get(ConfigOptions.TEXT_FILTER_TYPE.value)
        if not filter_type:
            raise ValueError("Text filter type must be set before requesting text filter")

        strategy = get_input_strategy(filter_type, InputManager.ask_open_question)
        return strategy.collect_input(config)

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
        console.print(prompt, end='')
        return input()

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
        console.print(prompt)
        console.print(create_prompt(Section.USER_CHOICE, Key.EXIT_OPTION))
        for i, option in enumerate(options, 1):
            console.print(f'{i}. {option}')

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
                console.print(create_prompt(Section.USER_CHOICE, Key.CHOICE, max_index=max_choice), end='')
                choice = int(input())
                if not 0 <= choice <= max_choice:
                    raise ValueError
                return choice
            except ValueError:
                console.print(create_prompt(Section.USER_CHOICE, Key.INVALID_CHOICE))


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
            ascii_tables: list['Panel'] = []
            for entry in entries:
                if is_comparison:
                    ascii_tables.append(utils.create_comparison_table(cast(dict[str, DataCompare],
                                                                           entry['data']), entry.get('preset'), entry.get('target')))
                else:
                    ascii_tables.append(utils.create_extraction_table(cast(dict[str, DataExtract],
                                                                           entry['data']), entry.get('preset'), entry.get('target')))
            if self.should_print_results:
                for table in ascii_tables:
                    console.print('\n')
                    console.print(table)
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
