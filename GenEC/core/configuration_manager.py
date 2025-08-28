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
from GenEC.core.configuration_factory import WorkflowConfigurationFactory
from GenEC.core.prompts import Section, Key, create_prompt
from GenEC.core.specs import ConfigOptions

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
                 preset_param: Optional[dict[str, str]] = None,
                 presets_directory: Optional[str] = None,
                 target_variables: Optional[dict[str, str]] = None,
                 auto_configure: bool = True) -> None:
        """
        Initialize the configuration manager and optionally load presets.

        Parameters
        ----------
        preset_param : Optional[dict[str, str]], optional
            Dictionary specifying a preset or preset list to load. Must include:
            - 'type': either 'preset' or 'preset-list'
            - 'value': the preset identifier or list name.
            If None, configuration is set interactively.
        presets_directory : Optional[str], optional
            Path to the directory containing preset YAML files.
            Defaults to the 'presets' directory in the package root.
        target_variables : Optional[dict[str, str]], optional
            Mapping of placeholder names to replacement values for target file paths.
            Applied when loading presets from a list.
        auto_configure : bool, optional
            Whether to automatically configure on initialization. Default True.
            Set to False for testing scenarios.
        """
        if presets_directory:
            self.presets_directory = Path(presets_directory)
        else:
            self.presets_directory = Path(__file__).parent.parent / 'presets'
        self.configurations: list[BaseConfiguration] = []

        if auto_configure:
            if preset_param:
                if preset_param['type'] == 'preset':
                    self.set_config(preset_param['value'])
                elif preset_param['type'] == 'preset-list':
                    self.configurations.extend(self.load_presets(preset_param['value'], target_variables))
                else:
                    raise ValueError(f"{preset_param['type']} is not a valid preset parameter type.")
            else:
                self.set_config()

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

    def load_presets(self, presets_list_target: str,
                     target_variables: Optional[dict[str, str]] = None) -> list[BaseConfiguration]:
        """
        Load multiple presets from a presets list configuration.

        Parameters
        ----------
        presets_list_target : str
            The name of the presets list YAML file (without extension).
        target_variables : Optional[dict[str, str]], optional
            Variables used to replace placeholders in target file paths.

        Returns
        -------
        list[BaseConfiguration]
            List of loaded and configured preset configurations.
        """
        return WorkflowConfigurationFactory.create_preset_list_configs(
            self, presets_list_target, target_variables
        )

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

    def set_config(self, preset: str = '', target_file: str = '') -> None:
        """
        Set up configuration either from preset or interactively.

        Parameters
        ----------
        preset : str, optional
            Preset identifier to load, by default ''
        target_file : str, optional
            Target file name for workflow metadata, by default ''
        """
        if preset:
            config = WorkflowConfigurationFactory.create_preset_config(self, preset, target_file)
        else:
            config = WorkflowConfigurationFactory.create_basic_config(self)

        self.configurations.append(config)

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


class BasicConfigurationManager(ConfigurationManager):
    """Configuration manager for single configuration workflows."""

    def __init__(self) -> None:
        self.configuration: BaseConfiguration


class PresetConfigurationManager(ConfigurationManager):
    """Configuration manager for preset workflows."""

    def __init__(self) -> None:
        self.configuration: BaseConfiguration


class BatchConfigurationManager(ConfigurationManager):
    """Configuration manager for preset-list workflows."""

    def __init__(self) -> None:
        self.configurations: list[BaseConfiguration] = []
