"""Type hinting support for output data."""

from typing import Mapping, TypedDict, Union


class DataExtract(TypedDict):
    """
    Represents extracted data from a single source.

    This dictionary stores the integer value of a metric extracted from a source file
    or data cluster. It is typically used to store results before any comparisons.

    Parameters
    ----------
    TypedDict : type
        Base class for creating typed dictionaries in Python.
    """

    source: int


class DataCompare(DataExtract):
    """
    Represents data used for comparison between source and reference.

    In addition to the 'source' value inherited from DataExtract, this dictionary
    contains the 'reference' value and the 'difference' between source and reference.
    It is typically used when comparing two sets of data.

    Parameters
    ----------
    DataExtract : type
        Base class for the source data dictionary.
    """

    reference: int
    difference: int


class Entry(TypedDict):
    """
    Represents a single entry in a results dictionary.

    Each entry contains metadata about the extraction or comparison, including the
    preset used, the target identifier, and a mapping of data metrics keyed by
    strings. Values can be either DataExtract or DataCompare depending on context.

    Parameters
    ----------
    TypedDict : type
        Base class for creating typed dictionaries in Python.
    """

    preset: str
    target: str
    data: Mapping[str, Union[DataExtract, DataCompare]]
