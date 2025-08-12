from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from GenEC import utils
from GenEC.core import ConfigOptions, PositionalFilterType
from GenEC.core.manage_io import InputManager
from GenEC.core.types.preset_config import Finalized, Initialized

YES_INPUT = ['yes', 'y']
NO_INPUT = ['no', 'n']


@dataclass
class Configuration:
    config: Finalized
    preset: str
    target_file: str
    group: str = ''


class ConfigManager:
    def __init__(self, preset_param: Optional[dict[str, str]] = None, presets_directory: Optional[str] = None) -> None:
        if presets_directory:
            self.presets_directory = Path(presets_directory)
        else:
            self.presets_directory = Path(__file__).parent.parent / 'presets'
        self.configurations: list[Configuration] = []

        if preset_param:
            if preset_param['type'] == 'preset':
                self.set_config(preset_param['value'])
            elif preset_param['type'] == 'preset-list':
                self.configurations.extend(self.load_presets(preset_param['value']))
            else:
                raise ValueError(f"{preset_param['type']} is not a valid preset parameter type.")
        else:
            self.set_config()

    @staticmethod
    def parse_preset_param(preset_param: str) -> tuple[str, Optional[str]]:
        if '/' not in preset_param:
            return preset_param, None
        else:
            return tuple(preset_param.split('/', 1))  # type: ignore[return-value]  # Always returns 2 items

    def load_presets(self, presets_list_target: str) -> list[Configuration]:  # pragma: no cover
        presets_list_file_path = self.presets_directory / f'{presets_list_target}.yaml'
        presets_list = utils.read_yaml_file(str(presets_list_file_path))
        presets_per_file = self._group_presets_by_file(presets_list)
        return self._collect_presets(presets_per_file)

    def _group_presets_by_file(self, presets_list: dict[str, list[dict[str, str]]]) -> dict[str, list[dict[str, str]]]:
        presets_per_target: dict[str, list[dict[str, str]]] = defaultdict(list)
        for group, presets in presets_list.items():
            for entry in presets:
                target_file = entry.get('target', '')
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
        file_name = entry['preset_file']
        preset_name = entry['preset_name']
        loaded_presets = self.load_preset_file(file_name)
        if preset_name not in loaded_presets:
            print(f'preset {preset_name} not found in {file_name}. Skipping...')
            return None
        config = loaded_presets[preset_name]
        config[ConfigOptions.CLUSTER_FILTER.value] = self._normalize_cluster_filter(config[ConfigOptions.CLUSTER_FILTER.value])
        finalized_config = self._finalize_config(config)
        return Configuration(
            config=finalized_config,
            preset=f'{file_name}/{preset_name}',
            target_file=target_file,
            group=entry.get('preset_group', ''))

    def load_preset(self, preset_target: str) -> Initialized:
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
        presets_file_path = self.presets_directory / f'{preset_file}.yaml'
        presets = utils.read_yaml_file(str(presets_file_path))

        if not presets or len(presets) == 0:
            raise ValueError(f'presets file {presets_file_path} does not contain any presets')

        return presets

    @staticmethod
    def _normalize_cluster_filter(cluster_filter: Optional[str]) -> str:
        if cluster_filter is None:
            return ''
        return cluster_filter.encode('utf-8').decode('unicode_escape')

    def _set_simple_options(self, config: Initialized):
        config[ConfigOptions.CLUSTER_FILTER.value] = InputManager.set_cluster_filter(config)
        config[ConfigOptions.TEXT_FILTER_TYPE.value] = InputManager.set_text_filter_type(config)
        config[ConfigOptions.TEXT_FILTER.value] = InputManager.set_text_filter(config)
        config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] = InputManager.set_should_slice_clusters(config)

    def _set_cluster_text_options(self, config: Initialized):
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
        if preset:
            config: Initialized = self.load_preset(preset)
        else:
            config: Initialized = Initialized(**{option.value: None for option in ConfigOptions})
            self._set_simple_options(config)

        if config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value):
            self._set_cluster_text_options(config)

        config[ConfigOptions.CLUSTER_FILTER.value] = self._normalize_cluster_filter(config[ConfigOptions.CLUSTER_FILTER.value])

        self.configurations.append(Configuration(self._finalize_config(config), preset, target_file))

    def _finalize_config(self, config: Initialized) -> Finalized:
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
