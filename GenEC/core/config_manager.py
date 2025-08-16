"""Module for managing configurations in GenEC."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from GenEC import utils
from GenEC.core import ConfigOptions, PositionalFilterType
from GenEC.core.manage_io import InputManager, YES_INPUT
from GenEC.core.prompts import Section, Key, create_prompt
from GenEC.core.types.preset_config import Finalized, Initialized


@dataclass
class Configuration:
    """
    Finalized configuration tied to a preset and target file.

    Each Configuration object stores the finalized settings
    derived from a preset, along with the preset name, target file, and optional group.

    Attributes
    ----------
    config : Finalized
        The finalized configuration object.
    preset : str
        The name of the preset used to generate this configuration.
    target_file : str
        The target file associated with this configuration.
    group : str, optional
        The group name of the preset, by default ''.
    """

    config: Finalized
    preset: str
    target_file: str
    group: str = ''


class ConfigManager:
    """
    Manages preset configuration loading, processing, and finalization.

    This class supports loading single or multiple presets,
    resolving placeholders in target files, and interactive configuration setup.
    Configurations are finalized for downstream processing.
    """

    def __init__(self,
                 preset_param: Optional[dict[str, str]] = None,
                 presets_directory: Optional[str] = None,
                 target_variables: Optional[dict[str, str]] = None) -> None:
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
        """
        if presets_directory:
            self.presets_directory = Path(presets_directory)
        else:
            self.presets_directory = Path(__file__).parent.parent / 'presets'
        self.configurations: list[Configuration] = []

        if preset_param:
            if preset_param['type'] == 'preset':
                self.set_config(preset_param['value'])
            elif preset_param['type'] == 'preset-list':
                self.configurations.extend(self.load_presets(preset_param['value'], target_variables))
            else:
                raise ValueError(f"{preset_param['type']} is not a valid preset parameter type.")
        else:
            self.set_config()

    @staticmethod
    def parse_preset_param(preset_param: str) -> tuple[str, Optional[str]]:
        """
        Parse a preset string into file and preset components.

        Parameters
        ----------
        preset_param : str
            The preset string, optionally in the format 'file/preset'.

        Returns
        -------
        tuple[str, Optional[str]]
            Tuple containing file name and preset name (or None if not provided).
        """
        if '/' not in preset_param:
            return preset_param, None
        else:
            return tuple(preset_param.split('/', 1))  # type: ignore[return-value]  # Always returns 2 items

    def load_presets(self, presets_list_target: str, target_variables: Optional[dict[str, str]] = None) -> list[Configuration]:  # pragma: no cover
        """
        Load multiple presets from a YAML file and process them into configurations.

        Parameters
        ----------
        presets_list_target : str
            The name of the presets list YAML file (without extension).
        target_variables : Optional[dict[str, str]], optional
            Variables used to replace placeholders in target file paths, by default None.

        Returns
        -------
        list[Configuration]
            A list of processed Configuration objects.
        """
        presets_list_file_path = self.presets_directory / f'{presets_list_target}.yaml'
        presets_list = utils.read_yaml_file(presets_list_file_path)
        presets_per_file = self._group_presets_by_file(presets_list, target_variables)
        return self._collect_presets(presets_per_file)

    def _group_presets_by_file(self,
                               presets_list: dict[str, list[dict[str, str]]],
                               target_variables: Optional[dict[str, str]] = None
                               ) -> dict[str, list[dict[str, str]]]:
        """
        Group presets by target file and apply variable substitutions.

        Parameters
        ----------
        presets_list : dict[str, list[dict[str, str]]]
            Dictionary mapping preset groups to lists of preset entries.
        target_variables : Optional[dict[str, str]], optional
            Variables to replace placeholders in target file paths, by default None.

        Returns
        -------
        dict[str, list[dict[str, str]]]
            Dictionary mapping target files to their preset entries.
        """
        presets_per_target: dict[str, list[dict[str, str]]] = defaultdict(list)
        for group, presets in presets_list.items():
            for entry in presets:
                target_file = entry.get('target', '')
                if target_variables:
                    try:
                        target_file = target_file.format(**target_variables)
                    except KeyError as e:
                        print(f'Missing target variable for placeholder {e} in target [{target_file}]')
                        continue
                preset = entry.get('preset', '')
                if not preset:
                    print(f'Preset missing in entry: {entry}')
                    continue
                file_name, preset_name = self.parse_preset_param(preset)
                if not preset_name:
                    print(f'Preset name missing in entry: {entry}')
                    continue
                presets_per_target[target_file].append({
                    'preset_file': file_name,
                    'preset_name': preset_name,
                    'target_file': target_file,
                    'preset_group': group
                })
        return presets_per_target

    def _collect_presets(self, presets_per_target: dict[str, list[dict[str, str]]]) -> list[Configuration]:
        """
        Process grouped presets into Configuration objects.

        Parameters
        ----------
        presets_per_target : dict[str, list[dict[str, str]]]
            Dictionary mapping target files to preset entries.

        Returns
        -------
        list[Configuration]
            List of Configuration objects.

        Raises
        ------
        ValueError
            If no valid configurations could be created.
        """
        configurations: list[Configuration] = []
        for target_file, preset_entries in presets_per_target.items():
            for entry in preset_entries:
                result = self._process_preset_entry(entry, target_file)
                if result:
                    configurations.append(result)

        if not configurations:
            raise ValueError('None of the provided presets were found.')
        return configurations

    def _process_preset_entry(self, entry: dict[str, str], target_file: str) -> Optional[Configuration]:
        """
        Finalize a single preset entry into a Configuration.

        Parameters
        ----------
        entry : dict[str, str]
            Preset entry containing file, name, target file, and group.
        target_file : str
            The target file associated with this preset.

        Returns
        -------
        Optional[Configuration]
            Finalized Configuration, or None if the preset does not exist.
        """
        file_name = entry['preset_file']
        preset_name = entry['preset_name']
        loaded_presets = self.load_preset_file(file_name)
        if preset_name not in loaded_presets:
            print(f'preset {preset_name} not found in {file_name}. Skipping...')
            return None
        config = loaded_presets[preset_name]
        finalized_config = self._finalize_config(config)
        return Configuration(
            config=finalized_config,
            preset=f'{file_name}/{preset_name}',
            target_file=target_file,
            group=entry.get('preset_group', ''))

    def load_preset(self, preset_target: str) -> Initialized:
        """
        Load a single preset, optionally prompting the user if multiple presets exist.

        Parameters
        ----------
        preset_target : str
            The preset string in the format 'file/preset' or just 'file'.

        Returns
        -------
        Initialized
            The loaded and initialized preset configuration.

        Raises
        ------
        ValueError
            If the specified preset does not exist in the file.
        """
        preset_file, preset_name = self.parse_preset_param(preset_target)
        presets = self.load_preset_file(preset_file)
        if not preset_name:
            if len(presets) == 1:
                preset_name = next(iter(presets))
            else:
                preset_name = InputManager.ask_mpc_question('Please choose a preset:\n', list(presets.keys()))

        if preset_name not in presets:
            raise ValueError(f'preset {preset_name} not found in {preset_file}')

        return presets[preset_name]

    def load_preset_file(self, preset_file: str) -> dict[str, Initialized]:
        """
        Load all presets from a YAML file.

        Parameters
        ----------
        preset_file : str
            Name of the preset file (without .yaml extension).

        Returns
        -------
        dict[str, Initialized]
            A dictionary mapping preset names to their Initialized configurations.

        Raises
        ------
        ValueError
            If the file does not contain any presets.
        """
        presets_file_path = self.presets_directory / f'{preset_file}.yaml'
        presets = utils.read_yaml_file(presets_file_path)

        if not presets or len(presets) == 0:
            raise ValueError(f'presets file {presets_file_path} does not contain any presets')

        return presets

    def _set_simple_options(self, config: Initialized):
        """
        Set basic configuration options interactively via InputManager.

        Parameters
        ----------
        config : Initialized
            The configuration object to modify.
        """
        config[ConfigOptions.CLUSTER_FILTER.value] = InputManager.set_cluster_filter(config)
        config[ConfigOptions.TEXT_FILTER_TYPE.value] = InputManager.set_text_filter_type(config)
        config[ConfigOptions.TEXT_FILTER.value] = InputManager.set_text_filter(config)
        config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] = InputManager.set_should_slice_clusters(config)

    def _set_cluster_text_options(self, config: Initialized):
        """
        Set cluster text options interactively if slicing clusters is enabled.

        Parameters
        ----------
        config : Initialized
            The configuration object to modify.
        """
        cluster_text_options = [
            (ConfigOptions.SRC_START_CLUSTER_TEXT.value, 'start', 'SRC'),
            (ConfigOptions.SRC_END_CLUSTER_TEXT.value, 'end', 'SRC'),
            (ConfigOptions.REF_START_CLUSTER_TEXT.value, 'start', 'REF'),
            (ConfigOptions.REF_END_CLUSTER_TEXT.value, 'end', 'REF'),
        ]
        for option_key, position, src_or_ref in cluster_text_options:
            if not config.get(option_key):
                config[option_key] = InputManager.set_cluster_text(config, option_key, position, src_or_ref)

    def set_config(self, preset: str = '', target_file: str = '') -> None:
        """
        Set a configuration using a preset or interactively.

        Parameters
        ----------
        preset : str, optional
            Preset string in 'file/preset' format. If empty, interactive setup is used.
        target_file : str, optional
            Associated target file name, by default ''.
        """
        if preset:
            config: Initialized = self.load_preset(preset)
        else:
            config: Initialized = Initialized(**{option.value: None for option in ConfigOptions})
            self._set_simple_options(config)

        if config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value):
            self._set_cluster_text_options(config)

        self.configurations.append(Configuration(self._finalize_config(config), preset, target_file))

    def _finalize_config(self, config: Initialized) -> Finalized:
        """
        Convert an Initialized configuration into a finalized configuration.

        Parameters
        ----------
        config : Initialized
            The initialized configuration object.

        Returns
        -------
        Finalized
            The finalized configuration ready for use.
        """
        cluster_filter = config.get(ConfigOptions.CLUSTER_FILTER.value)
        text_filter_type = config.get(ConfigOptions.TEXT_FILTER_TYPE.value)
        text_filter = config.get(ConfigOptions.TEXT_FILTER.value)
        should_slice_clusters = config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value)

        assert isinstance(cluster_filter, str)
        assert isinstance(text_filter_type, str)
        assert isinstance(text_filter, (str, list, PositionalFilterType))
        assert isinstance(should_slice_clusters, bool)

        return Finalized(
            cluster_filter=cluster_filter,
            text_filter_type=text_filter_type,
            text_filter=text_filter,
            should_slice_clusters=should_slice_clusters,
            src_start_cluster_text=config.get(ConfigOptions.SRC_START_CLUSTER_TEXT.value),
            src_end_cluster_text=config.get(ConfigOptions.SRC_END_CLUSTER_TEXT.value),
            ref_start_cluster_text=config.get(ConfigOptions.REF_START_CLUSTER_TEXT.value),
            ref_end_cluster_text=config.get(ConfigOptions.REF_END_CLUSTER_TEXT.value)
        )

    def should_store_configuration(self) -> bool:
        """
        Prompt the user to decide whether the current configuration should be saved.

        Returns
        -------
        bool
            True if the configuration should be saved, False otherwise.
        """
        return InputManager.ask_open_question(create_prompt(Section.WRITE_CONFIG, Key.REQUEST_SAVE)) in YES_INPUT

    def create_new_preset(self) -> None:
        """Create a preset from the configuration to be written to a file."""
        config = self.configurations[0].config
        preset_name = ''
        file_name = ''

        while not preset_name:
            preset_name = InputManager.ask_open_question(create_prompt(Section.WRITE_CONFIG, Key.NEW_PRESET_NAME)).strip()
            if not preset_name:
                print(create_prompt(Section.WRITE_CONFIG, Key.INVALID_PRESET_NAME))
                continue

        file_name = InputManager.ask_open_question(create_prompt(Section.WRITE_CONFIG, Key.DESTINATION_FILE_NAME, presets_directory=self.presets_directory))

        file_path = Path(file_name).with_suffix('.yaml')
        if not file_path.is_absolute():
            file_path = self.presets_directory / file_path

        new_preset = {preset_name: config}

        if file_path.exists():
            print(create_prompt(Section.WRITE_CONFIG, Key.DESTINATION_FILE_FOUND, file_path=file_path))
            yaml_data = utils.convert_to_yaml(new_preset)
            utils.write_txt('\n' + yaml_data, file_path, mode='a')
        else:
            print(create_prompt(Section.WRITE_CONFIG, Key.DESTINATION_FILE_NOT_FOUND, file_path=file_path))
            utils.write_yaml(new_preset, file_path)
