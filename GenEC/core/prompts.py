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
            Key.CLUSTER_FILTER: '[bold cyan]Enter character(s) to split clusters[/bold cyan] (default: newline [\\n]): ',
            Key.SHOULD_SLICE_CLUSTERS: '[bold cyan]Compare only a subsection of clusters?[/bold cyan] \\[yes/y, Enter=skip]: ',
            Key.CLUSTER_TEXT: '[bold cyan]Text in {cluster} cluster where subsection should {position}[/bold cyan] (Enter=skip): ',
            Key.TEXT_FILTER_TYPE: '[bold cyan]Choose filter type:[/bold cyan]\n',
            Key.UNSUPPORTED_FILTER_TYPE: '[bold red]ERROR:[/bold red] Unsupported filter type: [yellow]{filter_type}[/yellow]',
            Key.POSITIONAL_SEPARATOR: '[bold cyan]Separator for counting[/bold cyan] (default: 1 space character): ',
            Key.POSITIONAL_LINE: '[bold cyan]Line number in cluster:[/bold cyan] ',
            Key.POSITIONAL_OCCURRENCE: '[bold cyan]Occurrence number:[/bold cyan] ',
            Key.REGEX_FILTER: '[bold cyan]Regex filter:[/bold cyan] ',
            Key.REGEX_LIST_FILTER: '[bold cyan]Regex filter for search {search}:[/bold cyan] ',
            Key.REGEX_LIST_CONTINUE: '[bold cyan]Add another search parameter?[/bold cyan] \\[yes/y, Enter=skip]: '
        },
        Section.USER_CHOICE: {
            Key.CHOICE: '[bold cyan]Select option[/bold cyan] [0-{max_index}]: ',
            Key.INVALID_CHOICE: '[bold red]ERROR:[/bold red] Invalid choice.',
            Key.EXIT_OPTION: '[bold]0.[/bold] Exit'
        },
        Section.WRITE_CONFIG: {
            Key.REQUEST_SAVE: '[bold cyan]Save this configuration?[/bold cyan] \\[yes/y, Enter=skip]: ',
            Key.NEW_PRESET_NAME: '[bold cyan]Preset name:[/bold cyan] ',
            Key.INVALID_PRESET_NAME: '[bold red]ERROR:[/bold red] Preset name cannot be empty.',
            Key.DESTINATION_FILE_NAME: ('[bold cyan]Destination YAML file[/bold cyan] (existing file will be appended).\n'
                                        'Default: [magenta]{presets_directory}[/magenta], or specify absolute path: '),
            Key.DESTINATION_FILE_FOUND: 'File [yellow]{file_path}[/yellow] exists → [green]appending preset[/green].',
            Key.DESTINATION_FILE_NOT_FOUND: 'File [yellow]{file_path}[/yellow] not found → [green]creating new file[/green].'
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
