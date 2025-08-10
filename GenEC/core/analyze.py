from typing import Optional

from GenEC import utils
from GenEC.core import extraction_filters, PresetConfigFinalized, FileID, ConfigOptions, TextFilterTypes


class Extractor:
    def extract_from_data(self, config: PresetConfigFinalized, data: str, file: int) -> list[str]:
        clusters = self.get_clusters(config, data, file)
        filter_type = config.get(ConfigOptions.TEXT_FILTER_TYPE.value)
        if filter_type not in [t.value for t in TextFilterTypes] or 'UNSUPPORTED' in filter_type:
            raise ValueError("Unsupported filter type: %s" % config.get(ConfigOptions.TEXT_FILTER_TYPE.value))
        extractor = extraction_filters.get_extractor(filter_type, config)
        return extractor.extract(clusters)

    def get_clusters(self, config: PresetConfigFinalized, data: str, file: int) -> list[str]:
        clusters = data.split(config.get(ConfigOptions.CLUSTER_FILTER.value))
        if config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value):
            if file == FileID.SOURCE:
                start_keyword = config.get(ConfigOptions.SRC_START_CLUSTER_TEXT.value)
                end_keyword = config.get(ConfigOptions.SRC_END_CLUSTER_TEXT.value)
            else:
                start_keyword = config.get(ConfigOptions.REF_START_CLUSTER_TEXT.value)
                end_keyword = config.get(ConfigOptions.REF_END_CLUSTER_TEXT.value)
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
