"""Type definitions for immutable configuration classes."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional, Union

from GenEC.core.specs import PositionalFilterType, TextFilterTypes


@dataclass(frozen=True)
class RegexConfiguration:
    """Configuration for regex-based text filtering.

    Immutable dataclass for regex pattern filtering.
    """

    cluster_filter: str
    should_slice_clusters: bool
    text_filter: str
    src_start_cluster_text: Optional[str] = None
    src_end_cluster_text: Optional[str] = None
    ref_start_cluster_text: Optional[str] = None
    ref_end_cluster_text: Optional[str] = None

    @property
    def filter_type(self) -> str:
        """Get the filter type for regex configuration.

        Returns
        -------
        str
            The regex filter type value
        """
        return TextFilterTypes.REGEX.value

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary for serialization.

        Returns
        -------
        dict[str, Any]
            Dictionary representation with text_filter_type instead of filter_type
        """
        # Maintain expected field order for consistency with legacy format
        result = {
            'cluster_filter': self.cluster_filter,
            'text_filter_type': self.filter_type,
            'text_filter': self.text_filter,
            'should_slice_clusters': self.should_slice_clusters,
            'src_start_cluster_text': self.src_start_cluster_text,
            'src_end_cluster_text': self.src_end_cluster_text,
            'ref_start_cluster_text': self.ref_start_cluster_text,
            'ref_end_cluster_text': self.ref_end_cluster_text
        }
        return result


@dataclass(frozen=True)
class RegexListConfiguration:
    """Configuration for regex list-based text filtering.

    Immutable dataclass for multiple regex patterns.
    """

    cluster_filter: str
    should_slice_clusters: bool
    text_filter: list[str]
    src_start_cluster_text: Optional[str] = None
    src_end_cluster_text: Optional[str] = None
    ref_start_cluster_text: Optional[str] = None
    ref_end_cluster_text: Optional[str] = None

    @property
    def filter_type(self) -> str:
        """Get the filter type for regex list configuration.

        Returns
        -------
        str
            The regex list filter type value
        """
        return TextFilterTypes.REGEX_LIST.value

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary for serialization.

        Returns
        -------
        dict[str, Any]
            Dictionary representation with text_filter_type instead of filter_type
        """
        # Maintain expected field order for consistency with legacy format
        result = {
            'cluster_filter': self.cluster_filter,
            'text_filter_type': self.filter_type,
            'text_filter': self.text_filter,
            'should_slice_clusters': self.should_slice_clusters,
            'src_start_cluster_text': self.src_start_cluster_text,
            'src_end_cluster_text': self.src_end_cluster_text,
            'ref_start_cluster_text': self.ref_start_cluster_text,
            'ref_end_cluster_text': self.ref_end_cluster_text
        }
        return result


@dataclass(frozen=True)
class PositionalConfiguration:
    """Configuration for positional text filtering.

    Immutable dataclass for positional column extraction.
    """

    cluster_filter: str
    should_slice_clusters: bool
    text_filter: PositionalFilterType
    src_start_cluster_text: Optional[str] = None
    src_end_cluster_text: Optional[str] = None
    ref_start_cluster_text: Optional[str] = None
    ref_end_cluster_text: Optional[str] = None

    @property
    def filter_type(self) -> str:
        """Get the filter type for positional configuration.

        Returns
        -------
        str
            The positional filter type value
        """
        return TextFilterTypes.POSITIONAL.value

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary for serialization.

        Returns
        -------
        dict[str, Any]
            Dictionary representation with text_filter_type instead of filter_type
        """
        # Maintain expected field order for consistency with legacy format
        result = {
            'cluster_filter': self.cluster_filter,
            'text_filter_type': self.filter_type,
            'text_filter': self.text_filter,
            'should_slice_clusters': self.should_slice_clusters,
            'src_start_cluster_text': self.src_start_cluster_text,
            'src_end_cluster_text': self.src_end_cluster_text,
            'ref_start_cluster_text': self.ref_start_cluster_text,
            'ref_end_cluster_text': self.ref_end_cluster_text
        }
        return result


# Type alias for any configuration type
ConfigurationType = Union[RegexConfiguration, RegexListConfiguration, PositionalConfiguration]
