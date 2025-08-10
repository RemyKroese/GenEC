from abc import ABC, abstractmethod
import re
from typing import Callable, Dict, Type, TypeVar

from GenEC.core import PositionalFilterType, ConfigOptions, TextFilterTypes
from GenEC.core.types.preset_config import Finalized


class BaseExtractor(ABC):
    def __init__(self, config: Finalized):
        self.config = config

    @abstractmethod
    def extract(self, clusters: list[str]) -> list[str]:  # pragma: no cover
        pass


E = TypeVar('E', bound=BaseExtractor)
_extractor_registry: Dict[str, Type[BaseExtractor]] = {}


def register_extractor(name: str) -> Callable[[Type[E]], Type[E]]:
    def decorator(cls: Type[E]) -> Type[E]:
        _extractor_registry[name] = cls
        return cls
    return decorator


def get_extractor(name: str, config: Finalized) -> BaseExtractor:
    try:
        return _extractor_registry[name](config)
    except KeyError:
        raise ValueError(f'Extractor type "{name}" is not registered.')


@register_extractor(TextFilterTypes.REGEX.value)
class RegexExtractor(BaseExtractor):
    def extract(self, clusters: list[str]) -> list[str]:
        regex_pattern = self.config.get(ConfigOptions.TEXT_FILTER.value)
        if not isinstance(regex_pattern, str):  # pragma: no cover
            # Regex pattern should always be a string due to input_manager logic, so there will be a bug if this error is raised
            raise TypeError('Incorrect text filter type for regex, expected a regex pattern.')
        pattern = re.compile(regex_pattern)

        filtered_text: list[str] = []
        for cluster in clusters:
            search_result = pattern.search(cluster)
            if search_result:
                groups = search_result.groups()
                text_output = ' | '.join(groups) if groups else search_result.group(0)
                filtered_text.append(text_output)
        return filtered_text


@register_extractor(TextFilterTypes.POSITIONAL.value)
class PositionalExtractor(BaseExtractor):
    def extract(self, clusters: list[str]) -> list[str]:
        position_filter = self.config.get(ConfigOptions.TEXT_FILTER.value)
        if not isinstance(position_filter, PositionalFilterType):  # pragma: no cover
            # Regex pattern should always be a string due to input_manager logic, so there will be a bug if this error is raised
            raise TypeError('Incorrect text filter type for positional, expected a separator string, line number, and occurrence number.')

        filtered_text: list[str] = []
        for cluster in clusters:
            try:
                line = cluster.split('\n')[position_filter.line-1]
                filtered_text.append(line.split(position_filter.separator)[position_filter.occurrence-1])
            except IndexError:  # Clusters that don't contain the search parameters are ignored altogether
                continue
        return filtered_text


@register_extractor(TextFilterTypes.COMBI_SEARCH.value)
class CombiSearchExtractor(BaseExtractor):
    def extract(self, clusters: list[str]) -> list[str]:
        text_filters = self.config.get(ConfigOptions.TEXT_FILTER.value)
        if not isinstance(text_filters, list):  # pragma: no cover
            # Regex pattern should always be a string due to input_manager logic, so there will be a bug if this error is raised
            raise TypeError('Incorrect text filter type for Combi-Search, expected a list of regex patterns.')

        for text_filter in text_filters[:-1]:
            pattern = re.compile(text_filter)
            clusters = [cluster for cluster in clusters if pattern.search(cluster)]

        # copy the config for safe modification
        new_config: Finalized = {
            **self.config,
            ConfigOptions.TEXT_FILTER_TYPE.value: TextFilterTypes.REGEX.value,
            ConfigOptions.TEXT_FILTER.value: text_filters[-1]}
        return RegexExtractor(new_config).extract(clusters)
