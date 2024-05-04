import pytest

from src.genec import Comparer

SRC_1 = ['1', '2', '3']
SRC_2 = ['1', '2']
SRC_3 = ['1', '1', '1', '2']

REF_1 = ['1', '2', '3']
REF_2 = ['3']
REF_3 = ['3', '2', '100', '52']

SRC_STRUCT_1 = {'1': 1, '2': 1, '3': 1}
REF_STRUCT_1 = {'1': 1, '2': 1, '3': 1}

SRC_STRUCT_2 = {'1': 1, '2': 1, '3': 0}
REF_STRUCT_2 = {'1': 0, '2': 0, '3': 1}

SRC_STRUCT_3 = {'1': 3, '2': 1, '3': 0, '52': 0, '100': 0}
REF_STRUCT_3 = {'1': 0, '2': 1, '3': 1, '52': 1, '100': 1}

DIFFERENCES_1 = {
    '1': {'source': 1, 'reference': 1, 'difference': 0},
    '2': {'source': 1, 'reference': 1, 'difference': 0},
    '3': {'source': 1, 'reference': 1, 'difference': 0}
}

DIFFERENCES_2 = {
    '1': {'source': 1, 'reference': 0, 'difference': 1},
    '2': {'source': 1, 'reference': 0, 'difference': 1},
    '3': {'source': 0, 'reference': 1, 'difference': 1}
}

DIFFERENCES_3 = {
    '1': {'source': 3, 'reference': 0, 'difference': 3},
    '2': {'source': 1, 'reference': 1, 'difference': 0},
    '3': {'source': 0, 'reference': 1, 'difference': 1},
    '52': {'source': 0, 'reference': 1, 'difference': 1},
    '100': {'source': 0, 'reference': 1, 'difference': 1}
}


@pytest.mark.parametrize('source, reference, expected_unique_elements', [
    (SRC_1, REF_1, {'1', '2', '3'}),
    (SRC_1, REF_1, {'3', '2', '1'}),  # set order should not matter
    (SRC_2, REF_2, {'1', '2', '3'}),
    (SRC_2, REF_3, {'1', '2', '3', '52', '100'}),
    ])
def test_init_comparer(source, reference, expected_unique_elements):
    c = Comparer(source, reference)
    assert c.unique_elements == expected_unique_elements


@pytest.mark.parametrize('source, reference, expected_src_struct, expected_ref_struct', [
    (SRC_1, REF_1, SRC_STRUCT_1, REF_STRUCT_1),
    (SRC_2, REF_2, SRC_STRUCT_2, REF_STRUCT_2),
    (SRC_3, REF_3, SRC_STRUCT_3, REF_STRUCT_3)])
def test_create_data_structures(source, reference, expected_src_struct, expected_ref_struct):
    c = Comparer(source, reference)
    src, ref = c.create_data_structures()
    assert src == expected_src_struct
    assert ref == expected_ref_struct


@pytest.mark.parametrize('src, ref, src_struct, ref_struct, expected_diff', [
    (SRC_1, REF_1, SRC_STRUCT_1, REF_STRUCT_1, DIFFERENCES_1),
    (SRC_2, REF_2, SRC_STRUCT_2, REF_STRUCT_2, DIFFERENCES_2),
    (SRC_3, REF_3, SRC_STRUCT_3, REF_STRUCT_3, DIFFERENCES_3)])
def test_get_differences(src, ref, src_struct, ref_struct, expected_diff):
    c = Comparer(src, ref)
    assert c.get_differences(src_struct, ref_struct) == expected_diff


@pytest.mark.parametrize('src, ref, expected_diff', [
    (SRC_1, REF_1, DIFFERENCES_1),
    (SRC_2, REF_2, DIFFERENCES_2),
    (SRC_3, REF_3, DIFFERENCES_3)])
def test_compare(src, ref, expected_diff):
    c = Comparer(src, ref)
    assert c.compare() == expected_diff
