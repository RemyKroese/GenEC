"""Module containing the various workflow paths for executing the program."""

from abc import ABC, abstractmethod
from collections import defaultdict
from pathlib import Path
from typing import Callable, Optional, Type, TypeVar, TYPE_CHECKING

from rich.console import Console

from GenEC import utils
from GenEC.core import FileID, Workflows
from GenEC.core.analyze import Extractor, Comparer
from GenEC.core.configuration_manager import (
    ConfigurationManager, BasicConfigurationManager,
    PresetConfigurationManager, BatchConfigurationManager
)
from GenEC.core.configuration import BaseConfiguration
from GenEC.core.output_manager import OutputManager
from GenEC.core.types.output import DataExtract, DataCompare, Entry
from GenEC.core.prompts import Section, Key, create_prompt

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
        self.console = Console()
        self.configuration_manager: ConfigurationManager

    @abstractmethod
    def _get_configuration_manager(self) -> ConfigurationManager:  # pragma: no cover
        """
        Return the configuration manager for this workflow.

        Returns
        -------
        ConfigurationManager
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

            # Check if both source and reference data exist for this specific target file
            has_source = configuration.target_file in source_data
            has_reference = ref_data is not None and configuration.target_file in ref_data

            if has_source and has_reference:
                # ref_data guaranteed not None by has_reference check
                entry = self._create_comparison_entry(configuration, source_filtered, ref_data, extractor)  # type: ignore
                results[configuration.group].append(entry)
            elif has_source:
                entry = self._create_extraction_entry(configuration, source_filtered)
                results[configuration.group].append(entry)

        return results

    def _create_comparison_entry(self, configuration: BaseConfiguration, source_filtered: list[str],
                                 ref_data: dict[str, str], extractor: Extractor) -> Entry:
        """Create an entry with comparison data."""
        ref_text = ref_data[configuration.target_file]
        ref_filtered = extractor.extract_from_data(configuration, ref_text, FileID.REFERENCE)
        comparer = Comparer(source_filtered, ref_filtered)
        comparison_result: dict[str, DataCompare] = comparer.compare()
        return Entry(
            preset=configuration.preset,
            target=configuration.target_file,
            data=dict(sorted(comparison_result.items())))

    def _create_extraction_entry(self, configuration: BaseConfiguration, source_filtered: list[str]) -> Entry:
        """Create an entry with extraction-only data."""
        count_result = utils.get_list_each_element_count(source_filtered)
        extraction_result: dict[str, DataExtract] = {key: {'source': value} for key, value in count_result.items()}
        return Entry(
            preset=configuration.preset,
            target=configuration.target_file,
            data=dict(sorted(extraction_result.items())))

    def run(self) -> None:
        """Execute the workflow: read files, process configurations, and generate output."""
        assert self.configuration_manager is not None, 'configuration_manager must be initialized before run()'
        source_data, ref_data = self._get_data(self.configuration_manager.configurations)
        results = self._process_configurations(self.configuration_manager.configurations, source_data, ref_data)

        output_manager = self._create_output_manager()
        output_manager.process(results, root=self.source)

        utils.print_footer()

    def _create_output_manager(self) -> OutputManager:
        """Create the OutputManager for this workflow."""
        return OutputManager(output_directory=self.output_directory,
                             output_types=self.output_types,
                             should_print_results=True)


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
        self.configuration_manager: BasicConfigurationManager = self._get_configuration_manager()

    def _get_configuration_manager(self) -> BasicConfigurationManager:
        """
        Initialize a BasicConfigurationManager.

        Returns
        -------
        BasicConfigurationManager
            Configuration manager initialized for basic workflow.
        """
        manager = BasicConfigurationManager()
        manager.initialize_configuration()
        return manager

    def run(self) -> None:
        """Execute the base workflow and request if a preset should be generated from the CLI input."""
        super().run()
        print('\n')
        if self.configuration_manager.should_store_configuration():
            self.configuration_manager.create_new_preset()


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
        self.configuration_manager = self._get_configuration_manager()

    def _get_configuration_manager(self) -> PresetConfigurationManager:
        """
        Initialize a PresetConfigurationManager for the specified preset.

        Returns
        -------
        PresetConfigurationManager
            Configuration manager initialized with the preset.
        """
        manager = PresetConfigurationManager(
            presets_directory=self.presets_directory,
            preset=self.preset
        )
        manager.initialize_configuration()
        return manager


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
        self.print_results = args.print_results
        self.configuration_manager = self._get_configuration_manager()

    def _get_configuration_manager(self) -> BatchConfigurationManager:
        """
        Initialize a BatchConfigurationManager for the specified list of presets.

        Returns
        -------
        BatchConfigurationManager
            Configuration manager initialized with the preset list.
        """
        manager = BatchConfigurationManager(
            presets_directory=self.presets_directory,
            preset_list=self.preset_list,
            target_variables=self.target_variables
        )
        manager.initialize_configuration()
        return manager

    def _get_data(self, configurations: list[BaseConfiguration]) -> tuple[dict[str, str], Optional[dict[str, str]]]:
        """
        Read source and reference files one-by-one, skipping missing files.

        Parameters
        ----------
        configurations : list[BaseConfiguration]
            List of Configuration objects specifying target files to read.

        Returns
        -------
        tuple[dict[str, str], Optional[dict[str, str]]]
            Dictionary mapping file names to contents for source files and
            optionally for reference files if provided. Missing files are skipped.
        """
        source_data: dict[str, str] = {}
        ref_data: Optional[dict[str, str]] = {} if self.reference else None
        unique_source_files: set[str] = set(c.target_file for c in configurations)

        for target_file in unique_source_files:
            # Read source file
            source_file_path = Path(self.source) if target_file == '' else Path(self.source) / target_file
            try:
                source_data[target_file] = utils.read_file(source_file_path)
                source_exists = True
            except FileNotFoundError:
                self.console.print(create_prompt(Section.ERROR_HANDLING, Key.SKIPPING_SOURCE_FILE,
                                                 target_file=target_file))
                source_exists = False

            # Only read reference file if source file exists and reference directory is provided
            if source_exists and self.reference and ref_data is not None:
                ref_file_path = Path(self.reference) if target_file == '' else Path(self.reference) / target_file
                try:
                    ref_data[target_file] = utils.read_file(ref_file_path)
                except FileNotFoundError:
                    self.console.print(create_prompt(Section.ERROR_HANDLING, Key.SKIPPING_REFERENCE_FILE,
                                                     target_file=target_file))

        return source_data, ref_data

    def _create_output_manager(self) -> OutputManager:
        """Create OutputManager with performance-optimized CLI printing for preset-list workflow."""
        # Always print if no output files, otherwise check user preference
        should_print = not (self.output_directory and self.output_types) or self.print_results
        if not should_print:
            self.console.print(create_prompt(Section.ERROR_HANDLING, Key.CLI_PRINTING_DISABLED))
        return OutputManager(self.output_directory, self.output_types, should_print_results=should_print)
