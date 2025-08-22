"""Module for managing configurations in GenEC."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Optional, Union, TypeVar, Callable, cast, Any

from rich.console import Console

from GenEC import utils
from GenEC.core import ConfigOptions, PositionalFilterType, TextFilterTypes
from GenEC.core.prompts import Section, Key, create_prompt
from GenEC.core.types.preset_config import Finalized, Initialized
from GenEC.core.input_strategies import get_input_strategy


console = Console()
YES_INPUT = ['yes', 'y']

T = TypeVar('T')


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
        self.configurations: list[Configuration] = []
        self.initialized_config: Optional[Initialized] = None

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
    def _resolve_config_value(self, config: Initialized, key: ConfigOptions, prompt_func: Callable[[], T]) -> T:
        """
        Resolve configuration value with fallback to user prompt.

        Parameters
        ----------
        config : Initialized
            The configuration object containing preset values.
        key : ConfigOptions
            The configuration key to check.
        prompt_func : Callable[[], T]
            Function to prompt user for value if not in config.

        Returns
        -------
        T
            The resolved configuration value.
        """
        if value := config.get(key.value):
            return cast(T, value)
        return prompt_func()

    def _ask_open_question(self, prompt: str) -> str:
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

    def _ask_mpc_question(self, prompt: str, options: list[str]) -> str:
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
        console.print('\n')

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
                console.print(create_prompt(Section.USER_CHOICE, Key.CHOICE, max_index=max_choice), end='')
                choice = int(input())
                if not 0 <= choice <= max_choice:
                    raise ValueError
                return choice
            except ValueError:
                console.print(create_prompt(Section.USER_CHOICE, Key.INVALID_CHOICE))

    # Configuration Collection Methods
    def _collect_cluster_filter(self, config: Initialized) -> str:
        """
        Get or request the cluster splitting character(s) from the user.

        Parameters
        ----------
        config : Initialized
            The configuration object containing preset values.

        Returns
        -------
        str
            The character(s) used to split text clusters.
        """
        def get_cluster_filter() -> str:
            user_input = self._ask_open_question(create_prompt(Section.SET_CONFIG, Key.CLUSTER_FILTER))
            return user_input or '\\n'  # Store escaped string for display/presets

        result = self._resolve_config_value(config, ConfigOptions.CLUSTER_FILTER, get_cluster_filter)
        return result

    def _collect_text_filter_type(self, config: Initialized) -> str:
        """
        Get or request the text filter type from the user.

        Parameters
        ----------
        config : Initialized
            The configuration object containing preset values.

        Returns
        -------
        str
            The selected text filter type, e.g., 'regex', 'positional', or 'regex-list'.
        """
        return self._resolve_config_value(
            config, ConfigOptions.TEXT_FILTER_TYPE,
            lambda: self._ask_mpc_question(
                create_prompt(Section.SET_CONFIG, Key.TEXT_FILTER_TYPE),
                [t.value for t in TextFilterTypes]))

    def _collect_text_filter(self, config: Initialized) -> Union[str, PositionalFilterType, list[str], dict[str, Any]]:
        """
        Get or request the actual text filter based on the selected filter type.

        Parameters
        ----------
        config : Initialized
            The configuration object containing preset values.

        Returns
        -------
        Union[str, PositionalFilterType, list[str], dict[str, Any]]
            The configured text filter, which can be a regex string, a positional filter object,
            a dict (for positional filters in initialized config), or a list of regex strings.
        """
        return self._resolve_config_value(
            config, ConfigOptions.TEXT_FILTER, lambda: self._request_text_filter(config))

    def _collect_should_slice_clusters(self, config: Initialized) -> bool:
        """
        Determine if only a subsection of clusters should be compared.

        Parameters
        ----------
        config : Initialized
            The configuration object containing preset values.

        Returns
        -------
        bool
            True if a subsection of clusters should be compared, False otherwise.
        """
        # Special handling for boolean since False is a valid value
        if (value := config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value)) is not None:
            return value

        response = self._ask_open_question(create_prompt(Section.SET_CONFIG, Key.SHOULD_SLICE_CLUSTERS)).lower()
        return response in YES_INPUT

    def _collect_cluster_text(self, config: Initialized, config_option: str, position: str, src_or_ref: str) -> str:
        """
        Get or request the text within a cluster for a specific subsection.

        Parameters
        ----------
        config : Initialized
            The configuration object containing preset values.
        config_option : str
            The configuration key to check for existing value.
        position : str
            Indicates where the subsection should be within the cluster (e.g., 'start' or 'end').
        src_or_ref : str
            Indicates whether this is source or reference cluster.

        Returns
        -------
        str
            The text input for the cluster subsection.
        """
        if value := config.get(config_option):
            return cast(str, value)
        return self._ask_open_question(create_prompt(Section.SET_CONFIG, Key.CLUSTER_TEXT, cluster=src_or_ref.lower(), position=position))

    def _request_text_filter(self, config: Initialized) -> Union[str, PositionalFilterType, list[str], dict[str, Any]]:
        """
        Request a text filter from the user according to the selected filter type.

        Parameters
        ----------
        config : Initialized
            The configuration object containing the filter type.

        Returns
        -------
        Union[str, PositionalFilterType, list[str], dict[str, Any]]
            The configured text filter, which can be a regex string, a positional filter object,
            a dict (for positional filters in initialized config), or a list of regex strings.

        Raises
        ------
        ValueError
            If the selected text filter type is not supported.
        """
        filter_type = config.get(ConfigOptions.TEXT_FILTER_TYPE.value)
        if not filter_type:
            raise ValueError("Text filter type must be set before requesting text filter")

        strategy = get_input_strategy(filter_type, self._ask_open_question)
        return strategy.collect_input(config)

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

        file_name, preset_name = preset_param.split('/', 1)
        return file_name, preset_name

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
        presets_list_file_path = self.presets_directory / \
            f'{presets_list_target}.yaml'
        presets_list = utils.read_yaml_file(presets_list_file_path)
        presets_per_file = self._group_presets_by_file(
            presets_list, target_variables)
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
                        console.print(f'Missing target variable for placeholder {e} in target [{target_file}]')
                        continue
                preset = entry.get('preset', '')
                if not preset:
                    console.print(f'Preset missing in entry: {entry}')
                    continue
                file_name, preset_name = self.parse_preset_param(preset)
                if not preset_name:
                    console.print(f'Preset name missing in entry: {entry}')
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

        try:
            loaded_presets = self.load_preset_file(file_name)
        except (FileNotFoundError, UnicodeDecodeError, ValueError) as e:
            console.print(create_prompt(Section.ERROR_HANDLING, Key.PRESET_LOAD_ERROR,
                                        preset=f'{file_name}/{preset_name}', error=str(e)))
            console.print(f'[yellow]Skipping preset {preset_name} from {file_name}[/yellow]')
            return None

        if preset_name not in loaded_presets:
            console.print(create_prompt(Section.ERROR_HANDLING, Key.PRESET_VALIDATION_ERROR,
                                        preset=f'{file_name}/{preset_name}',
                                        error=f'Preset "{preset_name}" not found in file'))
            console.print(f'[yellow]Skipping preset {preset_name} from {file_name}[/yellow]')
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
                preset_name = self._ask_mpc_question(
                    'Please choose a preset:\n', list(presets.keys()))

        if preset_name not in presets:
            raise ValueError(
                f'preset {preset_name} not found in {preset_file}')

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

        try:
            presets_data = utils.read_yaml_file(presets_file_path)
            presets: dict[str, Initialized] = cast(dict[str, Initialized], presets_data)

            if not presets or len(presets) == 0:
                raise ValueError(f'Preset file {presets_file_path} contains no presets')

            # Convert positional filter dictionaries to PositionalFilterType objects
            for preset_name, preset_config in presets.items():
                text_filter = preset_config.get('text_filter')
                if isinstance(text_filter, dict):
                    presets[preset_name]['text_filter'] = PositionalFilterType(**text_filter)

            return presets

        except FileNotFoundError:
            console.print(create_prompt(Section.ERROR_HANDLING, Key.FILE_READ_ERROR,
                                        file_path=presets_file_path, error="File not found"))
            raise
        except UnicodeDecodeError as e:
            console.print(create_prompt(Section.ERROR_HANDLING, Key.FILE_READ_ERROR,
                                        file_path=presets_file_path, error=f"File encoding error: {e.reason}"))
            raise
        except Exception as e:
            console.print(create_prompt(Section.ERROR_HANDLING, Key.PRESET_LOAD_ERROR,
                                        preset=preset_file, error=str(e)))
            raise

    def _set_simple_options(self, config: Initialized) -> None:
        """
        Set basic configuration options interactively.

        Parameters
        ----------
        config : Initialized
            The configuration object to modify.
        """
        config[ConfigOptions.TEXT_FILTER_TYPE.value] = self._collect_text_filter_type(
            config)
        config[ConfigOptions.CLUSTER_FILTER.value] = self._collect_cluster_filter(
            config)
        config[ConfigOptions.TEXT_FILTER.value] = self._collect_text_filter(
            config)
        config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] = self._collect_should_slice_clusters(
            config)

    def _set_cluster_text_options(self, config: Initialized) -> None:
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
                # Cast to dict to bypass TypedDict literal key requirement
                config_dict = cast(dict[str, Union[str, None]], config)
                config_dict[option_key] = self._collect_cluster_text(
                    config, option_key, position, src_or_ref)

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
            config = Initialized(
                cluster_filter=None,
                text_filter_type=None,
                text_filter=None,
                should_slice_clusters=None,
                src_start_cluster_text=None,
                src_end_cluster_text=None,
                ref_start_cluster_text=None,
                ref_end_cluster_text=None
            )
            self._set_simple_options(config)

        if config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value):
            self._set_cluster_text_options(config)

        # Store the initialized config before finalization for preset generation
        self.initialized_config = config.copy()

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
        should_slice_clusters = config.get(
            ConfigOptions.SHOULD_SLICE_CLUSTERS.value)

        assert isinstance(cluster_filter, str)
        assert isinstance(text_filter_type, str)
        assert isinstance(text_filter, (str, list, PositionalFilterType, dict))
        assert isinstance(should_slice_clusters, bool)

        # Convert dict positional filter to PositionalFilterType for processing
        final_text_filter: Union[str, list[str], PositionalFilterType]
        if isinstance(text_filter, dict) and text_filter_type == TextFilterTypes.POSITIONAL.value:
            final_text_filter = PositionalFilterType(**text_filter)
        else:
            # text_filter must be str, list, or PositionalFilterType at this point
            final_text_filter = cast(Union[str, list[str], PositionalFilterType], text_filter)

        return Finalized(
            cluster_filter=cluster_filter,
            text_filter_type=text_filter_type,
            text_filter=final_text_filter,
            should_slice_clusters=should_slice_clusters,
            src_start_cluster_text=config.get(
                ConfigOptions.SRC_START_CLUSTER_TEXT.value),
            src_end_cluster_text=config.get(
                ConfigOptions.SRC_END_CLUSTER_TEXT.value),
            ref_start_cluster_text=config.get(
                ConfigOptions.REF_START_CLUSTER_TEXT.value),
            ref_end_cluster_text=config.get(
                ConfigOptions.REF_END_CLUSTER_TEXT.value))

    def should_store_configuration(self) -> bool:
        """
        Prompt the user to decide whether the current configuration should be saved.

        Returns
        -------
        bool
            True if the configuration should be saved, False otherwise.
        """
        return self._ask_open_question(create_prompt(Section.WRITE_CONFIG, Key.REQUEST_SAVE)) in YES_INPUT

    def _get_preset_data(self) -> dict[str, Any]:
        """
        Extract clean preset data from initialized config.

        Returns only non-None values in a format suitable for YAML serialization.
        Positional filters are kept as dicts (no conversion needed).

        Returns
        -------
        dict[str, Any]
            Clean configuration data for preset generation.
        """
        if not self.initialized_config:
            return {}

        # Filter out None values for clean preset output
        return {k: v for k, v in self.initialized_config.items() if v is not None}

    def create_new_preset(self) -> None:
        """Create a preset from the configuration to be written to a file."""
        if not self.initialized_config:
            raise ValueError("No initialized config available for preset creation")

        preset_name = ''
        file_name = ''

        while not preset_name:
            preset_name = self._ask_open_question(create_prompt(
                Section.WRITE_CONFIG, Key.NEW_PRESET_NAME)).strip()
            if not preset_name:
                console.print(
                    create_prompt(
                        Section.WRITE_CONFIG,
                        Key.INVALID_PRESET_NAME))
                continue

        file_name = self._ask_open_question(create_prompt(Section.WRITE_CONFIG, Key.DESTINATION_FILE_NAME, presets_directory=self.presets_directory))

        file_path = Path(file_name).with_suffix('.yaml')
        if not file_path.is_absolute():
            file_path = self.presets_directory / file_path

        # Get clean preset data (only non-None values)
        preset_data = self._get_preset_data()
        new_preset = {preset_name: preset_data}

        if file_path.exists():
            console.print(create_prompt(Section.WRITE_CONFIG, Key.DESTINATION_FILE_FOUND, file_path=file_path))
            yaml_data = utils.convert_to_yaml(new_preset)
            utils.append_to_file('\n' + yaml_data, file_path)
        else:
            console.print(create_prompt(Section.WRITE_CONFIG, Key.DESTINATION_FILE_NOT_FOUND, file_path=file_path))
            utils.write_yaml(new_preset, file_path)
