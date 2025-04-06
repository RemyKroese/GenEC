from collections import defaultdict
import os

from GenEC import utils
from GenEC.core import ConfigOptions, TextFilterTypes


YES_INPUT = ['yes', 'y']
NO_INPUT = ['no', 'n']


class InputManager:
    PRESETS_DIR = os.path.join(os.path.dirname(__file__), '../presets')

    def __init__(self, preset_param=None):
        self.preset_file = self.preset_name = None
        self.config = {}
        if preset_param:
            if preset_param['type'] == 'preset':
                self.preset_file, self.preset_name = self.parse_preset_param(preset_param['value'])
                self.config = self.load_preset()
            elif preset_param['type'] == 'preset-list':
                self.presets = self.load_preset_list()
            else:
                raise ValueError(f"{preset_param['type']} is not a valid preset parameter type.")

    @staticmethod
    def parse_preset_param(preset_param):
        if '/' not in preset_param:
            return preset_param, None
        else:
            return tuple(preset_param.split('/', 1))

    def load_preset_list(self, preset_list_file):
        preset_list_construction = utils.read_yaml_file(os.path.join(self.PRESETS_DIR, preset_list_file + '.yaml'))

        presets_list = defaultdict(list)
        for entry in preset_list_construction['presets']:
            file_name, preset_name = self.parse_preset_param(entry)
            presets_list[file_name].append(preset_name)
        self.presets = self.load_presets(presets_list)

    def load_presets(self, presets_list):
        presets = {}
        for file_name, preset_names in presets_list.items():
            loaded_presets = self.load_preset_file(file_name)
            for preset_name in preset_names:
                if preset_name in loaded_presets:
                    presets[file_name + '/' + preset_name] = loaded_presets[preset_name]
                else:
                    print(f'preset {preset_name} not found in {file_name}. Skipping...')
        if not presets:
            raise ValueError('None of the provided presets were found.')
        return presets

    def load_preset(self):
        presets = self.load_preset_file()
        if not self.preset_name:
            if len(presets) == 1:
                self.preset_name = next(iter(presets))
            else:
                self.preset_name = self.ask_mpc_question('Please choose a preset:\n', list(presets.keys()))

        if self.preset_name not in presets:
            raise ValueError(f'preset {self.preset_name} not found in {self.preset_file}')

        return presets[self.preset_name]

    def load_preset_file(self):
        presets_file_path = os.path.join(self.PRESETS_DIR, self.preset_file + '.yaml')
        presets = utils.read_yaml_file(presets_file_path)

        if not presets or len(presets) == 0:
            raise ValueError(f'presets file {presets_file_path} does not contain any presets')

        return presets

    def set_config(self):  # pragma: no cover
        self.set_cluster_filter()
        self.set_text_filter_type()
        self.set_text_filter()
        self.set_should_slice_clusters()

        if self.config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value):
            self.set_cluster_text(ConfigOptions.SRC_START_CLUSTER_TEXT.value, 'start', 'SRC')
            self.set_cluster_text(ConfigOptions.SRC_END_CLUSTER_TEXT.value, 'end', 'SRC')
            self.set_cluster_text(ConfigOptions.REF_START_CLUSTER_TEXT.value, 'start', 'REF')
            self.set_cluster_text(ConfigOptions.REF_END_CLUSTER_TEXT.value, 'end', 'REF')

    def set_cluster_filter(self):
        if not self.config.get(ConfigOptions.CLUSTER_FILTER.value):
            input_string = self.ask_open_question(
                'Please indicate the character(s) to split text clusters on (Default: Newline [\\n]): ')
        else:
            input_string = self.config.get(ConfigOptions.CLUSTER_FILTER.value)
        self.config[ConfigOptions.CLUSTER_FILTER.value] = input_string.replace('\\n', '\n') if input_string else '\n'

    def set_text_filter_type(self):
        if not self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value):
            self.config[ConfigOptions.TEXT_FILTER_TYPE.value] = self.ask_mpc_question(
                'Please choose a filter type:\n', [t.value for t in TextFilterTypes])

    def set_text_filter(self):
        if not self.config.get(ConfigOptions.TEXT_FILTER.value):
            self.config[ConfigOptions.TEXT_FILTER.value] = self.request_text_filter()

    def set_should_slice_clusters(self):
        if self.config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value) is None:  # False is a valid value
            response = self.ask_open_question(
                'Do you want to compare only a subsection of the clusters (press enter to skip)? [yes/y]: ').lower()
            self.config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] = response in YES_INPUT

    def set_cluster_text(self, config_option, position, src_or_ref):
        if not self.config.get(config_option):
            self.config[config_option] = self.ask_open_question(
                f'Text in the {src_or_ref.lower()} cluster where the subsection should {position} (press enter to skip): ')

    def request_text_filter(self):
        if self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.REGEX.value:
            return self.ask_open_question('Please provide a regex filter: ')
        elif self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.POSITIONAL.value:
            separator_input = self.ask_open_question('Please provide the separator for counting (default: 1 space character): ')
            positional_text_filter = {'separator': separator_input if separator_input else ' ',
                                      'line': int(self.ask_open_question('Please provide the line number in the cluster: ')),
                                      'occurrence': int(self.ask_open_question('Please provide the occurrence number: '))}
            return positional_text_filter
        elif self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.COMBI_SEARCH.value:
            combi_search_filters = []
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
    def ask_open_question(prompt):
        return input(prompt)

    @staticmethod
    def ask_mpc_question(prompt, options):
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
    def get_user_choice(max_choice):
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
    def __init__(self, output_directory=None, should_print_results=True):
        self.output_directory = output_directory
        self.should_print_results = should_print_results

    def process(self, results, file_name='results'):
        ascii_table = utils.create_ascii_table(results)
        if self.should_print_results:
            print(ascii_table)
        if self.output_directory:
            utils.write_to_txt_file(ascii_table, os.path.join(self.output_directory, file_name + '.txt'))
            utils.write_to_json_file(results, os.path.join(self.output_directory,  file_name + '.json'))
