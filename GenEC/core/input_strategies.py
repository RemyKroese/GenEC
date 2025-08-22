"""Strategy pattern implementation for text filter input handling."""

from abc import ABC, abstractmethod
from typing import Union, TYPE_CHECKING, Callable, Any

from rich.console import Console

from GenEC.core import PositionalFilterType, TextFilterTypes
from GenEC.core.prompts import create_prompt, Section, Key
from GenEC.core.validation import validate_integer, validate_regex
from GenEC.core.types.preset_config import Initialized

console = Console()

if TYPE_CHECKING:  # pragma: no cover
    pass


class TextFilterInputStrategy(ABC):
    """
    Abstract base class for text filter input strategies.

    Each concrete strategy handles input collection for a specific text filter type.
    """

    def __init__(self, ask_question_func: Callable[[str], str]) -> None:
        """
        Initialize the strategy with a function for user interaction.

        Parameters
        ----------
        ask_question_func : Callable[[str], str]
            Function to ask questions to the user and get responses.
        """
        self.ask_question = ask_question_func

    @abstractmethod
    def collect_input(self, config: Initialized) -> Union[str, PositionalFilterType, list[str], dict[str, Any]]:
        """
        Collect text filter input from the user.

        Parameters
        ----------
        config : Initialized
            The configuration object containing preset values.

        Returns
        -------
        Union[str, PositionalFilterType, list[str]]
            The collected text filter data.
        """

    @abstractmethod
    def get_filter_type(self) -> TextFilterTypes:
        """
        Get the text filter type this strategy handles.

        Returns
        -------
        TextFilterTypes
            The filter type enum value.
        """


class RegexInputStrategy(TextFilterInputStrategy):
    """Strategy for collecting regex filter input."""

    def collect_input(self, config: Initialized) -> str:
        """
        Collect regex pattern from user input with validation.

        Parameters
        ----------
        config : Initialized
            The configuration object (unused for regex input).

        Returns
        -------
        str
            The regex pattern string.
        """
        while True:
            regex_input = self.ask_question(create_prompt(Section.SET_CONFIG, Key.REGEX_FILTER))
            if validate_regex(regex_input):
                return regex_input
            console.print(create_prompt(Section.ERROR_HANDLING, Key.INVALID_REGEX_INPUT))

    def get_filter_type(self) -> TextFilterTypes:
        """Get the regex filter type."""
        return TextFilterTypes.REGEX


class PositionalInputStrategy(TextFilterInputStrategy):
    """Strategy for collecting positional filter input."""

    def collect_input(self, config: Initialized) -> dict[str, Any]:
        """
        Collect positional filter parameters from user input.

        Parameters
        ----------
        config : Initialized
            The configuration object (unused for positional input).

        Returns
        -------
        dict[str, Any]
            The configured positional filter as a dict (for clean YAML serialization).
        """
        separator_input = self.ask_question(create_prompt(Section.SET_CONFIG, Key.POSITIONAL_SEPARATOR))

        # Get line number with validation - create custom validation loop
        while True:
            line_input = self.ask_question(create_prompt(Section.SET_CONFIG, Key.POSITIONAL_LINE))
            if validate_integer(line_input, min_val=1):
                line = int(line_input)
                break
            console.print(create_prompt(Section.ERROR_HANDLING, Key.INVALID_LINE_NUMBER))

        # Get occurrence number with validation - create custom validation loop
        while True:
            occurrence_input = self.ask_question(create_prompt(Section.SET_CONFIG, Key.POSITIONAL_OCCURRENCE))
            if validate_integer(occurrence_input, min_val=1):
                occurrence = int(occurrence_input)
                break
            console.print(create_prompt(Section.ERROR_HANDLING, Key.INVALID_OCCURRENCE_NUMBER))

        return {
            'separator': separator_input if separator_input else ' ',
            'line': line,
            'occurrence': occurrence
        }

    def get_filter_type(self) -> TextFilterTypes:
        """Get the positional filter type."""
        return TextFilterTypes.POSITIONAL


class RegexListInputStrategy(TextFilterInputStrategy):
    """Strategy for collecting regex list filter input."""

    YES_INPUT = ['yes', 'y']

    def collect_input(self, config: Initialized) -> list[str]:
        """
        Collect multiple regex patterns from user input.

        Parameters
        ----------
        config : Initialized
            The configuration object (unused for regex list input).

        Returns
        -------
        list[str]
            List of regex pattern strings.
        """
        regex_list_filters: list[str] = []
        index = 1

        while True:
            regex_list_filters.append(self.ask_question(create_prompt(Section.SET_CONFIG, Key.REGEX_LIST_FILTER, search=index)))
            index += 1

            if self.ask_question(create_prompt(Section.SET_CONFIG, Key.REGEX_LIST_CONTINUE)).lower() not in self.YES_INPUT:
                break

        return regex_list_filters

    def get_filter_type(self) -> TextFilterTypes:
        """Get the regex list filter type."""
        return TextFilterTypes.REGEX_LIST


# Registry for text filter input strategies
_input_strategy_registry: dict[str, type[TextFilterInputStrategy]] = {}


def register_input_strategy(filter_type: str) -> Callable[[type[TextFilterInputStrategy]], type[TextFilterInputStrategy]]:
    """
    Register text filter input strategies.

    Parameters
    ----------
    filter_type : str
        The text filter type identifier.

    Returns
    -------
    callable
        The decorator function.
    """
    def decorator(strategy_class: type[TextFilterInputStrategy]) -> type[TextFilterInputStrategy]:
        _input_strategy_registry[filter_type] = strategy_class
        return strategy_class
    return decorator


def get_input_strategy(filter_type: str, ask_question_func: Callable[[str], str]) -> TextFilterInputStrategy:
    """
    Get the appropriate input strategy for a filter type.

    Parameters
    ----------
    filter_type : str
        The text filter type identifier.
    ask_question_func : Callable[[str], str]
        Function to ask questions to the user and get responses.

    Returns
    -------
    TextFilterInputStrategy
        The strategy instance for the specified filter type.

    Raises
    ------
    ValueError
        If the filter type is not supported.
    """
    if filter_type not in _input_strategy_registry:
        raise ValueError(f'Unsupported filter type: {filter_type}')

    strategy_class = _input_strategy_registry[filter_type]
    return strategy_class(ask_question_func)


# Register the built-in strategies
register_input_strategy(TextFilterTypes.REGEX.value)(RegexInputStrategy)
register_input_strategy(TextFilterTypes.POSITIONAL.value)(PositionalInputStrategy)
register_input_strategy(TextFilterTypes.REGEX_LIST.value)(RegexListInputStrategy)
