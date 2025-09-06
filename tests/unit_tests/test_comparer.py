"""Unit tests for GenEC Comparer class."""
from __future__ import annotations

import pytest
from GenEC.core.analyze import Comparer

SRC_1: list[str] = ['1', '2', '3']
SRC_2: list[str] = ['1', '2']
SRC_3: list[str] = ['1', '1', '1', '2']

REF_1: list[str] = ['1', '2', '3']
REF_2: list[str] = ['3']
REF_3: list[str] = ['3', '2', '100', '52']

EXPECTED_SRC_1: dict[str, int] = {'1': 1, '2': 1, '3': 1}
EXPECTED_SRC_2: dict[str, int] = {'1': 1, '2': 1}
EXPECTED_SRC_3: dict[str, int] = {'1': 3, '2': 1}

EXPECTED_REF_1: dict[str, int] = {'1': 1, '2': 1, '3': 1}
EXPECTED_REF_2: dict[str, int] = {'3': 1}
EXPECTED_REF_3: dict[str, int] = {'3': 1, '2': 1, '100': 1, '52': 1}

SRC_STRUCT_1: dict[str, int] = {'1': 1, '2': 1, '3': 1}
REF_STRUCT_1: dict[str, int] = {'1': 1, '2': 1, '3': 1}

SRC_STRUCT_2: dict[str, int] = {'1': 1, '2': 1, '3': 0}
REF_STRUCT_2: dict[str, int] = {'1': 0, '2': 0, '3': 1}

SRC_STRUCT_3: dict[str, int] = {'1': 3, '2': 1, '3': 0, '52': 0, '100': 0}
REF_STRUCT_3: dict[str, int] = {'1': 0, '2': 1, '3': 1, '52': 1, '100': 1}

DIFFERENCES_1: dict[str, dict[str, int]] = {
    '1': {'source': 1, 'reference': 1, 'difference': 0},
    '2': {'source': 1, 'reference': 1, 'difference': 0},
    '3': {'source': 1, 'reference': 1, 'difference': 0}
}

DIFFERENCES_2: dict[str, dict[str, int]] = {
    '1': {'source': 1, 'reference': 0, 'difference': 1},
    '2': {'source': 1, 'reference': 0, 'difference': 1},
    '3': {'source': 0, 'reference': 1, 'difference': -1}
}

DIFFERENCES_3: dict[str, dict[str, int]] = {
    '1': {'source': 3, 'reference': 0, 'difference': 3},
    '2': {'source': 1, 'reference': 1, 'difference': 0},
    '3': {'source': 0, 'reference': 1, 'difference': -1},
    '52': {'source': 0, 'reference': 1, 'difference': -1},
    '100': {'source': 0, 'reference': 1, 'difference': -1}
}

# Expected results for only_show_differences=True tests
DIFFERENCES_2_FILTERED: dict[str, dict[str, int]] = {
    '1': {'source': 1, 'reference': 0, 'difference': 1},
    '2': {'source': 1, 'reference': 0, 'difference': 1},
    '3': {'source': 0, 'reference': 1, 'difference': -1}
}

DIFFERENCES_3_FILTERED: dict[str, dict[str, int]] = {
    '1': {'source': 3, 'reference': 0, 'difference': 3},
    '3': {'source': 0, 'reference': 1, 'difference': -1},
    '52': {'source': 0, 'reference': 1, 'difference': -1},
    '100': {'source': 0, 'reference': 1, 'difference': -1}
}


@pytest.mark.unit
@pytest.mark.parametrize('source, reference, expected_unique_elements', [
    (SRC_1, REF_1, {'1', '2', '3'}),
    (SRC_1, REF_1, {'3', '2', '1'}),  # set order should not matter
    (SRC_2, REF_2, {'1', '2', '3'}),
    (SRC_2, REF_3, {'1', '2', '3', '52', '100'}),
])
def test_init_comparer(source: list[str], reference: list[str], expected_unique_elements: set[str]) -> None:
    c: Comparer = Comparer(source, reference)
    assert c.unique_elements == expected_unique_elements


@pytest.mark.unit
@pytest.mark.parametrize('source, reference, expected_source_counter, expected_reference_counter', [
    (SRC_1, REF_1, EXPECTED_SRC_1, EXPECTED_REF_1),
    (SRC_2, REF_2, EXPECTED_SRC_2, EXPECTED_REF_2),
    (SRC_3, REF_3, EXPECTED_SRC_3, EXPECTED_REF_3),
])
def test_counters(source: list[str], reference: list[str],
                 expected_source_counter: dict[str, int],
                 expected_reference_counter: dict[str, int]) -> None:
    c: Comparer = Comparer(source, reference)
    assert c.source_counts == expected_source_counter
    assert c.reference_counts == expected_reference_counter


@pytest.mark.unit
@pytest.mark.parametrize('source, reference, expected_diff', [
    (SRC_1, REF_1, DIFFERENCES_1),
    (SRC_2, REF_2, DIFFERENCES_2),
    (SRC_3, REF_3, DIFFERENCES_3)])
def test_compare(source: list[str], reference: list[str], expected_diff: dict[str, dict[str, int]]) -> None:
    c: Comparer = Comparer(source, reference)
    assert c.compare() == expected_diff


@pytest.mark.unit
@pytest.mark.parametrize('source, reference, expected_diff', [
    (SRC_1, REF_1, {}),
    (SRC_2, REF_2, DIFFERENCES_2_FILTERED),
    (SRC_3, REF_3, DIFFERENCES_3_FILTERED),
])
def test_compare_with_only_show_differences(source: list[str], reference: list[str],
                                          expected_diff: dict[str, dict[str, int]]) -> None:
    c: Comparer = Comparer(source, reference, only_show_differences=True)
    assert c.compare() == expected_diff
