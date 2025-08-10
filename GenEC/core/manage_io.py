import os
from typing import cast, Optional, Union

from GenEC import utils
from GenEC.core import PositionalFilterType, ConfigOptions, TextFilterTypes
from GenEC.core.types.preset_config import Initialized
from GenEC.core.types.output import DataCompare, DataExtract, Entry


YES_INPUT = ['yes', 'y']
NO_INPUT = ['no', 'n']


class InputManager:
    @staticmethod
    def set_cluster_filter(config: Initialized) -> str:
        if not config.get(ConfigOptions.CLUSTER_FILTER.value):
            input_string: str = InputManager.ask_open_question(
                'Please indicate the character(s) to split text clusters on (Default: Newline [\\n]): ')
        else:
            input_string: str = cast(str, config[ConfigOptions.CLUSTER_FILTER.value])
        return input_string

    @staticmethod
    def set_text_filter_type(config: Initialized) -> str:
        if not config.get(ConfigOptions.TEXT_FILTER_TYPE.value):
            return InputManager.ask_mpc_question('Please choose a filter type:\n', [t.value for t in TextFilterTypes])
        return cast(str, config[ConfigOptions.TEXT_FILTER_TYPE.value])

    @staticmethod
    def set_text_filter(config: Initialized) -> Union[
            str,                   # Regex
            PositionalFilterType,  # positional
            list[str]]:            # combi-search
        if not config.get(ConfigOptions.TEXT_FILTER.value):
            return InputManager.request_text_filter(config)
        return cast(Union[str, PositionalFilterType, list[str]], config[ConfigOptions.TEXT_FILTER.value])

    @staticmethod
    def set_should_slice_clusters(config: Initialized) -> bool:
        if config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value) is None:  # False is a valid value
            response = InputManager.ask_open_question(
                'Do you want to compare only a subsection of the clusters (press enter to skip)? [yes/y]: ').lower()
            return response in YES_INPUT
        return cast(bool, config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value])

    @staticmethod
    def set_cluster_text(config: Initialized, config_option: str, position: str, src_or_ref: str) -> str:
        if not config.get(config_option):
            return InputManager.ask_open_question(
                f'Text in the {src_or_ref.lower()} cluster where the subsection should {position} (press enter to skip): ')
        return cast(str, config[config_option])

    @staticmethod
    def request_text_filter(config: Initialized) -> Union[
            str,                   # Regex
            PositionalFilterType,  # positional
            list[str]]:            # combi-search
        if config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.REGEX.value:
            return InputManager.ask_open_question('Please provide a regex filter: ')
        elif config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.POSITIONAL.value:
            separator_input = InputManager.ask_open_question('Please provide the separator for counting (default: 1 space character): ')
            positional_text_filter = PositionalFilterType(
                separator=separator_input if separator_input else ' ',
                line=int(InputManager.ask_open_question('Please provide the line number in the cluster: ')),
                occurrence=int(InputManager.ask_open_question('Please provide the occurrence number: ')))
            return positional_text_filter
        elif config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.COMBI_SEARCH.value:
            combi_search_filters: list[str] = []
            index = 1
            while True:
                combi_search_filters.append(InputManager.ask_open_question('Please provide a regex filter for search {0}: '.format(index)))
                index += 1
                if InputManager.ask_open_question('Do you wish to provide a next search parameter [yes/y]: ').lower() not in YES_INPUT:
                    break
            return combi_search_filters
        else:
            raise ValueError('Unsupported filter type: %s' % config.get(ConfigOptions.TEXT_FILTER_TYPE.value))

    @staticmethod
    def ask_open_question(prompt: str) -> str:
        return input(prompt)

    @staticmethod
    def ask_mpc_question(prompt: str, options: list[str]) -> str:
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
    def __init__(self, output_directory: Optional[str] = None, should_print_results: bool = True) -> None:
        self.output_directory = output_directory
        self.should_print_results = should_print_results

    def process(self,
                results: dict[str, list[Entry]],
                root: str,
                file_name: str = 'result',
                is_comparison: bool = False
                ) -> None:

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
            if self.output_directory:
                output_path = self._create_output_path(group, root, file_name=file_name)
                utils.write_to_txt_file(ascii_tables, output_path + '.txt')
                utils.write_to_json_file(entries, output_path + '.json')

    def _create_output_path(self, group: str, root: str, file_name: str = 'result') -> str:
        root_path = os.path.basename(os.path.normpath(root))
        root_path_without_extension = os.path.splitext(root_path)[0]
        group_dir = os.path.join(
            cast(str, self.output_directory),  # this function is only called when output_directory is set
            root_path_without_extension,
            group)
        return os.path.join(group_dir, file_name)
