"""Module for maintaining the specs of the program execution."""

from enum import Enum, IntEnum
from dataclasses import dataclass


class MetaData(Enum):
    """Metadata for GenEC."""

    TOOL = 'GenEC'
    VERSION = '1.0.0'
    REPOSITORY = 'https://github.com/RemyKroese/GenEC'
    AUTHOR = 'Remy Kroese'


@dataclass
class PositionalFilterType:
    """
    Represents a positional filter used to extract text based on line and occurrence.

    This filter allows extracting a specific occurrence of a separator on a given line
    from a text cluster.

    Attributes
    ----------
    separator : str
        The character(s) used to split the text for positional extraction.
    line : int
        The line number in the cluster from which to extract text (1-based indexing).
    occurrence : int
        The occurrence index of the separator on the specified line to extract.
    """

    separator: str
    line: int
    occurrence: int


class FileID(IntEnum):
    """
    Enum representing file roles in a comparison workflow.

    Attributes
    ----------
    SOURCE : int
        Indicates the source file.
    REFERENCE : int
        Indicates the reference file.
    """

    SOURCE = 1
    REFERENCE = 2


class Workflows(Enum):
    """
    Enum representing supported workflow types in GenEC.

    Attributes
    ----------
    BASIC : str
        A simple workflow with default settings.
    PRESET : str
        Workflow using a single preset configuration.
    PRESET_LIST : str
        Workflow using multiple preset configurations.
    """

    BASIC = 'basic'
    PRESET = 'preset'
    PRESET_LIST = 'preset-list'


class ConfigOptions(Enum):
    """
    Enum representing configuration options keys for GenEC.

    Attributes
    ----------
    CLUSTER_FILTER : str
        Key for cluster splitting filter.
    TEXT_FILTER_TYPE : str
        Key for the type of text filter.
    TEXT_FILTER : str
        Key for the actual text filter.
    SHOULD_SLICE_CLUSTERS : str
        Key indicating whether clusters should be sliced.
    SRC_START_CLUSTER_TEXT : str
        Key for source cluster start text.
    SRC_END_CLUSTER_TEXT : str
        Key for source cluster end text.
    REF_START_CLUSTER_TEXT : str
        Key for reference cluster start text.
    REF_END_CLUSTER_TEXT : str
        Key for reference cluster end text.
    """

    CLUSTER_FILTER = 'cluster_filter'
    TEXT_FILTER_TYPE = 'text_filter_type'
    TEXT_FILTER = 'text_filter'
    SHOULD_SLICE_CLUSTERS = 'should_slice_clusters'
    SRC_START_CLUSTER_TEXT = 'src_start_cluster_text'
    SRC_END_CLUSTER_TEXT = 'src_end_cluster_text'
    REF_START_CLUSTER_TEXT = 'ref_start_cluster_text'
    REF_END_CLUSTER_TEXT = 'ref_end_cluster_text'


class TextFilterTypes(Enum):
    """
    Enum representing supported text filter types in GenEC.

    Attributes
    ----------
    REGEX : str
        Filter using a regular expression.
    POSITIONAL : str
        Filter using a positional extraction method.
    REGEX_LIST : str
        Filter using a list of regular expressions applied sequentially.
    KEYWORD : str
        Keyword-based filter (currently unsupported).
    SPLIT_KEYWORDS : str
        Split-keywords filter (currently unsupported).
    """

    REGEX = 'Regex'
    POSITIONAL = 'Positional'
    REGEX_LIST = 'Regex-list'
    KEYWORD = 'Keyword_UNSUPPORTED'
    SPLIT_KEYWORDS = 'Split-keywords_UNSUPPORTED'
