from typing import Mapping, TypedDict, Union


class DataExtract(TypedDict):
    source: int


class DataCompare(DataExtract):
    reference: int
    difference: int


class Entry(TypedDict):
    preset: str
    target: str
    data: Mapping[str, Union[DataExtract, DataCompare]]
