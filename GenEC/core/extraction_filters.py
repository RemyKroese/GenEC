"""Module defining text extraction strategies for GenEC."""

from abc import abstractmethod
import re
from typing import Callable, Type, TypeVar, Generic, TYPE_CHECKING

from rich.console import Console

from GenEC.core import PositionalFilterType, TextFilterTypes
from GenEC.core.prompts import create_prompt, Section, Key

# Import at module level to avoid import-outside-toplevel issue
import GenEC.core.configuration as config_module

if TYPE_CHECKING:
    from GenEC.core.configuration import BaseConfiguration

T = TypeVar('T')

console = Console()


class BaseExtractor(Generic[T]):
    """
    Abstract base class for all text extractors.

    Type-safe extractor that works with specific configuration types.
    """

    def __init__(self, config: 'BaseConfiguration[T]'):
        self.config = config

    def get_text_filter(self) -> T:
        """Get text filter from config with proper typing."""
        return self.config.text_filter

    @abstractmethod
    def extract(self, clusters: list[str]) -> list[str]:  # pragma: no cover
        """
        Extract text from a list of text clusters.

        Parameters
        ----------
        clusters : list[str]
            List of text blocks to extract from.

        Returns
        -------
        list[str]
            List of extracted text snippets.
        """


E = TypeVar('E', bound=BaseExtractor)
_extractor_registry: dict[str, Type[BaseExtractor]] = {}


def register_extractor(name: str) -> Callable[[Type[E]], Type[E]]:
    """
    Register an extractor class under a given name decorator.

    Parameters
    ----------
    name : str
        Name used to register the extractor.

    Returns
    -------
    Callable[[Type[E]], Type[E]]
        Decorator that registers the class in the extractor registry.
    """

    def decorator(cls: Type[E]) -> Type[E]:
        """
        Register the extractor class.

        Parameters
        ----------
        cls : Type[E]
            Extractor class to register.

        Returns
        -------
        Type[E]
            The registered extractor class.
        """
        _extractor_registry[name] = cls
        return cls

    return decorator


def get_extractor(name: str, config: 'BaseConfiguration') -> BaseExtractor:
    """
    Retrieve a registered extractor instance by name.

    Parameters
    ----------
    name : str
        Name of the registered extractor.
    config : Finalized
        Configuration object to pass to the extractor.

    Returns
    -------
    BaseExtractor
        An instance of the requested extractor.

    Raises
    ------
    ValueError
        If no extractor is registered under the given name.
    """
    try:
        return _extractor_registry[name](config)
    except KeyError as exc:
        raise ValueError(f'Extractor type "{name}" is not registered.') from exc


@register_extractor(TextFilterTypes.REGEX.value)
class RegexExtractor(BaseExtractor[str]):
    """
    Extracts text using a single regular expression pattern.

    Type-safe extractor that expects str text_filter.
    """

    def extract(self, clusters: list[str]) -> list[str]:
        """
        Extract text from clusters using a single regex pattern.

        Parameters
        ----------
        clusters : list[str]
            List of text blocks to search with the regex pattern.

        Returns
        -------
        list[str]
            List of matched text strings. If the regex defines groups,
            the extracted string will be the joined groups separated by ' | '.

        Raises
        ------
        TypeError
            If the configured text filter is not a string.
        """
        regex_pattern = self.get_text_filter()
        if not isinstance(regex_pattern, str):  # pragma: no cover
            raise TypeError('Incorrect text filter type for regex, expected a regex pattern.')

        try:
            pattern = re.compile(regex_pattern)
        except re.error as e:
            console.print(create_prompt(Section.ERROR_HANDLING, Key.REGEX_COMPILATION_ERROR, error=str(e)))
            raise ValueError(f"Invalid regex pattern: {regex_pattern}") from e

        filtered_text: list[str] = []
        for cluster in clusters:
            search_result = pattern.search(cluster)
            if search_result:
                groups = search_result.groups()
                if groups:
                    # Filter out None values from groups and join
                    valid_groups = [group for group in groups if group is not None]
                    text_output = ' | '.join(valid_groups) if valid_groups else search_result.group(0)
                else:
                    text_output = search_result.group(0)
                filtered_text.append(text_output)
        return filtered_text


@register_extractor(TextFilterTypes.POSITIONAL.value)
class PositionalExtractor(BaseExtractor[PositionalFilterType]):
    """
    Extracts text based on line number, separator, and occurrence.

    Type-safe extractor that expects PositionalFilterType text_filter.
    """

    def extract(self, clusters: list[str]) -> list[str]:
        """
        Extract specific lines or fields from clusters based on position.

        Parameters
        ----------
        clusters : list[str]
            List of text blocks to extract from.

        Returns
        -------
        list[str]
            Extracted lines or fields from clusters that match the positional filter.

        Raises
        ------
        TypeError
            If the configured text filter is not a PositionalFilterType object.
        """
        position_filter = self.get_text_filter()
        if not isinstance(position_filter, PositionalFilterType):  # pragma: no cover
            raise TypeError(
                'Incorrect text filter type for positional, expected a PositionalFilterType object.'
            )

        filtered_text: list[str] = []
        for cluster in clusters:
            try:
                line = cluster.split('\n')[position_filter.line - 1]
                filtered_text.append(line.split(position_filter.separator)[position_filter.occurrence - 1])
            except IndexError:  # Ignore clusters that don't match the filter
                continue
        return filtered_text


@register_extractor(TextFilterTypes.REGEX_LIST.value)
class RegexListExtractor(BaseExtractor[list[str]]):
    """
    Extracts text using a sequence of regular expressions applied in order.

    Type-safe extractor that expects list[str] text_filter.
    """

    def extract(self, clusters: list[str]) -> list[str]:
        """
        Sequentially filter and extract text using multiple regex patterns.

        Parameters
        ----------
        clusters : list[str]
            List of text blocks to extract from.

        Returns
        -------
        list[str]
            Text extracted using the last regex pattern after filtering
            clusters with preceding patterns.

        Raises
        ------
        TypeError
            If the text filter is not a list of regex patterns.
        """
        text_filters = self.get_text_filter()
        if not isinstance(text_filters, list):  # pragma: no cover
            raise TypeError('Incorrect text filter type for regex-list, expected a list of regex patterns.')

        for text_filter in text_filters[:-1]:
            pattern = re.compile(text_filter)
            clusters = [cluster for cluster in clusters if pattern.search(cluster)]

        # Create a temporary RegexConfiguration for final extraction
        dataclass_config = config_module.RegexConfiguration(
            cluster_filter=self.config.cluster_filter,
            should_slice_clusters=self.config.should_slice_clusters,
            text_filter=text_filters[-1],
            src_start_cluster_text=self.config.src_start_cluster_text,
            src_end_cluster_text=self.config.src_end_cluster_text,
            ref_start_cluster_text=self.config.ref_start_cluster_text,
            ref_end_cluster_text=self.config.ref_end_cluster_text,
        )
        return RegexExtractor(dataclass_config).extract(clusters)
