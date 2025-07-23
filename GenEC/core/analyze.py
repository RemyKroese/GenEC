import re
from typing import cast, Optional

from GenEC import utils
from GenEC.core import PresetConfigFinalized, PositionalFilterType, FileID, ConfigOptions, TextFilterTypes


class Extractor:
    def __init__(self, config: PresetConfigFinalized) -> None:
        self.config = config

    def extract_from_data(self, data: str, file: int) -> list[str]:
        clusters = self.get_clusters(data, file)
        if self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.REGEX.value:
            return self.extract_text_from_clusters_by_regex(clusters)
        elif self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.POSITIONAL.value:
            return self.extract_text_from_clusters_by_position(clusters)
        elif self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value) == TextFilterTypes.COMBI_SEARCH.value:
            return self.extract_text_from_clusters_by_combi_search(clusters)
        else:
            raise ValueError("Unsupported filter type: %s" % self.config.get(ConfigOptions.TEXT_FILTER_TYPE.value))

    def get_clusters(self, data: str, file: int) -> list[str]:
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

    def get_sliced_clusters(self, clusters: list[str], start_keyword: Optional[str] = '', end_keyword: Optional[str] = '') -> list[str]:
        start_cluster_index = 0
        end_cluster_index = len(clusters) - 1

        if start_keyword:
            start_cluster_index = next((i for i, cluster in enumerate(clusters)
                                        if start_keyword in cluster), start_cluster_index)

        if end_keyword:
            end_cluster_index = next((i for i, cluster in enumerate(
                clusters[start_cluster_index:], start=start_cluster_index)
                if end_keyword in cluster), end_cluster_index)

        return clusters[start_cluster_index:end_cluster_index+1]

    def extract_text_from_clusters_by_regex(self, clusters: list[str], regex_pattern: Optional[str] = None) -> list[str]:
        regex_pattern = regex_pattern if regex_pattern else cast(str, self.config.get(ConfigOptions.TEXT_FILTER.value))
        if not isinstance(regex_pattern, str):  # type: ignore[unnecessary-isinstance]
            # Regex pattern should always be a string due to input_manager logic, so there will be a bug if this error is raised
            raise TypeError('Incorrect text filter type for regex, expected a regex pattern.')
        pattern = re.compile(regex_pattern)

        filtered_text: list[str] = []
        for cluster in clusters:
            search_result = pattern.search(cluster)
            if search_result:
                groups = search_result.groups()
                text_output = ' | '.join(groups) if groups else search_result.group(0)
                filtered_text.append(text_output)
        return filtered_text

    def extract_text_from_clusters_by_position(self, clusters: list[str]) -> list[str]:
        position_filter = cast(PositionalFilterType, self.config.get(ConfigOptions.TEXT_FILTER.value))
        print(type(position_filter))
        if not isinstance(position_filter, PositionalFilterType):  # type: ignore[unnecessary-isinstance]
            # Regex pattern should always be a string due to input_manager logic, so there will be a bug if this error is raised
            raise TypeError('Incorrect text filter type for positional, expected a separator string, line number, and occurrence number.')

        filtered_text: list[str] = []
        for cluster in clusters:
            try:
                line = cluster.split('\n')[position_filter.line-1]
                filtered_text.append(line.split(position_filter.separator)[position_filter.occurrence-1])
            except IndexError:  # Clusters that don't contain the search parameters are ignored altogether
                continue
        return filtered_text

    def extract_text_from_clusters_by_combi_search(self, clusters: list[str]) -> list[str]:
        '''Combi-search executes multiple user-defined regex searches, isolating only the relevant clusters for the final search'''
        text_filters = self.config.get(ConfigOptions.TEXT_FILTER.value)
        if not isinstance(text_filters, list):
            # Regex pattern should always be a string due to input_manager logic, so there will be a bug if this error is raised
            raise TypeError('Incorrect text filter type for Combi-Search, expected a list of regex patterns.')

        for text_filter in text_filters[:-1]:
            pattern = re.compile(text_filter)
            clusters = [cluster for cluster in clusters if pattern.search(cluster)]
        return self.extract_text_from_clusters_by_regex(clusters, text_filters[-1])


class Comparer:
    def __init__(self, source: list[str], reference: list[str]) -> None:
        self.source_counts = utils.get_list_each_element_count(source)
        self.reference_counts = utils.get_list_each_element_count(reference)
        self.unique_elements = set(self.source_counts.keys()).union(self.reference_counts.keys())

    def compare(self) -> dict[str, dict[str, int]]:
        differences: dict[str, dict[str, int]] = {}
        for element in self.unique_elements:
            src_count = self.source_counts.get(element, 0)
            ref_count = self.reference_counts.get(element, 0)
            differences[element] = {
                'source': src_count,
                'reference': ref_count,
                'difference': src_count - ref_count
            }
        return differences
