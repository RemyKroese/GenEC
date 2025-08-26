"""Type definitions for immutable configuration classes."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

from GenEC.core.specs import PositionalFilterType, TextFilterTypes


T = TypeVar('T')


@dataclass(frozen=True)
class BaseConfiguration(ABC, Generic[T]):  # pylint: disable=too-many-instance-attributes
    """Base configuration class with common attributes.

    Immutable dataclass containing attributes shared across all filter types.
    """

    cluster_filter: str
    text_filter: T
    should_slice_clusters: bool
    preset: str = ''
    target_file: str = ''
    group: str = ''
    src_start_cluster_text: Optional[str] = None
    src_end_cluster_text: Optional[str] = None
    ref_start_cluster_text: Optional[str] = None
    ref_end_cluster_text: Optional[str] = None

    @property
    @abstractmethod
    def filter_type(self) -> str:
        """Get the filter type for this configuration.

        Returns
        -------
        str
            The filter type value
        """

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
class RegexConfiguration(BaseConfiguration[str]):
    """Configuration for regex-based text filtering."""

    @property
    def filter_type(self) -> str:
        """Get the filter type for regex configuration.

        Returns
        -------
        str
            The regex filter type value
        """
        return TextFilterTypes.REGEX.value


@dataclass(frozen=True)
class RegexListConfiguration(BaseConfiguration[list[str]]):
    """Configuration for regex list-based text filtering."""

    @property
    def filter_type(self) -> str:
        """Get the filter type for regex list configuration.

        Returns
        -------
        str
            The regex list filter type value
        """
        return TextFilterTypes.REGEX_LIST.value


@dataclass(frozen=True)
class PositionalConfiguration(BaseConfiguration[PositionalFilterType]):
    """Configuration for positional text filtering."""

    @property
    def filter_type(self) -> str:
        """Get the filter type for positional configuration.

        Returns
        -------
        str
            The positional filter type value
        """
        return TextFilterTypes.POSITIONAL.value
