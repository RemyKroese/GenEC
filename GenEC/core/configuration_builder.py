"""Builder for immutable configuration objects."""

from typing import Any, Optional, cast

from GenEC.core.specs import PositionalFilterType, TextFilterTypes
from GenEC.core.configuration import (
    BaseConfiguration, RegexConfiguration, RegexListConfiguration, PositionalConfiguration
)


class ConfigurationBuilder:
    """Builder for creating immutable configuration objects."""

    def __init__(self) -> None:
        """Initialize an empty builder."""
        self._fields: dict[str, Any] = {}

    def with_cluster_filter(self, value: str) -> 'ConfigurationBuilder':
        """
        Set the cluster filter.

        Parameters
        ----------
        value : str
            The cluster filter value

        Returns
        -------
        ConfigurationBuilder
            Builder instance for method chaining
        """
        self._fields['cluster_filter'] = value
        return self

    def with_should_slice_clusters(self, value: bool) -> 'ConfigurationBuilder':
        """
        Set whether clusters should be sliced.

        Parameters
        ----------
        value : bool
            Whether clusters should be sliced

        Returns
        -------
        ConfigurationBuilder
            Builder instance for method chaining
        """
        self._fields['should_slice_clusters'] = value
        return self

    def with_src_start_cluster_text(self, value: Optional[str]) -> 'ConfigurationBuilder':
        """
        Set the source start cluster text.

        Parameters
        ----------
        value : Optional[str]
            The source start cluster text, or None

        Returns
        -------
        ConfigurationBuilder
            Builder instance for method chaining
        """
        self._fields['src_start_cluster_text'] = value
        return self

    def with_src_end_cluster_text(self, value: Optional[str]) -> 'ConfigurationBuilder':
        """
        Set the source end cluster text.

        Parameters
        ----------
        value : Optional[str]
            The source end cluster text, or None

        Returns
        -------
        ConfigurationBuilder
            Builder instance for method chaining
        """
        self._fields['src_end_cluster_text'] = value
        return self

    def with_ref_start_cluster_text(self, value: Optional[str]) -> 'ConfigurationBuilder':
        """
        Set the reference start cluster text.

        Parameters
        ----------
        value : Optional[str]
            The reference start cluster text, or None

        Returns
        -------
        ConfigurationBuilder
            Builder instance for method chaining
        """
        self._fields['ref_start_cluster_text'] = value
        return self

    def with_ref_end_cluster_text(self, value: Optional[str]) -> 'ConfigurationBuilder':
        """
        Set the reference end cluster text.

        Parameters
        ----------
        value : Optional[str]
            The reference end cluster text, or None

        Returns
        -------
        ConfigurationBuilder
            Builder instance for method chaining
        """
        self._fields['ref_end_cluster_text'] = value
        return self

    def with_filter_type(self, value: str) -> 'ConfigurationBuilder':
        """
        Set the filter type.

        Parameters
        ----------
        value : str
            The filter type value from TextFilterTypes enum

        Returns
        -------
        ConfigurationBuilder
            Builder instance for method chaining
        """
        self._fields['filter_type'] = value
        return self

    def with_text_filter(self, value: Any) -> 'ConfigurationBuilder':
        """Set the text filter value.

        Parameters
        ----------
        value : Any
            The text filter value (type depends on filter type)

        Returns
        -------
        ConfigurationBuilder
            Builder instance for method chaining
        """
        self._fields['text_filter'] = value
        return self

    def with_preset(self, value: str) -> 'ConfigurationBuilder':
        """
        Set the preset name.

        Parameters
        ----------
        value : str
            The preset name

        Returns
        -------
        ConfigurationBuilder
            Builder instance for method chaining
        """
        self._fields['preset'] = value
        return self

    def with_target_file(self, value: str) -> 'ConfigurationBuilder':
        """
        Set the target file.

        Parameters
        ----------
        value : str
            The target file name

        Returns
        -------
        ConfigurationBuilder
            Builder instance for method chaining
        """
        self._fields['target_file'] = value
        return self

    def with_group(self, value: str) -> 'ConfigurationBuilder':
        """
        Set the group name.

        Parameters
        ----------
        value : str
            The group name

        Returns
        -------
        ConfigurationBuilder
            Builder instance for method chaining
        """
        self._fields['group'] = value
        return self

    def build(self) -> BaseConfiguration:  # pylint: disable=R0912
        """
        Build the configuration object based on collected values.

        Returns
        -------
        BaseConfiguration
            The built configuration object of the appropriate subtype

        Raises
        ------
        ValueError
            If required fields are missing or have invalid values
        """
        # Validate required fields
        required_fields = ['cluster_filter', 'should_slice_clusters', 'filter_type', 'text_filter']
        for field_name in required_fields:
            if field_name not in self._fields:
                raise ValueError(f"Required field {field_name} is missing")

        filter_type = self._fields['filter_type']
        text_filter = self._fields['text_filter']

        # Prepare common arguments
        base_args = {
            'cluster_filter': self._fields['cluster_filter'],
            'should_slice_clusters': self._fields['should_slice_clusters'],
        }

        # Add optional fields if present
        for field_name in ['src_start_cluster_text', 'src_end_cluster_text',
                           'ref_start_cluster_text', 'ref_end_cluster_text']:
            if field_name in self._fields:
                base_args[field_name] = self._fields[field_name]

        # Add metadata fields with defaults
        base_args['preset'] = self._fields.get('preset', '')
        base_args['target_file'] = self._fields.get('target_file', '')
        base_args['group'] = self._fields.get('group', '')

        # Create the appropriate configuration type based on filter_type
        if filter_type == TextFilterTypes.REGEX.value:
            if not isinstance(text_filter, str):
                raise ValueError(f"text_filter must be str for {filter_type}, got {type(text_filter)}")
            return RegexConfiguration(text_filter=text_filter, **base_args)

        if filter_type == TextFilterTypes.REGEX_LIST.value:
            if not isinstance(text_filter, list):
                raise ValueError(f"text_filter must be list for {filter_type}, got {type(text_filter)}")
            # Validate that all elements are strings - text_filter is now known to be list
            for i, item in enumerate(text_filter):
                if not isinstance(item, str):
                    raise ValueError(f"Item {i} in text_filter must be string, got {type(item)}")
            validated_list = cast(list[str], text_filter)
            return RegexListConfiguration(text_filter=validated_list, **base_args)

        if filter_type == TextFilterTypes.POSITIONAL.value:
            # Handle dictionary conversion for positional filter
            if isinstance(text_filter, dict):
                try:
                    text_filter_dict = cast(dict[str, Any], text_filter)
                    text_filter = PositionalFilterType(**text_filter_dict)
                except (TypeError, ValueError) as e:
                    raise ValueError(f"Invalid positional filter configuration: {e}") from e
            elif not isinstance(text_filter, PositionalFilterType):
                raise ValueError(f"text_filter must be PositionalFilterType for {filter_type}, got {type(text_filter)}")
            return PositionalConfiguration(text_filter=text_filter, **base_args)

        raise ValueError(f"Unsupported filter_type: {filter_type}")
