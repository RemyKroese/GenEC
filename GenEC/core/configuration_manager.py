"""Module for managing configurations in GenEC."""

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import is_dataclass, asdict
from pathlib import Path
from typing import Optional, TypeVar, cast, Any
import sys

from rich.console import Console

from GenEC import utils
from GenEC.core.configuration import BaseConfiguration
from GenEC.core.configuration_builder import ConfigurationBuilder
from GenEC.core.prompts import Section, Key, create_prompt
from GenEC.core.specs import ConfigOptions, PositionalFilterType, TextFilterTypes

console = Console()
YES_INPUT = ['yes', 'y']

T = TypeVar('T')


class ConfigurationManager(ABC):
    """
    Manages preset configuration loading, processing, and finalization.

    This class supports loading single or multiple presets,
    resolving placeholders in target files, and interactive configuration setup.
    Configurations are finalized for downstream processing.
    """

    def __init__(self,
                 presets_directory: Optional[str] = None) -> None:
        """
        Initialize the configuration manager. Configuration(s) are created separately.

        Parameters
        ----------
        presets_directory : Optional[str], optional
            Path to the directory containing preset YAML files.
            Defaults to the 'presets' directory in the package root.
        """
        if presets_directory:
            self.presets_directory = Path(presets_directory)
        else:
            self.presets_directory = Path(__file__).parent.parent / 'presets'
        self.configurations: list[BaseConfiguration] = []

    # User Interaction Methods
    def ask_open_question(self, prompt: str) -> str:
        """
        Prompt the user with an open-ended question.

        Parameters
        ----------
        prompt : str
            The message to display to the user.

        Returns
        -------
        str
            The user's input.
        """
        console.print(prompt, end='')
        return input()

    def ask_mpc_question(self, prompt: str, options: list[str]) -> str:
        """
        Prompt the user with a multiple-choice question.

        Parameters
        ----------
        prompt : str
            The message to display to the user.
        options : list[str]
            The list of selectable options.

        Returns
        -------
        str
            The selected option from the list.
        """
        console.print(prompt)
        console.print(create_prompt(Section.USER_CHOICE, Key.EXIT_OPTION))
        for i, option in enumerate(options, 1):
            console.print(f'{i}. {option}')

        choice = self._get_user_choice(len(options))

        if choice == 0:
            sys.exit()  # Exit the script
        else:
            return options[choice - 1]

    def _get_user_choice(self, max_choice: int) -> int:
        """
        Get a numeric choice from the user within a specified range.

        Parameters
        ----------
        max_choice : int
            The maximum valid choice value.

        Returns
        -------
        int
            The user's chosen number within the range [0, max_choice].
        """
        while True:
            try:
                choice = int(input(create_prompt(Section.USER_CHOICE, Key.CHOICE)))
                if 0 <= choice <= max_choice:
                    return choice
                console.print(create_prompt(Section.USER_CHOICE, Key.INVALID_CHOICE))
            except ValueError:
                console.print(create_prompt(Section.USER_CHOICE, Key.INVALID_CHOICE))

    def group_presets_by_file(self,
                              presets_list: dict[str, list[dict[str, str]]],
                              target_variables: Optional[dict[str, str]] = None
                              ) -> dict[str, list[dict[str, str]]]:
        """
        Group preset entries by their target file after variable substitution.

        Parameters
        ----------
        presets_list : dict[str, list[dict[str, str]]]
            Dictionary containing preset groups and their entries.
        target_variables : Optional[dict[str, str]], optional
            Variables for template substitution in target file paths.

        Returns
        -------
        dict[str, list[dict[str, str]]]
            Dictionary mapping target files to their preset entries.
        """
        grouped_presets: dict[str, list[dict[str, str]]] = defaultdict(list)

        for group_name, preset_entries in presets_list.items():
            for preset_entry in preset_entries:
                target_file = preset_entry['target']

                # Apply variable substitution if provided
                if target_variables:
                    for var_name, var_value in target_variables.items():
                        target_file = target_file.replace(f'{{{var_name}}}', var_value)

                # Add group information to preset entry
                preset_entry_with_group = preset_entry.copy()
                preset_entry_with_group[ConfigOptions.GROUP.value] = group_name
                preset_entry_with_group['target'] = target_file

                grouped_presets[target_file].append(preset_entry_with_group)

        return dict(grouped_presets)

    def load_preset(self, preset_target: str) -> dict[str, Any]:
        """
        Load a single preset configuration from YAML files.

        Parameters
        ----------
        preset_target : str
            Preset identifier in format 'filename/preset_name' or just 'preset_name'.

        Returns
        -------
        dict[str, Any]
            The loaded preset configuration as a dictionary.
        """
        if '/' in preset_target:
            preset_file, preset_name = preset_target.split('/', 1)
        else:
            preset_file = preset_target
            preset_name = None

        presets = self.load_preset_file(preset_file)

        if preset_name:
            if preset_name not in presets:
                available_presets = list(presets.keys())
                raise ValueError(f"Preset '{preset_name}' not found in file '{preset_file}'. Available presets: {available_presets}")
            return presets[preset_name]

        if len(presets) == 1:
            return next(iter(presets.values()))

        preset_options = list(presets.keys())
        chosen_preset = self.ask_mpc_question(
            f'Multiple presets found in {preset_file}. Choose one:',
            preset_options
        )
        return presets[chosen_preset]

    def load_preset_file(self, preset_file: str) -> dict[str, dict[str, Any]]:
        """
        Load all presets from a single YAML file.

        Parameters
        ----------
        preset_file : str
            Name of the preset file (without .yaml extension).

        Returns
        -------
        dict[str, dict[str, Any]]
            Dictionary mapping preset names to their configurations.
        """
        preset_file_path = self.presets_directory / f'{preset_file}.yaml'

        if not preset_file_path.exists():
            raise FileNotFoundError(f'Preset file not found: {preset_file_path}')

        presets_data = utils.read_yaml_file(preset_file_path)

        if not isinstance(presets_data, dict):
            raise ValueError(f'Invalid preset file format in {preset_file_path}')

        # Convert to ensure proper typing
        presets: dict[str, dict[str, Any]] = cast(dict[str, dict[str, Any]], presets_data)
        return presets

    # Removed set_config; derived classes must implement their own config logic

    @abstractmethod
    def initialize_configuration(self) -> None:
        """
        Initialize configuration(s) for the specific workflow.

        Derived classes must implement this method to create their configurations
        based on their workflow type (basic, preset, or preset-list).
        """


class BasicConfigurationManager(ConfigurationManager):
    """Configuration manager for single configuration workflows."""

    def initialize_configuration(self) -> None:
        """Create configuration for basic workflow."""
        config = self._build_interactive_configuration()
        self.configurations = [config]

    def _build_interactive_configuration(self) -> BaseConfiguration:
        """
        Build a configuration by prompting the user for all values.

        Returns
        -------
        BaseConfiguration
            The built configuration
        """
        builder = ConfigurationBuilder()

        # Configure filter type and basic settings
        filter_type = self.ask_mpc_question(
            create_prompt(Section.SET_CONFIG, Key.TEXT_FILTER_TYPE),
            [t.value for t in TextFilterTypes]
        )
        builder.with_filter_type(filter_type)

        # Configure cluster filter
        cluster_filter = self.ask_open_question(
            create_prompt(Section.SET_CONFIG, Key.CLUSTER_FILTER_REGEX)
        )
        if not cluster_filter:
            cluster_filter = r'\n'  # Default if empty
        builder.with_cluster_filter(cluster_filter)

        # Configure text filter based on type
        self._configure_text_filter(builder, filter_type)

        # Configure cluster slicing
        self._configure_cluster_slicing(builder)

        return builder.build()

    def _configure_text_filter(self, builder: ConfigurationBuilder, filter_type: str) -> None:
        """
        Configure the text filter based on the selected filter type.

        Parameters
        ----------
        builder : ConfigurationBuilder
            The configuration builder to update
        filter_type : str
            The selected text filter type
        """
        if filter_type == TextFilterTypes.REGEX.value:
            self._configure_regex_filter(builder)
        elif filter_type == TextFilterTypes.REGEX_LIST.value:
            self._configure_regex_list_filter(builder)
        elif filter_type == TextFilterTypes.POSITIONAL.value:
            self._configure_positional_filter(builder)

    def _configure_regex_filter(self, builder: ConfigurationBuilder) -> None:
        """Configure a regex text filter."""
        regex_pattern = self.ask_open_question(
            create_prompt(Section.SET_CONFIG, Key.REGEX_FILTER)
        )
        builder.with_text_filter(regex_pattern)

    def _configure_regex_list_filter(self, builder: ConfigurationBuilder) -> None:
        """Configure a regex list text filter."""
        patterns: list[str] = []
        search_count = 1
        while True:
            pattern = self.ask_open_question(
                create_prompt(Section.SET_CONFIG, Key.REGEX_LIST_FILTER, search=search_count)
            )
            if not pattern:
                break
            patterns.append(pattern)
            search_count += 1

            # Ask if user wants to add another pattern
            continue_response = self.ask_open_question(
                create_prompt(Section.SET_CONFIG, Key.REGEX_LIST_CONTINUE)
            ).lower()
            if continue_response not in ('yes', 'y'):
                break
        builder.with_text_filter(patterns)

    def _configure_positional_filter(self, builder: ConfigurationBuilder) -> None:
        """Configure a positional text filter."""
        separator = self.ask_open_question(
            create_prompt(Section.SET_CONFIG, Key.POSITIONAL_SEPARATOR)
        )
        line_str = self.ask_open_question(
            create_prompt(Section.SET_CONFIG, Key.POSITIONAL_LINE)
        )
        occurrence_str = self.ask_open_question(
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

    def _configure_cluster_slicing(self, builder: ConfigurationBuilder) -> None:
        """Configure cluster slicing settings."""
        should_slice = self.ask_open_question(
            create_prompt(Section.SET_CONFIG, Key.SHOULD_SLICE_CLUSTERS)
        ).lower() in ('y', 'yes')
        builder.with_should_slice_clusters(should_slice)

        if should_slice:
            builder.with_src_start_cluster_text(
                self.ask_open_question(
                    create_prompt(Section.SET_CONFIG, Key.SOURCE_START_CLUSTER_TEXT)
                ) or None
            )
            builder.with_src_end_cluster_text(
                self.ask_open_question(
                    create_prompt(Section.SET_CONFIG, Key.SOURCE_END_CLUSTER_TEXT)
                ) or None
            )
            builder.with_ref_start_cluster_text(
                self.ask_open_question(
                    create_prompt(Section.SET_CONFIG, Key.REFERENCE_START_CLUSTER_TEXT)
                ) or None
            )
            builder.with_ref_end_cluster_text(
                self.ask_open_question(
                    create_prompt(Section.SET_CONFIG, Key.REFERENCE_END_CLUSTER_TEXT)
                ) or None
            )

    def should_store_configuration(self) -> bool:
        """
        Ask user if they want to store the current configuration as a preset.

        Returns
        -------
        bool
            True if the configuration should be saved, False otherwise.
        """
        return self.ask_open_question(create_prompt(Section.WRITE_CONFIG, Key.REQUEST_SAVE)) in YES_INPUT

    def _get_preset_data(self) -> dict[str, Any]:
        """
        Generate preset data from the current configuration.

        Returns only non-None values in a format suitable for YAML serialization.
        Dataclass objects are converted to dictionaries.

        Returns
        -------
        dict[str, Any]
            Clean configuration data for preset generation.
        """
        if not self.configurations:
            return {}

        # Get the latest configuration
        latest_config = self.configurations[-1]

        # New dataclass config format
        config_dict = latest_config.to_dict()

        # Convert any dataclass objects in the text_filter field
        if 'text_filter' in config_dict:
            text_filter = config_dict['text_filter']
            if text_filter is not None and is_dataclass(text_filter):
                config_dict['text_filter'] = asdict(text_filter)

        # Filter out None values for clean preset output
        return {k: v for k, v in config_dict.items() if v is not None}

    def create_new_preset(self) -> None:
        """Create a preset from the configuration to be written to a file."""
        if not self.configurations:
            raise ValueError("No configuration available for preset creation")

        preset_name = ''
        file_name = ''

        while not preset_name:
            preset_name = self.ask_open_question(create_prompt(
                Section.WRITE_CONFIG, Key.NEW_PRESET_NAME)).strip()
            if not preset_name:
                console.print(create_prompt(Section.WRITE_CONFIG, Key.INVALID_PRESET_NAME))

        file_name = self.ask_open_question(create_prompt(
            Section.WRITE_CONFIG, Key.DESTINATION_FILE_NAME))

        preset_file_path = self.presets_directory / f'{file_name}.yaml'
        preset_data = self._get_preset_data()

        if not preset_file_path.exists():
            console.print(create_prompt(Section.WRITE_CONFIG, Key.DESTINATION_FILE_NOT_FOUND,
                                        file_path=preset_file_path))
            utils.write_yaml({preset_name: preset_data}, preset_file_path)
        else:
            console.print(create_prompt(Section.WRITE_CONFIG, Key.DESTINATION_FILE_FOUND,
                                        file_path=preset_file_path))
            utils.append_to_file(f'\n{preset_name}:\n', preset_file_path)
            preset_yaml_data = utils.convert_to_yaml(preset_data)
            utils.append_to_file(preset_yaml_data, preset_file_path)


class PresetConfigurationManager(ConfigurationManager):
    """Configuration manager for preset workflows."""

    def __init__(self, presets_directory: Optional[str] = None, preset: str = '') -> None:
        """
        Initialize the preset configuration manager.

        Parameters
        ----------
        presets_directory : Optional[str], optional
            Path to the directory containing preset YAML files.
        preset : str, optional
            Preset identifier in format 'filename/preset_name' or just 'preset_name'.
        """
        super().__init__(presets_directory)
        self.preset = preset

    def initialize_configuration(self) -> None:
        """Load configuration from preset."""
        config = self._build_preset_configuration(self.preset)
        self.configurations = [config]

    def _build_preset_configuration(self, preset: str, target_file: str = '') -> BaseConfiguration:
        """
        Create a preset workflow configuration.

        Parameters
        ----------
        preset : str
            Preset string in 'file/preset' format
        target_file : str, optional
            Associated target file name, by default ''

        Returns
        -------
        BaseConfiguration
            Configuration for preset workflow with metadata
        """
        extraction_config = self._build_from_preset(preset)

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

    def _build_from_preset(self, preset_target: str) -> BaseConfiguration:
        """Build configuration from a preset."""
        initialized_config = self.load_preset(preset_target)
        return self._convert_initialized_to_config(initialized_config)

    def _convert_initialized_to_config(self, initialized: dict[str, Any]) -> BaseConfiguration:
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


class BatchConfigurationManager(ConfigurationManager):
    """Configuration manager for preset-list workflows."""

    def __init__(self, presets_directory: Optional[str] = None,
                 preset_list: str = '',
                 target_variables: Optional[dict[str, str]] = None) -> None:
        """
        Initialize the batch configuration manager.

        Parameters
        ----------
        presets_directory : Optional[str], optional
            Path to the directory containing preset YAML files.
        preset_list : str, optional
            The name of the presets list YAML file (without extension).
        target_variables : Optional[dict[str, str]], optional
            Variables used to replace placeholders in target file paths.
        """
        super().__init__(presets_directory)
        self.preset_list = preset_list
        self.target_variables = target_variables

    def initialize_configuration(self) -> None:
        """Load configurations from preset list."""
        self.configurations = self._create_preset_list_configs(self.preset_list, self.target_variables)

    def _create_preset_list_configs(self,
                                    presets_list_target: str,
                                    target_variables: Optional[dict[str, str]] = None) -> list[BaseConfiguration]:
        """
        Create preset-list workflow configurations.

        Parameters
        ----------
        presets_list_target : str
            The name of the presets list YAML file (without extension)
        target_variables : Optional[dict[str, str]], optional
            Variables used to replace placeholders in target file paths

        Returns
        -------
        list[BaseConfiguration]
            List of configurations for preset-list workflow with full metadata
        """
        presets_list = utils.read_yaml_file(self.presets_directory / f'{presets_list_target}.yaml')
        presets_per_file = self.group_presets_by_file(presets_list, target_variables)

        configs = []
        for target_file, preset_entries in presets_per_file.items():
            for entry in preset_entries:
                preset_target = entry[ConfigOptions.PRESET.value]
                group = entry.get('group', '')

                try:
                    # preset_target is already in the format 'file/preset_name'
                    extraction_config = self._build_from_preset(preset_target)

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

    def _build_from_preset(self, preset_target: str) -> BaseConfiguration:
        """Build configuration from a preset."""
        initialized_config = self.load_preset(preset_target)
        return self._convert_initialized_to_config(initialized_config)

    def _convert_initialized_to_config(self, initialized: dict[str, Any]) -> BaseConfiguration:
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

    def group_presets_by_file(self,
                              presets_list: dict[str, list[dict[str, str]]],
                              target_variables: Optional[dict[str, str]] = None
                              ) -> dict[str, list[dict[str, str]]]:
        """
        Group preset entries by their target file after variable substitution.

        Parameters
        ----------
        presets_list : dict[str, list[dict[str, str]]]
            Dictionary containing preset groups and their entries.
        target_variables : Optional[dict[str, str]], optional
            Variables for template substitution in target file paths.

        Returns
        -------
        dict[str, list[dict[str, str]]]
            Dictionary mapping target files to their preset entries.
        """
        grouped_presets: dict[str, list[dict[str, str]]] = defaultdict(list)

        for group_name, preset_entries in presets_list.items():
            for preset_entry in preset_entries:
                target_file = preset_entry['target']

                # Apply variable substitution if provided
                if target_variables:
                    for var_name, var_value in target_variables.items():
                        target_file = target_file.replace(f'{{{var_name}}}', var_value)

                # Add group information to preset entry
                preset_entry_with_group = preset_entry.copy()
                preset_entry_with_group[ConfigOptions.GROUP.value] = group_name
                preset_entry_with_group['target'] = target_file

                grouped_presets[target_file].append(preset_entry_with_group)

        return dict(grouped_presets)
