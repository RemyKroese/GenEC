"""Module containing the various workflow paths for executing the program."""

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable, Optional, Type, TypeVar, TYPE_CHECKING

from GenEC import utils
from GenEC.core import FileID, Workflows
from GenEC.core.analyze import Extractor, Comparer
from GenEC.core.config_manager import ConfigManager
from GenEC.core.configuration import BaseConfiguration
from GenEC.core.output_manager import OutputManager
from GenEC.core.types.output import DataExtract, DataCompare, Entry

if TYPE_CHECKING:  # pragma: no cover
    import argparse


class Workflow(ABC):
    """
    Abstract base class for all workflow types.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments containing source, reference, output directory,
        and output type information.
    """

    def __init__(self, args: 'argparse.Namespace'):
        self.source = args.source
        self.reference = args.reference
        self.output_directory = args.output_directory
        self.output_types = args.output_types
        self.config_manager: ConfigManager

    @abstractmethod
    def _get_config_manager(self) -> ConfigManager:  # pragma: no cover
        """
        Return the configuration manager for this workflow.

        Returns
        -------
        ConfigManager
            Configuration manager instance that provides workflow configurations.
        """

    def _get_data(self, configurations: list[BaseConfiguration]) -> tuple[dict[str, str], Optional[dict[str, str]]]:
        """
        Read source and reference files based on the workflow configurations.

        Parameters
        ----------
        configurations : list[Configuration]
            List of Configuration objects specifying target files to read.

        Returns
        -------
        tuple[dict[str, str], Optional[dict[str, str]]]
            Dictionary mapping file names to contents for source files and
            optionally for reference files if provided.
        """
        source_data = utils.read_files(self.source, configurations)
        ref_data = utils.read_files(self.reference, configurations) if self.reference else None
        return source_data, ref_data

    def _process_configurations(self,
                                configurations: list[BaseConfiguration],
                                source_data: dict[str, str],
                                ref_data: Optional[dict[str, str]]
                                ) -> defaultdict[str, list[Entry]]:
        """
        Process all configurations by extracting and optionally comparing data.

        Parameters
        ----------
        configurations : list[Configuration]
            List of Configuration objects to process.
        source_data : dict[str, str]
            Dictionary mapping source file names to file contents.
        ref_data : Optional[dict[str, str]]
            Dictionary mapping reference file names to contents, or None if comparison is not required.

        Returns
        -------
        defaultdict[str, list[Entry]]
            Results organized by configuration group, where each entry contains
            extracted or compared data.
        """
        results: defaultdict[str, list[Entry]] = defaultdict(list)
        extractor = Extractor()

        for configuration in configurations:
            source_text = source_data.get(configuration.target_file, '')
            source_filtered = extractor.extract_from_data(configuration, source_text, FileID.SOURCE)

            if ref_data:  # extract and compare
                ref_text = ref_data.get(configuration.target_file, '')
                ref_filtered = extractor.extract_from_data(configuration, ref_text, FileID.REFERENCE)
                comparer = Comparer(source_filtered, ref_filtered)
                comparison_result: dict[str, DataCompare] = comparer.compare()
                results[configuration.group].append(Entry(
                    preset=configuration.preset,
                    target=configuration.target_file,
                    data=dict(sorted(comparison_result.items()))))
            else:  # extract only
                count_result = utils.get_list_each_element_count(source_filtered)
                extraction_result: dict[str, DataExtract] = {key: {'source': value} for key, value in count_result.items()}
                results[configuration.group].append(Entry(
                    preset=configuration.preset,
                    target=configuration.target_file,
                    data=dict(sorted(extraction_result.items()))))

        return results

    def run(self) -> None:
        """Execute the workflow: read files, process configurations, and generate output."""
        assert self.config_manager is not None, 'config_manager must be initialized before run()'
        source_data, ref_data = self._get_data(self.config_manager.configurations)
        results = self._process_configurations(self.config_manager.configurations, source_data, ref_data)

        output_manager = OutputManager(self.output_directory, self.output_types)
        output_manager.process(results, root=self.source, is_comparison=bool(ref_data))

        utils.print_footer()


E = TypeVar('E', bound=Workflow)
_workflow_registry: dict[str, Type[Workflow]] = {}


def register_workflow(name: str) -> Callable[[Type[E]], Type[E]]:
    """
     Register a workflow class under a given name decorator.

    Parameters
    ----------
    name : str
        Name used to register the workflow.

    Returns
    -------
    Callable[[Type[E]], Type[E]]
        Decorator that registers the class in the workflow registry.
    """
    def decorator(cls: Type[E]) -> Type[E]:
        _workflow_registry[name] = cls
        return cls
    return decorator


def get_workflow(name: str, args: 'argparse.Namespace') -> Workflow:
    """
    Retrieve a registered workflow instance by name.

    Parameters
    ----------
    name : str
        Name of the registered workflow.
    args : argparse.Namespace
        Parsed command-line arguments to pass to the workflow constructor.

    Returns
    -------
    Workflow
        An instance of the requested workflow.

    Raises
    ------
    ValueError
        If no workflow is registered under the given name.
    """
    try:
        return _workflow_registry[name](args)
    except KeyError as exc:  # pragma: no cover
        raise ValueError(f'Workflow [{name}] is not registered.') from exc


@register_workflow(Workflows.BASIC.value)
class Basic(Workflow):
    """
    Basic workflow that executes without preset configurations.

    This workflow reads source and optional reference files and extracts or compares
    data according to the default configuration setup.
    """

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self.config_manager = self._get_config_manager()

    def _get_config_manager(self) -> ConfigManager:
        """
        Initialize a ConfigManager.

        Returns
        -------
        ConfigManager
            Configuration manager initialized.
        """
        return ConfigManager()

    def run(self) -> None:
        """Execute the base workflow and request if a preset should be generated from the CLI input."""
        super().run()
        print('\n')
        if self.config_manager.should_store_configuration():
            self.config_manager.create_new_preset()


@register_workflow(Workflows.PRESET.value)
class Preset(Workflow):
    """
    Workflow that executes using a single preset configuration.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments including 'preset' and 'presets_directory'.
    """

    def __init__(self, args: 'argparse.Namespace') -> None:
        super().__init__(args)
        self.preset = args.preset
        self.presets_directory = args.presets_directory
        self.config_manager = self._get_config_manager()

    def _get_config_manager(self) -> ConfigManager:
        """
        Initialize a ConfigManager for the specified preset.

        Returns
        -------
        ConfigManager
            Configuration manager initialized with the preset.
        """
        preset_param: dict[str, str] = {'type': Workflows.PRESET.value, 'value': self.preset}
        return ConfigManager(preset_param, self.presets_directory)


@register_workflow(Workflows.PRESET_LIST.value)
class PresetList(Workflow):
    """
    Workflow that executes using a list of preset configurations.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments including 'preset_list', 'presets_directory',
        and 'target_variables'.
    """

    def __init__(self, args: 'argparse.Namespace') -> None:
        super().__init__(args)
        self.preset_list = args.preset_list
        self.presets_directory = args.presets_directory
        self.target_variables = args.target_variables
        self.config_manager = self._get_config_manager()

    def _get_config_manager(self) -> ConfigManager:
        """
        Initialize a ConfigManager for the specified list of presets.

        Returns
        -------
        ConfigManager
            Configuration manager initialized with the preset list.
        """
        preset_param: dict[str, str] = {'type': Workflows.PRESET_LIST.value, 'value': self.preset_list}
        return ConfigManager(preset_param, self.presets_directory, self.target_variables)
