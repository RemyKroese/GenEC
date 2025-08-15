"""Module for extracting and comparing output data from raw input data."""

from typing import Optional

from GenEC import utils
from GenEC.core import extraction_filters, FileID, ConfigOptions, TextFilterTypes
from GenEC.core.types.preset_config import Finalized
from GenEC.core.types.output import DataCompare


class Extractor:
    """
    Extract meaningful output data from raw input data.

    Supports optional slicing of clusters based on start and end keywords and
    applies text filtering as specified in the provided configuration.
    """

    def extract_from_data(self, config: Finalized, data: str, file: int) -> list[str]:
        """
        Extract processed results from raw data using the provided configuration.

        Parameters
        ----------
        config : Finalized
            The finalized configuration object containing extraction and filtering options.
        data : str
            The raw text data to extract output data from.
        file : int
            Identifier for the type of file (e.g., source or reference) to
            apply any file-specific slicing.

        Returns
        -------
        list[str]
            A list of output data.

        Raises
        ------
        ValueError
            If the configuration specifies an unsupported text filter type.
        """
        clusters = self.get_clusters(config, data, file)
        filter_type = config.get(ConfigOptions.TEXT_FILTER_TYPE.value)
        if filter_type not in [t.value for t in TextFilterTypes] or 'UNSUPPORTED' in filter_type:
            raise ValueError(
                f"Unsupported filter type: {config.get(ConfigOptions.TEXT_FILTER_TYPE.value)}"
            )
        extractor = extraction_filters.get_extractor(filter_type, config)
        return extractor.extract(clusters)

    def get_clusters(self, config: Finalized, data: str, file: int) -> list[str]:
        """
        Split raw text data into clusters according to the configuration.

        Optionally slices clusters using start and end keywords based on file type.

        Parameters
        ----------
        config : Finalized
            Configuration containing cluster filters and slicing options.
        data : str
            Raw text data to split into clusters.
        file : int
            Identifier for the type of file (source or reference) to
            determine start and end keywords for slicing.

        Returns
        -------
        list[str]
            A list of text clusters, optionally sliced based on keywords.
        """
        clusters = data.split(config.get(ConfigOptions.CLUSTER_FILTER.value))
        if config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value):
            if file == FileID.SOURCE:
                start_keyword = config.get(ConfigOptions.SRC_START_CLUSTER_TEXT.value)
                end_keyword = config.get(ConfigOptions.SRC_END_CLUSTER_TEXT.value)
            else:
                start_keyword = config.get(ConfigOptions.REF_START_CLUSTER_TEXT.value)
                end_keyword = config.get(ConfigOptions.REF_END_CLUSTER_TEXT.value)
            return self.get_sliced_clusters(clusters, start_keyword, end_keyword)
        return clusters

    def get_sliced_clusters(
        self, clusters: list[str], start_keyword: Optional[str] = None, end_keyword: Optional[str] = None
    ) -> list[str]:
        """
        Return a subset of clusters bounded by start and end keywords.

        Parameters
        ----------
        clusters : list[str]
            List of text clusters to slice.
        start_keyword : Optional[str], optional
            Keyword indicating the start of the slice. If None, slicing starts at the first cluster.
        end_keyword : Optional[str], optional
            Keyword indicating the end of the slice. If None, slicing ends at the last cluster.

        Returns
        -------
        list[str]
            Sliced list of clusters between start and end keywords.
            If keywords are not found, returns the full list or relevant subset.
        """
        start_cluster_index = 0
        end_cluster_index = len(clusters) - 1

        if start_keyword:
            start_cluster_index = next(
                (i for i, cluster in enumerate(clusters) if start_keyword in cluster),
                start_cluster_index,
            )

        if end_keyword:
            end_cluster_index = next(
                (i for i, cluster in enumerate(clusters[start_cluster_index:], start=start_cluster_index)
                 if end_keyword in cluster),
                end_cluster_index,
            )

        return clusters[start_cluster_index:end_cluster_index + 1]


class Comparer:
    """
    Compare two sets of extracted output data (source and reference).

    Computes occurrence counts for each element in both sets and calculates
    differences between source and reference counts.
    """

    def __init__(self, source: list[str], reference: list[str]) -> None:
        """
        Initialize the comparer with source and reference data.

        Parameters
        ----------
        source : list[str]
            Extracted data from the source text.
        reference : list[str]
            Extracted data from the reference text.
        """
        self.source_counts = utils.get_list_each_element_count(source)
        self.reference_counts = utils.get_list_each_element_count(reference)
        self.unique_elements = set(self.source_counts.keys()).union(self.reference_counts.keys())

    def compare(self) -> dict[str, DataCompare]:
        """
        Compare source and reference data and compute differences.

        Returns
        -------
        dict[str, DataCompare]
            Dictionary where keys are unique elements and values are dictionaries
            containing 'source' count, 'reference' count, and 'difference'.
        """
        differences: dict[str, DataCompare] = {}
        for element in self.unique_elements:
            src_count = self.source_counts.get(element, 0)
            ref_count = self.reference_counts.get(element, 0)
            differences[element] = {
                'source': src_count,
                'reference': ref_count,
                'difference': src_count - ref_count,
            }
        return differences
