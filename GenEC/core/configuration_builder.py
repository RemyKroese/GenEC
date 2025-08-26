"""Builder for immutable configuration objects."""

from typing import Any, Optional, cast

from GenEC.core.specs import PositionalFilterType, TextFilterTypes, ConfigOptions
from GenEC.core.configuration import (
    BaseConfiguration, RegexConfiguration, RegexListConfiguration, PositionalConfiguration
)
from GenEC.core.prompts import create_prompt, Section, Key


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
        self._fields[ConfigOptions.CLUSTER_FILTER.value] = value
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
        self._fields[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] = value
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
        self._fields[ConfigOptions.SRC_START_CLUSTER_TEXT.value] = value
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
        self._fields[ConfigOptions.SRC_END_CLUSTER_TEXT.value] = value
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
        self._fields[ConfigOptions.REF_START_CLUSTER_TEXT.value] = value
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
        self._fields[ConfigOptions.REF_END_CLUSTER_TEXT.value] = value
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
        self._fields[ConfigOptions.TEXT_FILTER_TYPE.value] = value
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
        self._fields[ConfigOptions.TEXT_FILTER.value] = value
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
        self._fields[ConfigOptions.PRESET.value] = value
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
        self._fields[ConfigOptions.TARGET_FILE.value] = value
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
        self._fields[ConfigOptions.GROUP.value] = value
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
        required_fields = [ConfigOptions.CLUSTER_FILTER.value, ConfigOptions.SHOULD_SLICE_CLUSTERS.value,
                           ConfigOptions.TEXT_FILTER_TYPE.value, ConfigOptions.TEXT_FILTER.value]
        for field_name in required_fields:
            if field_name not in self._fields:
                raise ValueError(create_prompt(Section.ERROR_HANDLING, Key.REQUIRED_FIELD_MISSING,
                                               field_name=field_name))

        filter_type = self._fields[ConfigOptions.TEXT_FILTER_TYPE.value]
        text_filter = self._fields[ConfigOptions.TEXT_FILTER.value]

        # Prepare common arguments
        base_args = {
            ConfigOptions.CLUSTER_FILTER.value: self._fields[ConfigOptions.CLUSTER_FILTER.value],
            ConfigOptions.SHOULD_SLICE_CLUSTERS.value: self._fields[ConfigOptions.SHOULD_SLICE_CLUSTERS.value],
        }

        # Add optional fields if present
        for field_name in [ConfigOptions.SRC_START_CLUSTER_TEXT.value, ConfigOptions.SRC_END_CLUSTER_TEXT.value,
                           ConfigOptions.REF_START_CLUSTER_TEXT.value, ConfigOptions.REF_END_CLUSTER_TEXT.value]:
            if field_name in self._fields:
                base_args[field_name] = self._fields[field_name]

        # Add metadata fields with defaults
        base_args[ConfigOptions.PRESET.value] = self._fields.get('preset', '')
        base_args[ConfigOptions.TARGET_FILE.value] = self._fields.get('target_file', '')
        base_args[ConfigOptions.GROUP.value] = self._fields.get('group', '')

        # Create the appropriate configuration type based on filter_type
        if filter_type == TextFilterTypes.REGEX.value:
            if not isinstance(text_filter, str):
                raise ValueError(create_prompt(Section.ERROR_HANDLING, Key.TEXT_FILTER_TYPE_MISMATCH_STR,
                                               filter_type=filter_type, actual_type=type(text_filter)))
            return RegexConfiguration(text_filter=text_filter, **base_args)

        if filter_type == TextFilterTypes.REGEX_LIST.value:
            if not isinstance(text_filter, list):
                raise ValueError(create_prompt(Section.ERROR_HANDLING, Key.TEXT_FILTER_TYPE_MISMATCH_LIST,
                                               filter_type=filter_type, actual_type=type(text_filter)))
            # Validate that all elements are strings - text_filter is now known to be list
            for i, item in enumerate(text_filter):
                if not isinstance(item, str):
                    raise ValueError(create_prompt(Section.ERROR_HANDLING, Key.TEXT_FILTER_LIST_ITEM_TYPE_ERROR,
                                                   item_index=i, actual_type=type(item)))
            validated_list = cast(list[str], text_filter)
            return RegexListConfiguration(text_filter=validated_list, **base_args)

        if filter_type == TextFilterTypes.POSITIONAL.value:
            # Handle dictionary conversion for positional filter
            if isinstance(text_filter, dict):
                try:
                    text_filter_dict = cast(dict[str, Any], text_filter)
                    text_filter = PositionalFilterType(**text_filter_dict)
                except (TypeError, ValueError) as e:
                    raise ValueError(create_prompt(Section.ERROR_HANDLING, Key.INVALID_POSITIONAL_FILTER_CONFIG,
                                                   error=str(e))) from e
            elif not isinstance(text_filter, PositionalFilterType):
                raise ValueError(create_prompt(Section.ERROR_HANDLING, Key.TEXT_FILTER_TYPE_MISMATCH_POSITIONAL,
                                               filter_type=filter_type, actual_type=type(text_filter)))
            return PositionalConfiguration(text_filter=text_filter, **base_args)

        raise ValueError(create_prompt(Section.SET_CONFIG, Key.UNSUPPORTED_FILTER_TYPE, filter_type=filter_type))
