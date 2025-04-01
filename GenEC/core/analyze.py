from collections import Counter
from enum import Enum
import os
import re
import yaml


YES_INPUT = ['yes', 'y']
NO_INPUT = ['no', 'n']


class Files(Enum):
    SOURCE = 1
    REFERENCE = 2


class ConfigOptions(Enum):
    CLUSTER_FILTER = 'cluster_filter'
    TEXT_FILTER_TYPE = 'text_filter_type'
    TEXT_FILTER = 'text_filter'
    SHOULD_SLICE_CLUSTERS = 'should_slice_clusters'
    SRC_START_CLUSTER_TEXT = 'src_start_cluster_text'
    SRC_END_CLUSTER_TEXT = 'src_end_cluster_text'
    REF_START_CLUSTER_TEXT = 'ref_start_cluster_text'
    REF_END_CLUSTER_TEXT = 'ref_end_cluster_text'


class TextFilterTypes(Enum):
    REGEX = 'Regex'
    POSITIONAL = 'Positional'
    COMBI_SEARCH = 'Combi-search'
    KEYWORD = 'Keyword_UNSUPPORTED'
    SPLIT_KEYWORDS = 'Split-keywords_UNSUPPORTED'


class InputManager:
    PRESETS_DIR = os.path.join(os.path.dirname(__file__), '../presets')

    def __init__(self, preset_param: str = None):
        self.preset_file, self.preset_name = self.parse_preset_param(preset_param) if preset_param else (None, None)
        self.config = self.load_preset() if self.preset_file else {}

    @staticmethod
    def parse_preset_param(preset_param):
        if '/' not in preset_param:
            return preset_param, None
        else:
            return tuple(preset_param.split('/', 1))

    def load_preset(self):
        presets = self.load_presets_file()
        if not self.preset_name:
            if len(presets) == 1:
                self.preset_name = next(iter(presets))
            else:
                self.preset_name = self.ask_mpc_question('Please choose a preset:\n', list(presets.keys()))

        if self.preset_name not in presets:
            raise ValueError(f'preset {self.preset_name} not found in {self.preset_file}')

        return presets[self.preset_name]

    def load_presets_file(self):
        presets_file_path = os.path.join(self.PRESETS_DIR, self.preset_file) + '.yaml'
        if not os.path.exists(presets_file_path):
            raise FileNotFoundError(f'preset file {presets_file_path} not found.')

        with open(presets_file_path, 'r') as file:
            presets = yaml.safe_load(file)

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


class Extractor:
    def __init__(self, config):
        self.config = config

    def extract_from_data(self, data, file):
        clusters = self.get_clusters(data, file)
        if self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.REGEX.value:
            return self.extract_text_from_clusters_by_regex(clusters)
        elif self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.POSITIONAL.value:
            return self.extract_text_from_clusters_by_position(clusters)
        elif self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.COMBI_SEARCH.value:
            return self.extract_text_from_clusters_by_combi_search(clusters)
        else:
            raise ValueError("Unsupported filter type: %s" % self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value))

    def get_clusters(self, data, file):
        clusters = data.split(self.config.get(ConfigOptions.CLUSTER_FILTER.value))
        if self.config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value):
            if file == Files.SOURCE.value:
                start_keyword = self.config.get(ConfigOptions.SRC_START_CLUSTER_TEXT.value)
                end_keyword = self.config.get(ConfigOptions.SRC_END_CLUSTER_TEXT.value)
            else:
                start_keyword = self.config.get(ConfigOptions.REF_START_CLUSTER_TEXT.value)
                end_keyword = self.config.get(ConfigOptions.REF_END_CLUSTER_TEXT.value)
            return self.get_sliced_clusters(clusters, start_keyword, end_keyword)
        else:
            return clusters

    def get_sliced_clusters(self, clusters, start_keyword='', end_keyword=''):
        start_cluster_index = 0
        end_cluster_index = len(clusters) - 1

        if start_keyword:
            start_cluster_index = next((i for i, cluster in enumerate(clusters)
                                        if start_keyword in cluster), start_cluster_index)

        if end_keyword:
            end_cluster_index = next((i for i, cluster in enumerate(
                clusters[start_cluster_index:], start=start_cluster_index)
                if end_keyword in cluster), end_cluster_index)

        return (clusters[start_cluster_index:end_cluster_index+1])

    def extract_text_from_clusters_by_regex(self, clusters, regex_pattern=None):
        filtered_text = []
        pattern = re.compile(regex_pattern if regex_pattern else self.config.get(ConfigOptions.TEXT_FILTER.value))
        for cluster in clusters:
            search_result = pattern.search(cluster)
            if search_result:
                groups = search_result.groups()
                text_output = ' | '.join(groups) if groups else search_result.group(0)
                filtered_text.append(text_output)
        return filtered_text

    def extract_text_from_clusters_by_position(self, clusters):
        position_filter = self.config.get(ConfigOptions.TEXT_FILTER.value)
        filtered_text = []
        for cluster in clusters:
            try:
                line = cluster.split('\n')[position_filter['line']-1]
                filtered_text.append(line.split(position_filter['separator'])[position_filter['occurrence']-1])
            except IndexError:  # Clusters that don't contain the search parameters are ignored altogether
                continue
        return filtered_text

    def extract_text_from_clusters_by_combi_search(self, clusters):
        '''Combi-search executes multiple user-defined regex searches, isolating only the relevant clusters for the final search'''
        filters = self.config.get(ConfigOptions.TEXT_FILTER.value)
        for filter in filters[:-1]:
            pattern = re.compile(filter)
            clusters = [cluster for cluster in clusters if pattern.search(cluster)]
        return self.extract_text_from_clusters_by_regex(clusters, filters[-1])


class Comparer:
    def __init__(self, source, reference):
        self.source = source
        self.reference = reference
        self.source_counter = Counter(source)
        self.reference_counter = Counter(reference)
        self.unique_elements = set(self.source_counter.keys()).union(self.reference_counter.keys())

    def compare(self):
        differences = {}
        for element in self.unique_elements:
            src_count = self.source_counter.get(element, 0)
            ref_count = self.reference_counter.get(element, 0)
            differences[element] = {
                'source': src_count,
                'reference': ref_count,
                'difference': src_count - ref_count
            }
        return differences
