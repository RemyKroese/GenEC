"""Collection of prompts for CLI interaction."""

from enum import Enum


class Section(Enum):
    """Categories of prompts grouped by feature or functional area."""

    USER_CHOICE = 'user_choice'
    SET_CONFIG = 'set_config'
    WRITE_CONFIG = 'write_config'


# Individual prompts
class Key(Enum):
    """Identifiers for individual CLI prompt messages."""

    # USER CHOICE
    CHOICE = 'choice'
    INVALID_CHOICE = 'invalid_choice'
    EXIT_OPTION = 'exit_option'

    # SET_CONFIG
    CLUSTER_FILTER = 'cluster_filter'
    SHOULD_SLICE_CLUSTERS = 'should_slice_clusters'
    CLUSTER_TEXT = 'cluster_text'
    TEXT_FILTER_TYPE = 'text_filter_type'
    UNSUPPORTED_FILTER_TYPE = 'unsupported_filter_type'
    POSITIONAL_SEPARATOR = 'positional_separator'
    POSITIONAL_LINE = 'positional_line'
    POSITIONAL_OCCURRENCE = 'positional_occurrence'
    REGEX_FILTER = 'regex_filter'
    REGEX_LIST_FILTER = 'regex_list_filter'
    REGEX_LIST_CONTINUE = 'regex_list_continue'

    # WRITE_CONFIG
    REQUEST_SAVE = 'request_save'
    NEW_PRESET_NAME = 'preset_name'
    INVALID_PRESET_NAME = 'invalid_preset_name'
    DESTINATION_FILE_NAME = 'destination_file_name'
    DESTINATION_FILE_FOUND = 'destination_file_found'
    DESTINATION_FILE_NOT_FOUND = 'destination_file_not_found'


prompts: dict[str, dict[Section, dict[Key, str]]] = {
    'common': {
        Section.SET_CONFIG: {
            Key.CLUSTER_FILTER: 'Please indicate the character(s) to split text clusters on (Default: Newline [\\n]): ',
            Key.SHOULD_SLICE_CLUSTERS: 'Do you want to compare only a subsection of the clusters (press enter to skip)? [yes/y]: ',
            Key.CLUSTER_TEXT: 'Text in the {cluster} cluster where the subsection should {position} (press enter to skip): ',
            Key.TEXT_FILTER_TYPE: 'Please choose a filter type:\n',
            Key.UNSUPPORTED_FILTER_TYPE: 'Unsupported filter type: {filter_type}',
            Key.POSITIONAL_SEPARATOR: 'Please provide the separator for counting (default: 1 space character): ',
            Key.POSITIONAL_LINE: 'Please provide the line number in the cluster: ',
            Key.POSITIONAL_OCCURRENCE: 'Please provide the occurrence number: ',
            Key.REGEX_FILTER: 'Please provide a regex filter: ',
            Key.REGEX_LIST_FILTER: 'Please provide a regex filter for search {search}: ',
            Key.REGEX_LIST_CONTINUE: 'Do you wish to provide a next search parameter [yes/y]: '
        },
        Section.USER_CHOICE: {
            Key.CHOICE: 'Choose a number [0-{max_index}]: ',
            Key.INVALID_CHOICE: 'Please enter a valid number.',
            Key.EXIT_OPTION: '0. Exit'
        },
        Section.WRITE_CONFIG: {
            Key.REQUEST_SAVE: 'Would you like to save this extraction configuration [yes/y]: ',
            Key.NEW_PRESET_NAME: 'Please choose a preset name: ',
            Key.INVALID_PRESET_NAME: 'Error: Preset name cannot be empty. Please try again.',
            Key.DESTINATION_FILE_NAME: ('Please choose a destination yaml file to store the preset (an existing file can be used).\n'
                                        'By default the preset will be stored in {presets_directory}, '
                                        'but an absolute path can be specified instead: '),
            Key.DESTINATION_FILE_FOUND: 'File [{file_path}] found. The preset will be appended.',
            Key.DESTINATION_FILE_NOT_FOUND: 'File [{file_path}] does not exist. A new file will be created.'
        }
    }
}


def create_prompt(feature: Section, prompt_key: Key, workflow: str = 'common', **kwargs: object) -> str:
    """
    Retrieve a formatted CLI prompt string for the given feature and prompt key.

    Parameters
    ----------
    feature : Features
        Feature category of the prompt
    prompt_key : PromptKeys
        Specific prompt identifier
    workflow : str, optional
        Workflow context to use, by default 'common'

    Returns
    -------
    str
        Formatted prompt string ready for display or input()
    """
    text = prompts[workflow][feature][prompt_key]
    return text.format(**kwargs) if kwargs else text
