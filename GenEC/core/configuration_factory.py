"""Factories for creating configuration objects."""

from typing import List, TYPE_CHECKING

from GenEC.core.configuration_builder import ConfigurationBuilder
from GenEC.core.configuration import ConfigurationType
from GenEC.core.prompts import Section, Key, create_prompt
from GenEC.core.specs import PositionalFilterType, TextFilterTypes

if TYPE_CHECKING:
    from GenEC.core.config_manager import ConfigManager
    from GenEC.core.types.preset_config import Initialized


class BasicConfigurationFactory:
    """Factory for creating configurations interactively."""

    @staticmethod
    def build_interactive(config_manager: 'ConfigManager') -> ConfigurationType:
        """
        Build a configuration by prompting the user for all values using existing prompt methods.

        Parameters
        ----------
        config_manager : ConfigManager
            ConfigManager instance with access to prompt methods

        Returns
        -------
        ConfigurationType
            The built configuration
        """
        builder = ConfigurationBuilder()

        # Use existing filter type selection with menu
        filter_options = [t.value for t in TextFilterTypes]
        filter_type = config_manager.ask_mpc_question(
            create_prompt(Section.SET_CONFIG, Key.TEXT_FILTER_TYPE),
            filter_options
        )
        builder.with_filter_type(filter_type)

        # Use existing cluster filter prompt
        cluster_filter = config_manager.ask_open_question(
            create_prompt(Section.SET_CONFIG, Key.CLUSTER_FILTER_REGEX)
        )
        if not cluster_filter:
            cluster_filter = '\n'  # Default if empty
        builder.with_cluster_filter(cluster_filter)

        # Use existing text filter prompts based on filter type
        if filter_type == TextFilterTypes.REGEX.value:
            regex_pattern = config_manager.ask_open_question(
                create_prompt(Section.SET_CONFIG, Key.REGEX_FILTER)
            )
            builder.with_text_filter(regex_pattern)

        elif filter_type == TextFilterTypes.REGEX_LIST.value:
            patterns: List[str] = []
            search_count = 1
            while True:
                pattern = config_manager.ask_open_question(
                    create_prompt(Section.SET_CONFIG, Key.REGEX_LIST_FILTER, search=search_count)
                )
                if not pattern:
                    break
                patterns.append(pattern)
                search_count += 1

                # Ask if user wants to add another pattern
                continue_response = config_manager.ask_open_question(
                    create_prompt(Section.SET_CONFIG, Key.REGEX_LIST_CONTINUE)
                ).lower()
                if continue_response not in ('yes', 'y'):
                    break
            builder.with_text_filter(patterns)

        elif filter_type == TextFilterTypes.POSITIONAL.value:
            # Use existing positional filter prompts
            separator = config_manager.ask_open_question(
                create_prompt(Section.SET_CONFIG, Key.POSITIONAL_SEPARATOR)
            )
            line_str = config_manager.ask_open_question(
                create_prompt(Section.SET_CONFIG, Key.POSITIONAL_LINE)
            )
            occurrence_str = config_manager.ask_open_question(
                create_prompt(Section.SET_CONFIG, Key.POSITIONAL_OCCURRENCE)
            )

            # Validate input
            if not line_str:
                raise ValueError("Line number is required for positional filter")
            if not occurrence_str:
                raise ValueError("Occurrence number is required for positional filter")

            line = int(line_str)
            occurrence = int(occurrence_str)
            positional_filter = PositionalFilterType(
                separator=separator,
                line=line,
                occurrence=occurrence
            )
            builder.with_text_filter(positional_filter)

        # Now ask about slicing clusters (after text filter is set)
        should_slice = config_manager.ask_open_question(
            create_prompt(Section.SET_CONFIG, Key.SHOULD_SLICE_CLUSTERS)
        ).lower() in ('y', 'yes')
        builder.with_should_slice_clusters(should_slice)

        # If slicing clusters, prompt for boundary texts
        if should_slice:
            builder.with_src_start_cluster_text(
                config_manager.ask_open_question("Source start cluster text: ") or None
            )
            builder.with_src_end_cluster_text(
                config_manager.ask_open_question("Source end cluster text: ") or None
            )
            builder.with_ref_start_cluster_text(
                config_manager.ask_open_question("Reference start cluster text: ") or None
            )
            builder.with_ref_end_cluster_text(
                config_manager.ask_open_question("Reference end cluster text: ") or None
            )

        # Build and return the configuration
        return builder.build()


class PresetConfigurationFactory:
    """Factory for creating configurations from presets."""

    @staticmethod
    def build_from_preset(config_manager: 'ConfigManager', preset_target: str) -> ConfigurationType:
        """Build configuration from a preset."""
        initialized_config = config_manager.load_preset(preset_target)
        return PresetConfigurationFactory._convert_initialized_to_new_config(initialized_config)

    @staticmethod
    def _convert_initialized_to_new_config(initialized: 'Initialized') -> ConfigurationType:
        """Convert Initialized config to new configuration format."""
        builder = ConfigurationBuilder()

        # Map required fields
        if initialized.get('cluster_filter') is not None:
            builder.with_cluster_filter(initialized['cluster_filter'])
        if initialized.get('text_filter_type') is not None:
            builder.with_filter_type(initialized['text_filter_type'])
        if initialized.get('text_filter') is not None:
            builder.with_text_filter(initialized['text_filter'])
        if initialized.get('should_slice_clusters') is not None:
            builder.with_should_slice_clusters(initialized['should_slice_clusters'])

        # Map optional slicing fields
        if initialized.get('src_start_cluster_text') is not None:
            builder.with_src_start_cluster_text(initialized['src_start_cluster_text'])
        if initialized.get('src_end_cluster_text') is not None:
            builder.with_src_end_cluster_text(initialized['src_end_cluster_text'])
        if initialized.get('ref_start_cluster_text') is not None:
            builder.with_ref_start_cluster_text(initialized['ref_start_cluster_text'])
        if initialized.get('ref_end_cluster_text') is not None:
            builder.with_ref_end_cluster_text(initialized['ref_end_cluster_text'])

        return builder.build()
