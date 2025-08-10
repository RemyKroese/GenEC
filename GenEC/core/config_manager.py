from collections import defaultdict
from dataclasses import dataclass
import os
from typing import Optional

from GenEC import utils
from GenEC.core import PresetConfigFinalized, PresetConfigInitialized, ConfigOptions, PositionalFilterType
from GenEC.core.manage_io import InputManager

YES_INPUT = ['yes', 'y']
NO_INPUT = ['no', 'n']


@dataclass
class Configuration:
    config: PresetConfigFinalized
    preset: str
    target_file: str


class ConfigManager:
    def __init__(self, preset_param: Optional[dict[str, str]] = None, presets_directory: Optional[str] = None) -> None:
        self.presets_directory = presets_directory if presets_directory else os.path.join(os.path.dirname(__file__), '../presets')
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
        presets_list_file_path = os.path.join(self.presets_directory, presets_list_target + '.yaml')
        presets_list = utils.read_yaml_file(presets_list_file_path)
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
                    'preset_group': group,
                    'preset_file': file_name,
                    'preset_name': preset_name,
                    'target_file': target_file
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

    def _process_preset_entry(self, entry: dict[str, str], target_file: str) -> Configuration | None:
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
            target_file=target_file)

    def load_preset(self, preset_target: str) -> PresetConfigInitialized:
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

    def load_preset_file(self, preset_file: str) -> dict[str, PresetConfigInitialized]:
        presets_file_path = os.path.join(self.presets_directory, preset_file + '.yaml')
        presets = utils.read_yaml_file(presets_file_path)

        if not presets or len(presets) == 0:
            raise ValueError(f'presets file {presets_file_path} does not contain any presets')

        return presets

    @staticmethod
    def _normalize_cluster_filter(cluster_filter: Optional[str]) -> str:
        if cluster_filter is None:
            return ''
        return cluster_filter.encode('utf-8').decode('unicode_escape')

    def _set_simple_options(self, config: PresetConfigInitialized):
        config[ConfigOptions.CLUSTER_FILTER.value] = InputManager.set_cluster_filter(config)
        config[ConfigOptions.TEXT_FILTER_TYPE.value] = InputManager.set_text_filter_type(config)
        config[ConfigOptions.TEXT_FILTER.value] = InputManager.set_text_filter(config)
        config[ConfigOptions.SHOULD_SLICE_CLUSTERS.value] = InputManager.set_should_slice_clusters(config)

    def _set_cluster_text_options(self, config: PresetConfigInitialized):
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
            config: PresetConfigInitialized = self.load_preset(preset)
        else:
            config: PresetConfigInitialized = PresetConfigInitialized(**{option.value: None for option in ConfigOptions})
            self._set_simple_options(config)

        if config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value):
            self._set_cluster_text_options(config)

        config[ConfigOptions.CLUSTER_FILTER.value] = self._normalize_cluster_filter(config[ConfigOptions.CLUSTER_FILTER.value])

        self.configurations.append(Configuration(self._finalize_config(config), preset, target_file))

    def _finalize_config(self, config: PresetConfigInitialized) -> PresetConfigFinalized:
        cluster_filter = config.get(ConfigOptions.CLUSTER_FILTER.value)
        text_filter_type = config.get(ConfigOptions.TEXT_FILTER_TYPE.value)
        text_filter = config.get(ConfigOptions.TEXT_FILTER.value)
        should_slice_clusters = config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value)

        assert isinstance(cluster_filter, str)
        assert isinstance(text_filter_type, str)
        assert isinstance(text_filter, str) or isinstance(text_filter, list) or isinstance(text_filter, PositionalFilterType)
        assert isinstance(should_slice_clusters, bool)

        return PresetConfigFinalized(
            cluster_filter=cluster_filter,
            text_filter_type=text_filter_type,
            text_filter=text_filter,
            should_slice_clusters=should_slice_clusters,
            src_start_cluster_text=config.get(ConfigOptions.SRC_START_CLUSTER_TEXT.value),
            src_end_cluster_text=config.get(ConfigOptions.SRC_END_CLUSTER_TEXT.value),
            ref_start_cluster_text=config.get(ConfigOptions.REF_START_CLUSTER_TEXT.value),
            ref_end_cluster_text=config.get(ConfigOptions.REF_END_CLUSTER_TEXT.value)
        )
