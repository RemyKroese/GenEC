"""Factories for creating configuration objects."""

from typing import TYPE_CHECKING, Optional, Any

from rich.console import Console

from GenEC import utils
from GenEC.core.configuration_builder import ConfigurationBuilder
from GenEC.core.configuration import BaseConfiguration
from GenEC.core.prompts import Section, Key, create_prompt
from GenEC.core.specs import PositionalFilterType, TextFilterTypes, ConfigOptions

if TYPE_CHECKING:
    from GenEC.core.config_manager import ConfigManager


class BasicConfigurationFactory:
    """Factory for creating configurations interactively."""

    @staticmethod
    def build_interactive(config_manager: 'ConfigManager') -> BaseConfiguration:  # pylint: disable=R0914
        """
        Build a configuration by prompting the user for all values using existing prompt methods.

        Parameters
        ----------
        config_manager : ConfigManager
            ConfigManager instance with access to prompt methods

        Returns
        -------
        BaseConfiguration
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
            cluster_filter = r'\n'  # Default if empty
        builder.with_cluster_filter(cluster_filter)

        # Use existing text filter prompts based on filter type
        if filter_type == TextFilterTypes.REGEX.value:
            regex_pattern = config_manager.ask_open_question(
                create_prompt(Section.SET_CONFIG, Key.REGEX_FILTER)
            )
            builder.with_text_filter(regex_pattern)

        elif filter_type == TextFilterTypes.REGEX_LIST.value:
            patterns: list[str] = []
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
                raise ValueError(create_prompt(Section.ERROR_HANDLING, Key.LINE_NUMBER_REQUIRED))
            if not occurrence_str:
                raise ValueError(create_prompt(Section.ERROR_HANDLING, Key.OCCURRENCE_NUMBER_REQUIRED))

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
                config_manager.ask_open_question(
                    create_prompt(Section.SET_CONFIG, Key.SOURCE_START_CLUSTER_TEXT)
                ) or None
            )
            builder.with_src_end_cluster_text(
                config_manager.ask_open_question(
                    create_prompt(Section.SET_CONFIG, Key.SOURCE_END_CLUSTER_TEXT)
                ) or None
            )
            builder.with_ref_start_cluster_text(
                config_manager.ask_open_question(
                    create_prompt(Section.SET_CONFIG, Key.REFERENCE_START_CLUSTER_TEXT)
                ) or None
            )
            builder.with_ref_end_cluster_text(
                config_manager.ask_open_question(
                    create_prompt(Section.SET_CONFIG, Key.REFERENCE_END_CLUSTER_TEXT)
                ) or None
            )

        # Build and return the configuration
        return builder.build()


class WorkflowConfigurationFactory:
    """Factory for creating workflow-specific configurations."""

    @staticmethod
    def create_basic_config(config_manager: 'ConfigManager') -> BaseConfiguration:
        """
        Create a basic workflow configuration.

        Parameters
        ----------
        config_manager : ConfigManager
            ConfigManager instance with access to prompt methods

        Returns
        -------
        BaseConfiguration
            Configuration for basic workflow (no metadata)
        """
        return BasicConfigurationFactory.build_interactive(config_manager)

    @staticmethod
    def create_preset_config(
            config_manager: 'ConfigManager',
            preset: str,
            target_file: str = '') -> BaseConfiguration:
        """
        Create a preset workflow configuration.

        Parameters
        ----------
        config_manager : ConfigManager
            ConfigManager instance for loading presets
        preset : str
            Preset string in 'file/preset' format
        target_file : str, optional
            Associated target file name, by default ''

        Returns
        -------
        BaseConfiguration
            Configuration for preset workflow with metadata
        """
        extraction_config = PresetConfigurationFactory.build_from_preset(config_manager, preset)

        # Create a new config with metadata by rebuilding through the builder
        builder = ConfigurationBuilder()
        builder._fields.update({
            ConfigOptions.CLUSTER_FILTER.value: extraction_config.cluster_filter,
            ConfigOptions.SHOULD_SLICE_CLUSTERS.value: extraction_config.should_slice_clusters,
            ConfigOptions.TEXT_FILTER_TYPE.value: extraction_config.filter_type,
            ConfigOptions.TEXT_FILTER.value: extraction_config.text_filter,
            ConfigOptions.SRC_START_CLUSTER_TEXT.value: extraction_config.src_start_cluster_text,
            ConfigOptions.SRC_END_CLUSTER_TEXT.value: extraction_config.src_end_cluster_text,
            ConfigOptions.REF_START_CLUSTER_TEXT.value: extraction_config.ref_start_cluster_text,
            ConfigOptions.REF_END_CLUSTER_TEXT.value: extraction_config.ref_end_cluster_text,
            ConfigOptions.PRESET.value: preset,
            ConfigOptions.TARGET_FILE.value: target_file,
            ConfigOptions.GROUP.value: ''
        })
        return builder.build()

    @staticmethod
    def create_preset_list_configs(
            config_manager: 'ConfigManager',
            presets_list_target: str,
            target_variables: Optional[dict[str, str]] = None) -> list[BaseConfiguration]:
        """
        Create preset-list workflow configurations.

        Parameters
        ----------
        config_manager : ConfigManager
            ConfigManager instance for loading presets
        presets_list_target : str
            The name of the presets list YAML file (without extension)
        target_variables : Optional[dict[str, str]], optional
            Variables used to replace placeholders in target file paths

        Returns
        -------
        list[BaseConfiguration]
            List of configurations for preset-list workflow with full metadata
        """
        console = Console()

        presets_list = utils.read_yaml_file(config_manager.presets_directory / f'{presets_list_target}.yaml')
        presets_per_file = config_manager.group_presets_by_file(presets_list, target_variables)

        configs = []
        for target_file, preset_entries in presets_per_file.items():
            for entry in preset_entries:
                preset_target = entry[ConfigOptions.PRESET.value]
                group = entry.get('group', '')

                try:
                    # preset_target is already in the format 'file/preset_name'
                    extraction_config = PresetConfigurationFactory.build_from_preset(
                        config_manager, preset_target)

                    # Create config with full metadata
                    builder = ConfigurationBuilder()
                    builder._fields.update({
                        ConfigOptions.CLUSTER_FILTER.value: extraction_config.cluster_filter,
                        ConfigOptions.SHOULD_SLICE_CLUSTERS.value: extraction_config.should_slice_clusters,
                        ConfigOptions.TEXT_FILTER_TYPE.value: extraction_config.filter_type,
                        ConfigOptions.TEXT_FILTER.value: extraction_config.text_filter,
                        ConfigOptions.SRC_START_CLUSTER_TEXT.value: extraction_config.src_start_cluster_text,
                        ConfigOptions.SRC_END_CLUSTER_TEXT.value: extraction_config.src_end_cluster_text,
                        ConfigOptions.REF_START_CLUSTER_TEXT.value: extraction_config.ref_start_cluster_text,
                        ConfigOptions.REF_END_CLUSTER_TEXT.value: extraction_config.ref_end_cluster_text,
                        ConfigOptions.PRESET.value: preset_target,
                        ConfigOptions.TARGET_FILE.value: target_file,
                        ConfigOptions.GROUP.value: group
                    })
                    configs.append(builder.build())

                # Catching all exceptions is valid here
                except Exception as e:  # pylint: disable=W0718
                    console.print(create_prompt(Section.ERROR_HANDLING, Key.SKIPPING_PRESET,
                                                preset=preset_target, error=e))
                    continue

        if not configs:
            raise ValueError(create_prompt(Section.ERROR_HANDLING, Key.NO_PRESETS_FOUND))
        return configs


class PresetConfigurationFactory:
    """Factory for creating configurations from presets."""

    @staticmethod
    def build_from_preset(  # pylint: disable=R0914
            config_manager: 'ConfigManager', preset_target: str) -> BaseConfiguration:
        """Build configuration from a preset."""
        initialized_config = config_manager.load_preset(preset_target)
        return PresetConfigurationFactory._convert_initialized_to_new_config(initialized_config)

    @staticmethod
    def _convert_initialized_to_new_config(initialized: dict[str, Any]) -> BaseConfiguration:
        """Convert initialized config dict to new configuration format."""
        builder = ConfigurationBuilder()

        # Map required fields - handle None values safely
        cluster_filter = initialized.get('cluster_filter')
        if cluster_filter is not None:
            builder.with_cluster_filter(cluster_filter)

        text_filter_type = initialized.get('text_filter_type')
        if text_filter_type is not None:
            builder.with_filter_type(text_filter_type)

        text_filter = initialized.get('text_filter')
        if text_filter is not None:
            builder.with_text_filter(text_filter)

        should_slice_clusters = initialized.get('should_slice_clusters')
        if should_slice_clusters is not None:
            builder.with_should_slice_clusters(should_slice_clusters)

        # Map optional slicing fields
        src_start = initialized.get('src_start_cluster_text')
        if src_start is not None:
            builder.with_src_start_cluster_text(src_start)

        src_end = initialized.get('src_end_cluster_text')
        if src_end is not None:
            builder.with_src_end_cluster_text(src_end)

        ref_start = initialized.get('ref_start_cluster_text')
        if ref_start is not None:
            builder.with_ref_start_cluster_text(ref_start)

        ref_end = initialized.get('ref_end_cluster_text')
        if ref_end is not None:
            builder.with_ref_end_cluster_text(ref_end)

        return builder.build()
