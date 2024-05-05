from enum import Enum
import re


class Extractor():
    def __init__(self):
        self.cluster_filter = None
        self.text_filter = {
            'filter_type': None,
            'filter': None
        }

    class TextFilterTypes(Enum):
        REGEX = 1
        KEYWORD = 2
        POSITIONAL = 3
        SPLIT_KEYWORDS = 4

    def extract_from_data(self, data):
        clusters = self.get_clusters(data)
        if self.text_filter['filter_type'] == self.TextFilterTypes(1):
            return self.extract_text_from_clusters_by_regex(clusters)
        else:
            raise ValueError('Unsupported filter type: %s' % self.text_filter['filter_type'].name)

    def get_clusters(self, data):
        return data.split(self.cluster_filter)

    def extract_text_from_clusters_by_regex(self, clusters):
        filtered_text = []
        for cluster in clusters:
            search_result = re.search(self.text_filter['filter'], cluster)
            if search_result is not None:
                filtered_text.append(search_result.group(1))
        return filtered_text

    def request_cluster_filter(self):
        self.cluster_filter = input('Please indicate the character(s) to split text clusters on: ').replace('\\n', '\n')

    def request_text_filter(self):
        self.text_filter['filter_type'] = self.request_text_filter_type()

        if self.text_filter['filter_type'] == self.TextFilterTypes(1):
            self.text_filter['filter'] = input('Please provide a regex filter: ')
        else:
            raise ValueError('Unsupported filter type: %s' % self.text_filter['filter_type'].name)

        # TODO: continue implementation of following filter types
        # elif self.text_filter['filter_type'] == self.TextFilterTypes(2):
        #      self.text_filter['filter'] = input('Please provide a keyword filter: ')

        # elif self.text_filter['filter_type'] == self.TextFilterTypes(3):
        #      self.text_filter['filter'] = {'line': None, 'word': None}
        #      self.text_filter['filter']['line'] = int(input('Please provide the line number in the cluster: '))
        #      self.text_filter['filter']['word'] = int(input('Please provide the word number on the line: '))

        # elif self.text_filter['filter_type'] == self.TextFilterTypes(4):
        #      self.text_filter['filter'] = {'start_split': None, 'end_split': None}
        #      self.text_filter['filter']['start_split'] = input('Please provide a keyword after which to filter: ')
        #      self.text_filter['filter']['end_split'] = input('Please provide a keyword to end the filter: ')

    def request_text_filter_type(self):
        return self.TextFilterTypes(
            int(input('Please choose a filter type (1-4):\n' +
                      '1. Regex\n' +
                      '2. Keyword (not yet supported)\n' +
                      '3. Positional (not yet supported)\n' +
                      '4. Split-keywords (not yet supported)\n')))


class Comparer():
    def __init__(self, source, reference):
        self.source = source
        self.reference = reference
        self.unique_elements = set(self.source + self.reference)

    def compare(self):
        src, ref = self.create_data_structures()
        return self.get_differences(src, ref)

    def create_data_structures(self):
        source_data_structure, reference_data_structure = dict(), dict()
        for element in self.unique_elements:
            source_data_structure[element] = self.source.count(element)
            reference_data_structure[element] = self.reference.count(element)
        return source_data_structure, reference_data_structure

    def get_differences(self, src, ref):
        differences = dict()
        for element in self.unique_elements:
            diff = src[element] - ref[element]
            differences[element] = {
                # 'value': element,
                'source': src[element],
                'reference': ref[element],
                'difference': diff}
        return differences
