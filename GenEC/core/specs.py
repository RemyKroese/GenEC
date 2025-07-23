from enum import Enum, IntEnum
from dataclasses import dataclass


@dataclass
class PositionalFilterType:
    separator: str
    line: int
    occurrence: int


class FileID(IntEnum):
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
