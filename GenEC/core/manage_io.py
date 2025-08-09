from collections import defaultdict
import os
from typing import Optional, Union

from GenEC import utils
from GenEC.core import PresetConfigFinalized, PresetConfigInitialized, PositionalFilterType, ConfigOptions, TextFilterTypes, AnalysisConstruct


YES_INPUT = ['yes', 'y']
NO_INPUT = ['no', 'n']


class InputManager:
    @staticmethod
    def normalize_cluster_filter(cluster_filter: Optional[str]) -> str:
        if not cluster_filter:
            return '\n'
        return cluster_filter.encode('utf-8').decode('unicode_escape')

    def __init__(self, preset_param: Optional[dict[str, str]] = None, presets_directory: Optional[str] = None) -> None:
        self.presets_directory = presets_directory if presets_directory else os.path.join(os.path.dirname(__file__), '../presets')
        self.preset_file = ''
        self.preset_name = ''
        self.analysis_constructs: list[AnalysisConstruct] = []
        self.config = PresetConfigInitialized(
            cluster_filter=None,
            text_filter_type=None,
            text_filter=None,
            should_slice_clusters=None,
            src_start_cluster_text=None,
            source_end_cluster_text=None,
            ref_start_cluster_text=None,
            ref_end_cluster_text=None
        )

        if preset_param:
            if preset_param['type'] == 'preset':
                self.preset_file, self.preset_name = self.parse_preset_param(preset_param['value'])
                self.config = self.load_preset()
            elif preset_param['type'] == 'preset-list':
                self.analysis_constructs.extend(self.load_presets(preset_param['value']))
            else:
                raise ValueError(f"{preset_param['type']} is not a valid preset parameter type.")

    @staticmethod
    def parse_preset_param(preset_param: str) -> tuple[str, Optional[str]]:
        if '/' not in preset_param:
            return preset_param, None
        else:
            return tuple(preset_param.split('/', 1))  # type: ignore[return-value]  # Always returns 2 items

    def load_presets(self, presets_list_file_name: str) -> list[AnalysisConstruct]:
        presets_list_file_path = os.path.join(self.presets_directory, presets_list_file_name + '.yaml')
        presets_list = utils.read_yaml_file(presets_list_file_path)
        presets_per_file = self._group_presets_by_file(presets_list)
        return self._collect_presets(presets_per_file)

    def _group_presets_by_file(self, presets_list: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
        presets_per_target: dict[str, list[dict[str, str]]] = defaultdict(list)
        for entry in presets_list:
            target_file = entry.get('target', '')
            preset = entry.get('preset', '')
            if not preset:
                print(f'Preset missing in entry: {entry}')
                continue
            file_name, preset_name = self.parse_preset_param(preset)
            if not preset_name:
                print(f'Preset name missing in entry: {entry}')
                continue
            presets_per_target[target_file].append({
                'preset_file': file_name,
                'preset_name': preset_name,
                'target_file': target_file
            })
        return presets_per_target

    def _collect_presets(self, presets_per_target: dict[str, list[dict[str, str]]]) -> list[AnalysisConstruct]:
        presets: list[AnalysisConstruct] = []
        for target_file, preset_entries in presets_per_target.items():
            for entry in preset_entries:
                file_name = entry['preset_file']
                preset_name = entry['preset_name']
                loaded_presets = self.load_preset_file(file_name)
                if preset_name in loaded_presets:
                    config = loaded_presets[preset_name]
                    # Normalize cluster_filter using utility
                    config[ConfigOptions.CLUSTER_FILTER.value] = self.normalize_cluster_filter(config.get(ConfigOptions.CLUSTER_FILTER.value))
                    finalized_config = self._finalize_config(config)
                    presets.append(
                        AnalysisConstruct(
                            preset=file_name + '/' + preset_name,
                            config=finalized_config,
                            target_file=target_file
                        )
                    )
                else:
                    print(f'preset {preset_name} not found in {file_name}. Skipping...')
        if not presets:
            raise ValueError('None of the provided presets were found.')
        return presets

    def load_preset(self) -> PresetConfigInitialized:
        presets = self.load_preset_file(self.preset_file)
        if not self.preset_name:
            if len(presets) == 1:
                self.preset_name = next(iter(presets))
            else:
                self.preset_name = self.ask_mpc_question('Please choose a preset:\n', list(presets.keys()))

        if self.preset_name not in presets:
            raise ValueError(f'preset {self.preset_name} not found in {self.preset_file}')

        return presets[self.preset_name]

    def load_preset_file(self, preset_file: str):
        presets_file_path = os.path.join(self.presets_directory, preset_file + '.yaml')
        presets = utils.read_yaml_file(presets_file_path)

        if not presets or len(presets) == 0:
            raise ValueError(f'presets file {presets_file_path} does not contain any presets')

        return presets

    def set_config(self, preset: str, target_file: str = '') -> None:  # pragma: no cover
        self.set_cluster_filter()
        self.set_text_filter_type()
        self.set_text_filter()
        self.set_should_slice_clusters()

        if self.config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value):
            self.set_cluster_text(ConfigOptions.SRC_START_CLUSTER_TEXT.value, 'start', 'SRC')
            self.set_cluster_text(ConfigOptions.SRC_END_CLUSTER_TEXT.value, 'end', 'SRC')
            self.set_cluster_text(ConfigOptions.REF_START_CLUSTER_TEXT.value, 'start', 'REF')
            self.set_cluster_text(ConfigOptions.REF_END_CLUSTER_TEXT.value, 'end', 'REF')

        self.analysis_constructs.append(AnalysisConstruct(preset, self._finalize_config(self.config), target_file))

    def _finalize_config(self, config: PresetConfigInitialized) -> PresetConfigFinalized:  # pragma: no cover
        text_filter = config.get('text_filter')
        if text_filter is None:
            text_filter = ''
        return PresetConfigFinalized(
            cluster_filter=config.get('cluster_filter') or '',
            text_filter_type=config.get('text_filter_type') or '',
            text_filter=text_filter,
            should_slice_clusters=bool(config.get('should_slice_clusters')),
            src_start_cluster_text=config.get('src_start_cluster_text'),
            source_end_cluster_text=config.get('source_end_cluster_text'),
            ref_start_cluster_text=config.get('ref_start_cluster_text'),
            ref_end_cluster_text=config.get('ref_end_cluster_text')
        )

    def set_cluster_filter(self) -> None:
        if not self.config.get(ConfigOptions.CLUSTER_FILTER.value):
            input_string = self.ask_open_question(
                'Please indicate the character(s) to split text clusters on (Default: Newline [\\n]): ')
        else:
            input_string = self.config.get(ConfigOptions.CLUSTER_FILTER.value)
        self.config[ConfigOptions.CLUSTER_FILTER.value] = self.normalize_cluster_filter(input_string)

    def set_text_filter_type(self) -> None:
        if not self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value):
            self.config[ConfigOptions.TEXT_FILTER_TYPE.value] = self.ask_mpc_question(
                'Please choose a filter type:\n', [t.value for t in TextFilterTypes])

    def set_text_filter(self) -> None:
        if not self.config.get(ConfigOptions.TEXT_FILTER.value):
            self.config[ConfigOptions.TEXT_FILTER.value] = self.request_text_filter()

    def set_should_slice_clusters(self) -> None:
        if self.config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value) is None:  # False is a valid value
            response = self.ask_open_question(
                'Do you want to compare only a subsection of the clusters (press enter to skip)? [yes/y]: ').lower()
            self.config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] = response in YES_INPUT

    def set_cluster_text(self, config_option: str, position: str, src_or_ref: str) -> None:
        if not self.config.get(config_option):
            self.config[config_option] = self.ask_open_question(
                f'Text in the {src_or_ref.lower()} cluster where the subsection should {position} (press enter to skip): ')

    def request_text_filter(self) -> Union[
            str,                   # Regex
            PositionalFilterType,  # positional
            list[str]]:            # combi-search
        if self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.REGEX.value:
            return self.ask_open_question('Please provide a regex filter: ')
        elif self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.POSITIONAL.value:
            separator_input = self.ask_open_question('Please provide the separator for counting (default: 1 space character): ')
            positional_text_filter = PositionalFilterType(
                separator=separator_input if separator_input else ' ',
                line=int(self.ask_open_question('Please provide the line number in the cluster: ')),
                occurrence=int(self.ask_open_question('Please provide the occurrence number: ')))
            return positional_text_filter
        elif self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.COMBI_SEARCH.value:
            combi_search_filters: list[str] = []
            index = 1
            while True:
                combi_search_filters.append(self.ask_open_question('Please provide a regex filter for search {0}: '.format(index)))
                index += 1
                if self.ask_open_question('Do you wish to provide a next search parameter [yes/y]: ').lower() not in YES_INPUT:
                    break
            return combi_search_filters
        else:
            raise ValueError('Unsupported filter type: %s' % self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value))

        # TODO: continue implementation of following filter types
        # elif self.text_filter['filter_type'] == self.TextFilterTypes.KEYWORD:
        #      self.text_filter['filter'] = input('Please provide a keyword filter: ')

        # elif self.text_filter['filter_type'] == self.TextFilterTypes.SPLIT_KEYWORDS:
        #      self.text_filter['filter'] = {'start_split': None, 'end_split': None}
        #      self.text_filter['filter']['start_split'] = input('Please provide a keyword after which to filter: ')
        #      self.text_filter['filter']['end_split'] = input('Please provide a keyword to end the filter: ')

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
                results: dict[str, dict[str, int]],
                file_name: str = 'results',
                is_comparison: bool = False
                ) -> None:
        if is_comparison:
            ascii_table = utils.create_comparison_ascii_table(results)
        else:
            ascii_table = utils.create_extraction_ascii_table(results)
        if self.should_print_results:
            print(ascii_table)
        if self.output_directory:
            utils.write_to_txt_file(ascii_table, os.path.join(self.output_directory, file_name + '.txt'))
            utils.write_to_json_file(results, os.path.join(self.output_directory,  file_name + '.json'))
