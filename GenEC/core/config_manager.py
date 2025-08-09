from collections import defaultdict
from dataclasses import dataclass
import os
from typing import Optional

from GenEC import utils
from GenEC.core import PresetConfigFinalized, PresetConfigInitialized, ConfigOptions
from GenEC.core.manage_io import InputManager

YES_INPUT = ['yes', 'y']
NO_INPUT = ['no', 'n']


@dataclass
class AnalysisConstruct:
    preset: str
    config: PresetConfigFinalized
    target_file: str


class ConfigManager:
    def __init__(self, preset_param: Optional[dict[str, str]] = None, presets_directory: Optional[str] = None) -> None:
        self.presets_directory = presets_directory if presets_directory else os.path.join(os.path.dirname(__file__), '../presets')
        self.preset_file = ''
        self.preset_name = ''
        self.analysis_constructs: list[AnalysisConstruct] = []
        self.config = PresetConfigInitialized(
            cluster_filter=None,
            text_filter_type=None,
            text_filter=None,
            should_slice_clusters=None,
            src_start_cluster_text=None,
            src_end_cluster_text=None,
            ref_start_cluster_text=None,
            ref_end_cluster_text=None
        )

        if preset_param:
            if preset_param['type'] == 'preset':
                self.preset_file, self.preset_name = self.parse_preset_param(preset_param['value'])
                self.config = self.load_preset()
            elif preset_param['type'] == 'preset-list':
                self.analysis_constructs.extend(self.load_presets(preset_param['value']))
            else:
                raise ValueError(f'{preset_param['type']} is not a valid preset parameter type.')

    @staticmethod
    def parse_preset_param(preset_param: str) -> tuple[str, Optional[str]]:
        if '/' not in preset_param:
            return preset_param, None
        else:
            return tuple(preset_param.split('/', 1))  # type: ignore[return-value]  # Always returns 2 items

    def load_presets(self, presets_list_file_name: str) -> list[AnalysisConstruct]:  # pragma: no cover
        presets_list_file_path = os.path.join(self.presets_directory, presets_list_file_name + '.yaml')
        presets_list = utils.read_yaml_file(presets_list_file_path)
        presets_per_file = self._group_presets_by_file(presets_list)
        return self._collect_presets(presets_per_file)

    def _group_presets_by_file(self, presets_list: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
        presets_per_target: dict[str, list[dict[str, str]]] = defaultdict(list)
        for entry in presets_list:
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
                'target_file': target_file
            })
        return presets_per_target

    def _collect_presets(self, presets_per_target: dict[str, list[dict[str, str]]]) -> list[AnalysisConstruct]:
        analysis_constructs: list[AnalysisConstruct] = []
        for target_file, preset_entries in presets_per_target.items():
            for entry in preset_entries:
                result = self._process_preset_entry(entry, target_file)
                if result:
                    analysis_constructs.append(result)

        if not analysis_constructs:
            raise ValueError('None of the provided presets were found.')
        return analysis_constructs

    def _process_preset_entry(self, entry: dict[str, str], target_file: str) -> AnalysisConstruct | None:
        file_name = entry['preset_file']
        preset_name = entry['preset_name']
        loaded_presets = self.load_preset_file(file_name)
        if preset_name not in loaded_presets:
            print(f'preset {preset_name} not found in {file_name}. Skipping...')
            return None
        config = loaded_presets[preset_name]
        config[ConfigOptions.CLUSTER_FILTER.value] = self._normalize_cluster_filter(config.get(ConfigOptions.CLUSTER_FILTER.value))
        finalized_config = self._finalize_config(config)
        return AnalysisConstruct(
            preset=f'{file_name}/{preset_name}',
            config=finalized_config,
            target_file=target_file)

    def load_preset(self) -> PresetConfigFinalized:
        presets = self.load_preset_file(self.preset_file)
        if not self.preset_name:
            if len(presets) == 1:
                self.preset_name = next(iter(presets))
            else:
                self.preset_name = InputManager.ask_mpc_question('Please choose a preset:\n', list(presets.keys()))

        if self.preset_name not in presets:
            raise ValueError(f'preset {self.preset_name} not found in {self.preset_file}')

        return presets[self.preset_name]

    def load_preset_file(self, preset_file: str) -> dict[str, PresetConfigFinalized]:
        presets_file_path = os.path.join(self.presets_directory, preset_file + '.yaml')
        presets = utils.read_yaml_file(presets_file_path)

        if not presets or len(presets) == 0:
            raise ValueError(f'presets file {presets_file_path} does not contain any presets')

        return presets

    @staticmethod
    def _normalize_cluster_filter(cluster_filter: Optional[str]) -> str:
        if not cluster_filter:
            return '\n'
        return cluster_filter.encode('utf-8').decode('unicode_escape')

    def _set_simple_options(self):
        simple_options = [
            (ConfigOptions.CLUSTER_FILTER.value, InputManager.set_cluster_filter),
            (ConfigOptions.TEXT_FILTER_TYPE.value, InputManager.set_text_filter_type),
            (ConfigOptions.TEXT_FILTER.value, InputManager.set_text_filter),
            (ConfigOptions.SHOULD_SLICE_CLUSTERS.value, InputManager.set_should_slice_clusters),
        ]
        for option_key, setter_func in simple_options:
            if not self.config.get(option_key):
                self.config[option_key] = setter_func(self.config)

    def _set_cluster_text_options(self):
        cluster_text_options = [
                (ConfigOptions.SRC_START_CLUSTER_TEXT.value, 'start', 'SRC'),
                (ConfigOptions.SRC_END_CLUSTER_TEXT.value, 'end', 'SRC'),
                (ConfigOptions.REF_START_CLUSTER_TEXT.value, 'start', 'REF'),
                (ConfigOptions.REF_END_CLUSTER_TEXT.value, 'end', 'REF'),
            ]
        for option_key, position, src_or_ref in cluster_text_options:
            if not self.config.get(option_key):
                self.config[option_key] = InputManager.set_cluster_text(self.config, option_key, position, src_or_ref)

    def set_config(self, preset: str, target_file: str = '') -> None:
        self._set_simple_options()
        if self.config.get(ConfigOptions.SHOULD_SLICE_CLUSTERS.value):
            self._set_cluster_text_options()

        self.config[ConfigOptions.CLUSTER_FILTER.value] = self._normalize_cluster_filter(self.config[ConfigOptions.CLUSTER_FILTER.value])
        self.analysis_constructs.append(AnalysisConstruct(preset, self._finalize_config(self.config), target_file))

    def _finalize_config(self, config: PresetConfigInitialized) -> PresetConfigFinalized:  # pragma: no cover
        text_filter = config.get('text_filter')
        if text_filter is None:
            text_filter = ''
        return PresetConfigFinalized(
            cluster_filter=config.get('cluster_filter') or '',
            text_filter_type=config.get('text_filter_type') or '',
            text_filter=text_filter,
            should_slice_clusters=bool(config.get('should_slice_clusters')),
            src_start_cluster_text=config.get('src_start_cluster_text'),
            src_end_cluster_text=config.get('src_end_cluster_text'),
            ref_start_cluster_text=config.get('ref_start_cluster_text'),
            ref_end_cluster_text=config.get('ref_end_cluster_text')
        )
