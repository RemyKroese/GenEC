from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable, Dict, Optional, Type, TypeVar, TYPE_CHECKING

from GenEC import utils
from GenEC.core import FileID, Workflows
from GenEC.core.analyze import Extractor, Comparer
from GenEC.core.config_manager import ConfigManager, Configuration
from GenEC.core.manage_io import OutputManager
from GenEC.core.types.output import DataExtract, Entry

if TYPE_CHECKING:
    import argparse


class Workflow(ABC):
    def __init__(self, args: 'argparse.Namespace'):
        self.source = args.source
        self.reference = args.reference
        self.output_directory = args.output_directory
        self.output_types = args.output_types

    @abstractmethod
    def _get_config_manager(self) -> ConfigManager:
        pass

    def _get_data(self, configurations: list[Configuration]) -> tuple[dict[str, str], Optional[dict[str, str]]]:
        source_data = utils.read_files(self.source, configurations)
        ref_data = utils.read_files(self.reference, configurations) if self.reference else None
        return source_data, ref_data

    def run(self) -> None:
        config_manager = self._get_config_manager()

        source_data, ref_data = self._get_data(config_manager.configurations)
        results: defaultdict[str, list[Entry]] = defaultdict(list)
        extractor = Extractor()

        for configuration in config_manager.configurations:
            source_text = source_data.get(configuration.target_file, '')
            source_filtered = extractor.extract_from_data(configuration.config, source_text, FileID.SOURCE)

            if ref_data:  # extract and compare
                ref_text = ref_data.get(configuration.target_file, '')
                ref_filtered = extractor.extract_from_data(configuration.config, ref_text, FileID.REFERENCE)
                comparer = Comparer(source_filtered, ref_filtered)
                result = comparer.compare()
                results[configuration.group].append(Entry(
                    preset=configuration.preset,
                    target=configuration.target_file,
                    data=result))
            else:  # extract only
                result = utils.get_list_each_element_count(source_filtered)
                output_result: dict[str, DataExtract] = {key: {'source': value} for key, value in result.items()}
                results[configuration.group].append(Entry(
                    preset=configuration.preset,
                    target=configuration.target_file,
                    data=output_result))

        output_manager = OutputManager(self.output_directory, self.output_types)
        output_manager.process(results, root=self.source, is_comparison=bool(ref_data))


E = TypeVar('E', bound=Workflow)
_workflow_registry: Dict[str, Type[Workflow]] = {}


def register_workflow(name: str) -> Callable[[Type[E]], Type[E]]:
    def decorator(cls: Type[E]) -> Type[E]:
        _workflow_registry[name] = cls
        return cls
    return decorator


def get_workflow(name: str, args: 'argparse.Namespace') -> Workflow:
    try:
        return _workflow_registry[name](args)
    except KeyError:
        raise ValueError(f'Workflow [{name}] is not registered.')


@register_workflow(Workflows.BASIC.value)
class Basic(Workflow):
    def _get_config_manager(self) -> ConfigManager:
        return ConfigManager()


@register_workflow(Workflows.PRESET.value)
class Preset(Workflow):
    def __init__(self, args: 'argparse.Namespace') -> None:
        super().__init__(args)
        self.preset = args.preset
        self.presets_directory = args.presets_directory

    def _get_config_manager(self) -> ConfigManager:
        preset_param: dict[str, str] = {'type': 'preset', 'value': self.preset}
        return ConfigManager(preset_param, self.presets_directory)


@register_workflow(Workflows.PRESET_LIST.value)
class PresetList(Workflow):
    def __init__(self, args: 'argparse.Namespace') -> None:
        super().__init__(args)
        self.preset_list = args.preset_list
        self.presets_directory = args.presets_directory

    def _get_config_manager(self) -> ConfigManager:
        preset_param: dict[str, str] = {'type': 'preset-list', 'value': self.preset_list}
        return ConfigManager(preset_param, self.presets_directory)
