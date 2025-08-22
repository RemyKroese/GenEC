"""Unit tests for GenEC ConfigManager input collection methods."""
from __future__ import annotations

from typing import Any, Union
from unittest.mock import patch, Mock
import pytest

from GenEC.core import TextFilterTypes, PositionalFilterType
from GenEC.core.config_manager import ConfigManager
from GenEC.core.types.preset_config import Initialized

@pytest.mark.unit
@patch.object(ConfigManager, '_ask_open_question')
def test_collect_cluster_filter(mock_ask_open_question: Mock) -> None:
    mock_ask_open_question.return_value = ';'
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    config: Initialized = {
        'cluster_filter': None,
        'text_filter_type': None,
        'text_filter': None,
        'should_slice_clusters': None,
        'src_start_cluster_text': None,
        'src_end_cluster_text': None,
        'ref_start_cluster_text': None,
        'ref_end_cluster_text': None
    }
    assert config_manager._collect_cluster_filter(config) == ';'


@pytest.mark.unit
def test_collect_cluster_filter_from_config() -> None:
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    config: Initialized = {
        'cluster_filter': '\n',
        'text_filter_type': None,
        'text_filter': None,
        'should_slice_clusters': None,
        'src_start_cluster_text': None,
        'src_end_cluster_text': None,
        'ref_start_cluster_text': None,
        'ref_end_cluster_text': None
    }
    assert config_manager._collect_cluster_filter(config) == '\n'


@pytest.mark.unit
@patch.object(ConfigManager, '_ask_mpc_question')
def test_collect_text_filter_type(mock_ask_mpc_question: Mock) -> None:
    mock_ask_mpc_question.return_value = 'regex'
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    config: Initialized = {
        'cluster_filter': None,
        'text_filter_type': None,
        'text_filter': None,
        'should_slice_clusters': None,
        'src_start_cluster_text': None,
        'src_end_cluster_text': None,
        'ref_start_cluster_text': None,
        'ref_end_cluster_text': None
    }
    assert config_manager._collect_text_filter_type(config) == 'regex'


@pytest.mark.unit
@patch.object(ConfigManager, '_request_text_filter')
def test_collect_text_filter(mock_request_text_filter: Mock) -> None:
    mock_request_text_filter.return_value = 'filter1'
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    config: Initialized = {
        'cluster_filter': None,
        'text_filter_type': None,
        'text_filter': None,
        'should_slice_clusters': None,
        'src_start_cluster_text': None,
        'src_end_cluster_text': None,
        'ref_start_cluster_text': None,
        'ref_end_cluster_text': None
    }
    assert config_manager._collect_text_filter(config) == 'filter1'


@pytest.mark.unit
@pytest.mark.parametrize('user_input, expected', [
    ('yes', True),
    ('no', False)
])
@patch.object(ConfigManager, '_ask_open_question')
def test_collect_should_slice_clusters(mock_ask_open_question: Mock, user_input: str, expected: bool) -> None:
    mock_ask_open_question.return_value = user_input
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    config: Initialized = {
        'cluster_filter': None,
        'text_filter_type': None,
        'text_filter': None,
        'should_slice_clusters': None,
        'src_start_cluster_text': None,
        'src_end_cluster_text': None,
        'ref_start_cluster_text': None,
        'ref_end_cluster_text': None
    }
    assert config_manager._collect_should_slice_clusters(config) == expected


@pytest.mark.unit
@pytest.mark.parametrize('config_option, position, src_or_ref', [
    ('src_start_cluster_text', 'start', 'SRC'),
    ('src_end_cluster_text', 'end', 'SRC'),
    ('ref_start_cluster_text', 'start', 'REF'),
    ('ref_end_cluster_text', 'end', 'REF'),
])
@patch.object(ConfigManager, '_ask_open_question')
def test_collect_cluster_text(mock_ask_open_question: Mock, config_option: str, position: str, src_or_ref: str) -> None:
    mock_ask_open_question.return_value = 'cluster_text'
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    config: Initialized = {
        'cluster_filter': None,
        'text_filter_type': None,
        'text_filter': None,
        'should_slice_clusters': None,
        'src_start_cluster_text': None,
        'src_end_cluster_text': None,
        'ref_start_cluster_text': None,
        'ref_end_cluster_text': None
    }
    result: str = config_manager._collect_cluster_text(config, config_option, position, src_or_ref)
    assert result == 'cluster_text'


@pytest.mark.unit
def test_ask_open_question() -> None:
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    with patch('builtins.input', return_value='user_input'):
        assert config_manager._ask_open_question('Test prompt: ') == 'user_input'


@pytest.mark.unit
@patch.object(ConfigManager, '_get_user_choice')
def test_ask_mpc_question_valid_choice(mock_get_user_choice: Mock) -> None:
    mock_get_user_choice.return_value = 1
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    options: list[str] = ['option1', 'option2']
    assert config_manager._ask_mpc_question('Choose:', options) == 'option1'


@pytest.mark.unit
@patch.object(ConfigManager, '_get_user_choice')
@patch('builtins.input', return_value='invalid')
def test_ask_mpc_question_invalid_choice(mock_input: Mock, mock_get_user_choice: Mock) -> None:
    mock_get_user_choice.side_effect = [ValueError, 2]
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    options: list[str] = ['option1', 'option2']
    # This should handle the ValueError and then work on second try
    mock_get_user_choice.side_effect = [2]
    assert config_manager._ask_mpc_question('Choose:', options) == 'option2'


@pytest.mark.unit
@patch.object(ConfigManager, '_get_user_choice')
def test_ask_mpc_question_exit(mock_get_user_choice: Mock) -> None:
    mock_get_user_choice.return_value = 0
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    options: list[str] = ['option1', 'option2']
    with pytest.raises(SystemExit):
        config_manager._ask_mpc_question('Choose:', options)


@pytest.mark.unit
@patch.object(ConfigManager, '_ask_open_question')
def test_request_REGEX_filter_type(mock_ask_open_question: Mock) -> None:
    mock_ask_open_question.return_value = 'my_filter'
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    config: Initialized = {
        'cluster_filter': None,
        'text_filter_type': TextFilterTypes.REGEX.value,
        'text_filter': None,
        'should_slice_clusters': None,
        'src_start_cluster_text': None,
        'src_end_cluster_text': None,
        'ref_start_cluster_text': None,
        'ref_end_cluster_text': None
    }
    assert config_manager._request_text_filter(config) == 'my_filter'


@pytest.mark.unit
@pytest.mark.parametrize('mock_side_effect, mock_output', [
    ([' ', '2', '4'], [' ', 2, 4]),
    (['', '3', '8'], [' ', 3, 8]),
    (['ABC', '4', '2'], ['ABC', 4, 2])
])
@patch.object(ConfigManager, '_ask_open_question')
def test_request_POSITIONAL_filter_type(mock_ask_open_question: Mock, mock_side_effect: list[str], mock_output: list[Any]) -> None:
    mock_ask_open_question.side_effect = mock_side_effect
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    config: Initialized = {
        'cluster_filter': None,
        'text_filter_type': TextFilterTypes.POSITIONAL.value,
        'text_filter': None,
        'should_slice_clusters': None,
        'src_start_cluster_text': None,
        'src_end_cluster_text': None,
        'ref_start_cluster_text': None,
        'ref_end_cluster_text': None
    }
    result: Union[str, list[str], PositionalFilterType] = config_manager._request_text_filter(config)
    expected: PositionalFilterType = PositionalFilterType(separator=str(mock_output[0]), line=int(mock_output[1]), occurrence=int(mock_output[2]))
    assert result == expected


@pytest.mark.unit
@pytest.mark.parametrize('mock_side_effect, mock_output', [
    (['regex_1', 'y', 'regex_2', 'done'], ['regex_1', 'regex_2']),
    (['regex_1', 'n'], ['regex_1']),
    (['regex_1', 'Y', 'regex_2', 'YeS', 'regex_3', ''], ['regex_1', 'regex_2', 'regex_3']),
])
@patch.object(ConfigManager, '_ask_open_question')
def test_request_REGEX_LIST_filter_type(mock_ask_open_question: Mock, mock_side_effect: list[str], mock_output: list[str]) -> None:
    mock_ask_open_question.side_effect = mock_side_effect
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    config: Initialized = {
        'cluster_filter': None,
        'text_filter_type': TextFilterTypes.REGEX_LIST.value,
        'text_filter': None,
        'should_slice_clusters': None,
        'src_start_cluster_text': None,
        'src_end_cluster_text': None,
        'ref_start_cluster_text': None,
        'ref_end_cluster_text': None
    }
    assert config_manager._request_text_filter(config) == mock_output


@pytest.mark.unit
@pytest.mark.parametrize('filter_type', [
    'Keyword_UNSUPPORTED',
    'Split-keywords_UNSUPPORTED'
])
def test_request_unsupported_filter_type(filter_type: str) -> None:
    config_manager: ConfigManager = ConfigManager(auto_configure=False)
    config: Initialized = {
        'cluster_filter': None,
        'text_filter_type': filter_type,
        'text_filter': None,
        'should_slice_clusters': None,
        'src_start_cluster_text': None,
        'src_end_cluster_text': None,
        'ref_start_cluster_text': None,
        'ref_end_cluster_text': None
    }
    with pytest.raises(ValueError):
        config_manager._request_text_filter(config)
