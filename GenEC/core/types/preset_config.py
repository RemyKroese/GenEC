"""Type hinting support for configuration data."""

from typing import Optional, TypedDict, Union
from GenEC.core.specs import PositionalFilterType


class Initialized(TypedDict):
    """
    Represents a configuration dictionary with optional values during initialization.

    This dictionary is used to store user-provided or default values before all
    configuration options are finalized. Some fields may start out as None and
    are filled in later through user input or default logic.

    Parameters
    ----------
    TypedDict : type
        Base class for creating typed dictionaries in Python.
    """

    cluster_filter: Optional[str]
    text_filter_type: Optional[str]
    text_filter: Optional[Union[str, list[str], PositionalFilterType]]
    should_slice_clusters: Optional[bool]
    src_start_cluster_text: Optional[str]
    src_end_cluster_text: Optional[str]
    ref_start_cluster_text: Optional[str]
    ref_end_cluster_text: Optional[str]


class Finalized(TypedDict):
    """
    Represents a fully populated configuration dictionary.

    This dictionary contains all required configuration options after user input
    or default logic has been applied. All fields are guaranteed to be filled
    except for optional cluster boundary texts.

    Parameters
    ----------
    TypedDict : type
        Base class for creating typed dictionaries in Python.
    """

    cluster_filter: str
    text_filter_type: str
    text_filter: Union[str, list[str], PositionalFilterType]
    should_slice_clusters: bool
    src_start_cluster_text: Optional[str]
    src_end_cluster_text: Optional[str]
    ref_start_cluster_text: Optional[str]
    ref_end_cluster_text: Optional[str]
