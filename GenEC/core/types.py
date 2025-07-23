from typing import Optional, TypedDict, Union
from GenEC.core.specs import PositionalFilterType


# Even though some values end up always filled in, they can start out empty in the logic
class PresetConfigInitialized(TypedDict):
    cluster_filter: Optional[str]
    text_filter_type: Optional[str]
    text_filter: Optional[Union[str, list[str], PositionalFilterType]]
    should_slice_clusters: Optional[bool]
    src_start_cluster_text: Optional[str]
    source_end_cluster_text: Optional[str]
    ref_start_cluster_text: Optional[str]
    ref_end_cluster_text: Optional[str]


class PresetConfigFinalized(TypedDict):
    cluster_filter: str
    text_filter_type: str
    text_filter: Union[str, list[str], PositionalFilterType]
    should_slice_clusters: bool
    src_start_cluster_text: Optional[str]
    source_end_cluster_text: Optional[str]
    ref_start_cluster_text: Optional[str]
    ref_end_cluster_text: Optional[str]
