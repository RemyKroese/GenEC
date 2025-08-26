"""Unit tests for GenEC ConfigurationBuilder."""

from __future__ import annotations

import pytest
import re
from typing import Any

from GenEC.core.configuration_builder import ConfigurationBuilder
from GenEC.core.configuration import RegexConfiguration, RegexListConfiguration, PositionalConfiguration
from GenEC.core.specs import PositionalFilterType, TextFilterTypes


def strip_rich_markup(text: str) -> str:
    """Strip Rich markup from text for testing error messages."""
    # Remove Rich markup tags like [bold red], [/bold red], [yellow], [/yellow]
    return re.sub(r'\[/?[^\]]+\]', '', text)


class TestConfigurationBuilder:
    """Test cases for ConfigurationBuilder class."""

    def test_init_creates_empty_builder(self) -> None:
        """Test that builder initializes with empty fields."""
        builder = ConfigurationBuilder()
        assert builder._fields == {}

    def test_with_cluster_filter_sets_value(self) -> None:
        """Test that with_cluster_filter sets the value and returns builder."""
        builder = ConfigurationBuilder()
        result = builder.with_cluster_filter('\\n')
        
        assert result is builder  # Method chaining
        assert builder._fields['cluster_filter'] == '\\n'

    def test_with_should_slice_clusters_sets_value(self) -> None:
        """Test that with_should_slice_clusters sets the value and returns builder."""
        builder = ConfigurationBuilder()
        result = builder.with_should_slice_clusters(True)
        
        assert result is builder
        assert builder._fields['should_slice_clusters'] is True

    def test_with_src_start_cluster_text_sets_value(self) -> None:
        """Test that with_src_start_cluster_text sets the value and returns builder."""
        builder = ConfigurationBuilder()
        result = builder.with_src_start_cluster_text('start_text')
        
        assert result is builder
        assert builder._fields['src_start_cluster_text'] == 'start_text'

    def test_with_src_start_cluster_text_sets_none(self) -> None:
        """Test that with_src_start_cluster_text can set None value."""
        builder = ConfigurationBuilder()
        result = builder.with_src_start_cluster_text(None)
        
        assert result is builder
        assert builder._fields['src_start_cluster_text'] is None

    def test_with_src_end_cluster_text_sets_value(self) -> None:
        """Test that with_src_end_cluster_text sets the value and returns builder."""
        builder = ConfigurationBuilder()
        result = builder.with_src_end_cluster_text('end_text')
        
        assert result is builder
        assert builder._fields['src_end_cluster_text'] == 'end_text'

    def test_with_src_end_cluster_text_sets_none(self) -> None:
        """Test that with_src_end_cluster_text can set None value."""
        builder = ConfigurationBuilder()
        result = builder.with_src_end_cluster_text(None)
        
        assert result is builder
        assert builder._fields['src_end_cluster_text'] is None

    def test_with_ref_start_cluster_text_sets_value(self) -> None:
        """Test that with_ref_start_cluster_text sets the value and returns builder."""
        builder = ConfigurationBuilder()
        result = builder.with_ref_start_cluster_text('ref_start')
        
        assert result is builder
        assert builder._fields['ref_start_cluster_text'] == 'ref_start'

    def test_with_ref_start_cluster_text_sets_none(self) -> None:
        """Test that with_ref_start_cluster_text can set None value."""
        builder = ConfigurationBuilder()
        result = builder.with_ref_start_cluster_text(None)
        
        assert result is builder
        assert builder._fields['ref_start_cluster_text'] is None

    def test_with_ref_end_cluster_text_sets_value(self) -> None:
        """Test that with_ref_end_cluster_text sets the value and returns builder."""
        builder = ConfigurationBuilder()
        result = builder.with_ref_end_cluster_text('ref_end')
        
        assert result is builder
        assert builder._fields['ref_end_cluster_text'] == 'ref_end'

    def test_with_ref_end_cluster_text_sets_none(self) -> None:
        """Test that with_ref_end_cluster_text can set None value."""
        builder = ConfigurationBuilder()
        result = builder.with_ref_end_cluster_text(None)
        
        assert result is builder
        assert builder._fields['ref_end_cluster_text'] is None

    def test_with_filter_type_sets_value(self) -> None:
        """Test that with_filter_type sets the value and returns builder."""
        builder = ConfigurationBuilder()
        result = builder.with_filter_type(TextFilterTypes.REGEX.value)

        assert result is builder
        assert builder._fields['text_filter_type'] == TextFilterTypes.REGEX.value

    def test_with_text_filter_sets_value(self) -> None:
        """Test that with_text_filter sets the value and returns builder."""
        builder = ConfigurationBuilder()
        result = builder.with_text_filter('test_pattern')
        
        assert result is builder
        assert builder._fields['text_filter'] == 'test_pattern'

    def test_with_preset_sets_value(self) -> None:
        """Test that with_preset sets the value and returns builder."""
        builder = ConfigurationBuilder()
        result = builder.with_preset('test_preset')
        
        assert result is builder
        assert builder._fields['preset'] == 'test_preset'

    def test_with_target_file_sets_value(self) -> None:
        """Test that with_target_file sets the value and returns builder."""
        builder = ConfigurationBuilder()
        result = builder.with_target_file('test_file.txt')
        
        assert result is builder
        assert builder._fields['target_file'] == 'test_file.txt'

    def test_with_group_sets_value(self) -> None:
        """Test that with_group sets the value and returns builder."""
        builder = ConfigurationBuilder()
        result = builder.with_group('test_group')
        
        assert result is builder
        assert builder._fields['group'] == 'test_group'

    def test_build_regex_configuration_minimal(self) -> None:
        """Test building a minimal regex configuration."""
        builder = ConfigurationBuilder()
        config = (builder
                  .with_cluster_filter('\\n')
                  .with_should_slice_clusters(False)
                  .with_filter_type(TextFilterTypes.REGEX.value)
                  .with_text_filter('test_pattern')
                  .build())
        
        assert isinstance(config, RegexConfiguration)
        assert config.cluster_filter == '\\n'
        assert config.should_slice_clusters is False
        assert config.text_filter == 'test_pattern'
        assert config.preset == ''
        assert config.target_file == ''
        assert config.group == ''
        assert config.src_start_cluster_text is None
        assert config.src_end_cluster_text is None
        assert config.ref_start_cluster_text is None
        assert config.ref_end_cluster_text is None

    def test_build_regex_configuration_full(self) -> None:
        """Test building a full regex configuration with all fields."""
        builder = ConfigurationBuilder()
        config = (builder
                  .with_cluster_filter('\\n')
                  .with_should_slice_clusters(True)
                  .with_filter_type(TextFilterTypes.REGEX.value)
                  .with_text_filter('test_pattern')
                  .with_preset('test_preset')
                  .with_target_file('test_file.txt')
                  .with_group('test_group')
                  .with_src_start_cluster_text('src_start')
                  .with_src_end_cluster_text('src_end')
                  .with_ref_start_cluster_text('ref_start')
                  .with_ref_end_cluster_text('ref_end')
                  .build())
        
        assert isinstance(config, RegexConfiguration)
        assert config.cluster_filter == '\\n'
        assert config.should_slice_clusters is True
        assert config.text_filter == 'test_pattern'
        assert config.preset == 'test_preset'
        assert config.target_file == 'test_file.txt'
        assert config.group == 'test_group'
        assert config.src_start_cluster_text == 'src_start'
        assert config.src_end_cluster_text == 'src_end'
        assert config.ref_start_cluster_text == 'ref_start'
        assert config.ref_end_cluster_text == 'ref_end'

    def test_build_regex_list_configuration_minimal(self) -> None:
        """Test building a minimal regex list configuration."""
        builder = ConfigurationBuilder()
        text_filters = ['pattern1', 'pattern2']
        config = (builder
                  .with_cluster_filter('\\n')
                  .with_should_slice_clusters(False)
                  .with_filter_type(TextFilterTypes.REGEX_LIST.value)
                  .with_text_filter(text_filters)
                  .build())
        
        assert isinstance(config, RegexListConfiguration)
        assert config.cluster_filter == '\\n'
        assert config.should_slice_clusters is False
        assert config.text_filter == text_filters
        assert config.preset == ''
        assert config.target_file == ''
        assert config.group == ''

    def test_build_regex_list_configuration_full(self) -> None:
        """Test building a full regex list configuration with all fields."""
        builder = ConfigurationBuilder()
        text_filters = ['pattern1', 'pattern2', 'pattern3']
        config = (builder
                  .with_cluster_filter('\\n\\n')
                  .with_should_slice_clusters(True)
                  .with_filter_type(TextFilterTypes.REGEX_LIST.value)
                  .with_text_filter(text_filters)
                  .with_preset('list_preset')
                  .with_target_file('list_file.txt')
                  .with_group('list_group')
                  .with_src_start_cluster_text('list_src_start')
                  .with_src_end_cluster_text('list_src_end')
                  .with_ref_start_cluster_text('list_ref_start')
                  .with_ref_end_cluster_text('list_ref_end')
                  .build())
        
        assert isinstance(config, RegexListConfiguration)
        assert config.cluster_filter == '\\n\\n'
        assert config.should_slice_clusters is True
        assert config.text_filter == text_filters
        assert config.preset == 'list_preset'
        assert config.target_file == 'list_file.txt'
        assert config.group == 'list_group'
        assert config.src_start_cluster_text == 'list_src_start'
        assert config.src_end_cluster_text == 'list_src_end'
        assert config.ref_start_cluster_text == 'list_ref_start'
        assert config.ref_end_cluster_text == 'list_ref_end'

    def test_build_positional_configuration_minimal(self) -> None:
        """Test building a minimal positional configuration."""
        builder = ConfigurationBuilder()
        pos_filter = PositionalFilterType(separator='=', line=1, occurrence=2)
        config = (builder
                  .with_cluster_filter('\\n\\n')
                  .with_should_slice_clusters(False)
                  .with_filter_type(TextFilterTypes.POSITIONAL.value)
                  .with_text_filter(pos_filter)
                  .build())
        
        assert isinstance(config, PositionalConfiguration)
        assert config.cluster_filter == '\\n\\n'
        assert config.should_slice_clusters is False
        assert config.text_filter == pos_filter
        assert config.preset == ''
        assert config.target_file == ''
        assert config.group == ''

    def test_build_positional_configuration_from_dict(self) -> None:
        """Test building positional configuration from dictionary."""
        builder = ConfigurationBuilder()
        pos_dict = {'separator': '=', 'line': 1, 'occurrence': 2}
        config = (builder
                  .with_cluster_filter('\\n\\n')
                  .with_should_slice_clusters(False)
                  .with_filter_type(TextFilterTypes.POSITIONAL.value)
                  .with_text_filter(pos_dict)
                  .build())
        
        assert isinstance(config, PositionalConfiguration)
        assert config.text_filter.separator == '='
        assert config.text_filter.line == 1
        assert config.text_filter.occurrence == 2

    def test_build_positional_configuration_full(self) -> None:
        """Test building a full positional configuration with all fields."""
        builder = ConfigurationBuilder()
        pos_filter = PositionalFilterType(separator='|', line=3, occurrence=1)
        config = (builder
                  .with_cluster_filter('\\n\\n')
                  .with_should_slice_clusters(True)
                  .with_filter_type(TextFilterTypes.POSITIONAL.value)
                  .with_text_filter(pos_filter)
                  .with_preset('pos_preset')
                  .with_target_file('pos_file.txt')
                  .with_group('pos_group')
                  .with_src_start_cluster_text('pos_src_start')
                  .with_src_end_cluster_text('pos_src_end')
                  .with_ref_start_cluster_text('pos_ref_start')
                  .with_ref_end_cluster_text('pos_ref_end')
                  .build())
        
        assert isinstance(config, PositionalConfiguration)
        assert config.cluster_filter == '\\n\\n'
        assert config.should_slice_clusters is True
        assert config.text_filter == pos_filter
        assert config.preset == 'pos_preset'
        assert config.target_file == 'pos_file.txt'
        assert config.group == 'pos_group'
        assert config.src_start_cluster_text == 'pos_src_start'
        assert config.src_end_cluster_text == 'pos_src_end'
        assert config.ref_start_cluster_text == 'pos_ref_start'
        assert config.ref_end_cluster_text == 'pos_ref_end'

    def test_build_missing_cluster_filter_raises_error(self) -> None:
        """Test that missing cluster_filter raises ValueError."""
        builder = ConfigurationBuilder()
        with pytest.raises(ValueError) as exc_info:
            (builder
             .with_should_slice_clusters(False)
             .with_filter_type(TextFilterTypes.REGEX.value)
             .with_text_filter('pattern')
             .build())
        
        error_msg = strip_rich_markup(str(exc_info.value))
        assert "Required field cluster_filter is missing" in error_msg

    def test_build_missing_should_slice_clusters_raises_error(self) -> None:
        """Test that missing should_slice_clusters raises ValueError."""
        builder = ConfigurationBuilder()
        with pytest.raises(ValueError) as exc_info:
            (builder
             .with_cluster_filter('\\n')
             .with_filter_type(TextFilterTypes.REGEX.value)
             .with_text_filter('pattern')
             .build())
        
        error_msg = strip_rich_markup(str(exc_info.value))
        assert "Required field should_slice_clusters is missing" in error_msg

    def test_build_missing_filter_type_raises_error(self) -> None:
        """Test that missing filter_type raises ValueError."""
        builder = ConfigurationBuilder()
        with pytest.raises(ValueError) as exc_info:
            (builder
             .with_cluster_filter('\\n')
             .with_should_slice_clusters(False)
             .with_text_filter('pattern')
             .build())
        
        error_msg = strip_rich_markup(str(exc_info.value))
        assert "Required field text_filter_type is missing" in error_msg

    def test_build_missing_text_filter_raises_error(self) -> None:
        """Test that missing text_filter raises ValueError."""
        builder = ConfigurationBuilder()
        with pytest.raises(ValueError) as exc_info:
            (builder
             .with_cluster_filter('\\n')
             .with_should_slice_clusters(False)
             .with_filter_type(TextFilterTypes.REGEX.value)
             .build())
        
        error_msg = strip_rich_markup(str(exc_info.value))
        assert "Required field text_filter is missing" in error_msg

    def test_build_regex_invalid_text_filter_type_raises_error(self) -> None:
        """Test that invalid text_filter type for regex raises ValueError."""
        builder = ConfigurationBuilder()
        with pytest.raises(ValueError) as exc_info:
            (builder
             .with_cluster_filter('\\n')
             .with_should_slice_clusters(False)
             .with_filter_type(TextFilterTypes.REGEX.value)
             .with_text_filter(['not', 'a', 'string'])
             .build())
        
        error_msg = strip_rich_markup(str(exc_info.value))
        assert "text_filter must be str for Regex, got <class 'list'>" in error_msg

    def test_build_regex_list_invalid_text_filter_type_raises_error(self) -> None:
        """Test that invalid text_filter type for regex list raises ValueError."""
        builder = ConfigurationBuilder()
        with pytest.raises(ValueError) as exc_info:
            (builder
             .with_cluster_filter('\\n')
             .with_should_slice_clusters(False)
             .with_filter_type(TextFilterTypes.REGEX_LIST.value)
             .with_text_filter('not_a_list')
             .build())
        
        error_msg = strip_rich_markup(str(exc_info.value))
        assert "text_filter must be list for Regex-list, got <class 'str'>" in error_msg

    def test_build_regex_list_invalid_list_item_type_raises_error(self) -> None:
        """Test that non-string items in regex list raises ValueError."""
        builder = ConfigurationBuilder()
        with pytest.raises(ValueError) as exc_info:
            (builder
             .with_cluster_filter('\\n')
             .with_should_slice_clusters(False)
             .with_filter_type(TextFilterTypes.REGEX_LIST.value)
             .with_text_filter(['valid_string', 123, 'another_string'])
             .build())
        
        error_msg = strip_rich_markup(str(exc_info.value))
        assert "Item 1 in text_filter must be string, got <class 'int'>" in error_msg

    def test_build_positional_invalid_text_filter_type_raises_error(self) -> None:
        """Test that invalid text_filter type for positional raises ValueError."""
        builder = ConfigurationBuilder()
        with pytest.raises(ValueError) as exc_info:
            (builder
             .with_cluster_filter('\\n')
             .with_should_slice_clusters(False)
             .with_filter_type(TextFilterTypes.POSITIONAL.value)
             .with_text_filter('not_positional')
             .build())
        
        error_msg = strip_rich_markup(str(exc_info.value))
        assert "text_filter must be PositionalFilterType for Positional, got <class 'str'>" in error_msg

    def test_build_positional_invalid_dict_raises_error(self) -> None:
        """Test that invalid positional dict raises ValueError."""
        builder = ConfigurationBuilder()
        with pytest.raises(ValueError, match="Invalid positional filter configuration"):
            (builder
             .with_cluster_filter('\\n')
             .with_should_slice_clusters(False)
             .with_filter_type(TextFilterTypes.POSITIONAL.value)
             .with_text_filter({'invalid': 'dict'})
             .build())

    def test_build_unsupported_filter_type_raises_error(self) -> None:
        """Test that unsupported filter type raises ValueError."""
        builder = ConfigurationBuilder()
        with pytest.raises(ValueError) as exc_info:
            (builder
             .with_cluster_filter('\\n')
             .with_should_slice_clusters(False)
             .with_filter_type('UnsupportedType')
             .with_text_filter('pattern')
             .build())
        
        error_msg = strip_rich_markup(str(exc_info.value))
        assert "Unsupported filter type: UnsupportedType" in error_msg

    def test_method_chaining_order_independence(self) -> None:
        """Test that method chaining works regardless of call order."""
        builder = ConfigurationBuilder()
        config = (builder
                  .with_text_filter('pattern')
                  .with_preset('test')
                  .with_cluster_filter('\\n')
                  .with_filter_type(TextFilterTypes.REGEX.value)
                  .with_should_slice_clusters(True)
                  .with_group('group1')
                  .build())
        
        assert isinstance(config, RegexConfiguration)
        assert config.text_filter == 'pattern'
        assert config.preset == 'test'
        assert config.cluster_filter == '\\n'
        assert config.should_slice_clusters is True
        assert config.group == 'group1'

    def test_builder_reuse_state_isolation(self) -> None:
        """Test that reusing builder doesn't affect previous builds."""
        builder = ConfigurationBuilder()
        
        # Build first configuration
        config1 = (builder
                   .with_cluster_filter('\\n')
                   .with_should_slice_clusters(False)
                   .with_filter_type(TextFilterTypes.REGEX.value)
                   .with_text_filter('pattern1')
                   .build())
        
        # Modify builder and build second configuration
        config2 = (builder
                   .with_text_filter('pattern2')
                   .with_preset('test_preset')
                   .build())
        
        # Verify both configurations are correct
        assert isinstance(config1, RegexConfiguration)
        assert config1.text_filter == 'pattern1'
        assert config1.preset == ''
        
        assert isinstance(config2, RegexConfiguration)
        assert config2.text_filter == 'pattern2'
        assert config2.preset == 'test_preset'
        assert config2.cluster_filter == '\\n'  # Inherited from first build

    def test_optional_fields_defaults(self) -> None:
        """Test that optional fields get proper default values."""
        builder = ConfigurationBuilder()
        config = (builder
                  .with_cluster_filter('\\n')
                  .with_should_slice_clusters(False)
                  .with_filter_type(TextFilterTypes.REGEX.value)
                  .with_text_filter('pattern')
                  .build())
        
        # Test default values for metadata fields
        assert config.preset == ''
        assert config.target_file == ''
        assert config.group == ''
        
        # Test default values for optional cluster text fields
        assert config.src_start_cluster_text is None
        assert config.src_end_cluster_text is None
        assert config.ref_start_cluster_text is None
        assert config.ref_end_cluster_text is None
