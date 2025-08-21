"""Module for managing the output of the program."""

from pathlib import Path
from typing import cast, Optional, TYPE_CHECKING

from rich.console import Console

from GenEC import utils
from GenEC.core.types.output import DataCompare, DataExtract, Entry

if TYPE_CHECKING:  # pragma: no cover
    from rich.panel import Panel

console = Console()


class OutputManager:
    """
    Handles formatting, printing, and writing of extracted or compared results.

    This class can optionally write results to files in multiple formats and print
    ASCII tables of the results to the console.
    """

    def __init__(self,
                 output_directory: Optional[str] = None,
                 output_types: Optional[list[str]] = None,
                 should_print_results: bool = True) -> None:
        self.output_directory = Path(output_directory) if output_directory else None
        self.output_types = output_types
        self.should_print_results = should_print_results

    def process(self,
                results: dict[str, list[Entry]],
                root: str,
                file_name: str = 'result',
                is_comparison: bool = False
                ) -> None:
        """
        Process and output extracted or compared results.

        Parameters
        ----------
        results : dict[str, list[Entry]]
            The results grouped by preset or category.
        root : str
            The root directory or identifier of the source data.
        file_name : str, optional
            The base name of output files, by default 'result'.
        is_comparison : bool, optional
            Whether the results are comparison results, by default False.
        """
        for group, entries in results.items():
            ascii_tables: list['Panel'] = []
            for entry in entries:
                if is_comparison:
                    ascii_tables.append(utils.create_comparison_table(cast(dict[str, DataCompare],
                                                                           entry['data']), entry.get('preset'), entry.get('target')))
                else:
                    ascii_tables.append(utils.create_extraction_table(cast(dict[str, DataExtract],
                                                                           entry['data']), entry.get('preset'), entry.get('target')))
            if self.should_print_results:
                for table in ascii_tables:
                    console.print('\n')
                    console.print(table)
            if self.output_directory and self.output_types:
                output_path = self._create_output_path(group, root, file_name=file_name)
                utils.write_output(entries, ascii_tables, output_path, self.output_types)

    def _create_output_path(self, group: str, root: str, file_name: str = 'result') -> Path:
        """
        Construct the output file path for a specific group.

        Parameters
        ----------
        group : str
            The group name or category.
        root : str
            The root directory or file identifier of the source data.
        file_name : str, optional
            The base name of the output file, by default 'result'.

        Returns
        -------
        Path
            The complete path to the output file.
        """
        root_path = Path(root).name
        root_path_without_extension = Path(root_path).stem
        group_dir = cast(Path, self.output_directory) / root_path_without_extension / group
        return group_dir / file_name
