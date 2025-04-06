from collections import Counter
import re

from GenEC.core import FileID, ConfigOptions, TextFilterTypes


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
            if file == FileID.SOURCE:
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
