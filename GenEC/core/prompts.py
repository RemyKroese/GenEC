"""Collection of prompts for CLI interaction."""

from enum import Enum


class Section(Enum):
    """Categories of prompts grouped by feature or functional area."""

    USER_CHOICE = 'user_choice'
    SET_CONFIG = 'set_config'
    WRITE_CONFIG = 'write_config'
    ERROR_HANDLING = 'error_handling'


# Individual prompts
class Key(Enum):
    """Identifiers for individual CLI prompt messages."""

    # USER CHOICE
    CHOICE = 'choice'
    INVALID_CHOICE = 'invalid_choice'
    EXIT_OPTION = 'exit_option'

    # SET_CONFIG
    CLUSTER_FILTER = 'cluster_filter'
    CLUSTER_FILTER_POSITIONAL = 'cluster_filter_positional'
    CLUSTER_FILTER_REGEX = 'cluster_filter_regex'
    CLUSTER_FILTER_REGEX_LIST = 'cluster_filter_regex_list'
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

    # ERROR_HANDLING
    INVALID_REGEX = 'invalid_regex'
    INVALID_REGEX_INPUT = 'invalid_regex_input'
    INVALID_INTEGER = 'invalid_integer'
    INVALID_LINE_NUMBER = 'invalid_line_number'
    INVALID_OCCURRENCE_NUMBER = 'invalid_occurrence_number'
    INVALID_FILE_PATH = 'invalid_file_path'
    FILE_READ_ERROR = 'file_read_error'
    PRESET_LOAD_ERROR = 'preset_load_error'
    PRESET_VALIDATION_ERROR = 'preset_validation_error'
    REGEX_COMPILATION_ERROR = 'regex_compilation_error'

    # VALIDATION
    ONLY_SHOW_DIFFERENCES_WITHOUT_REFERENCE = 'only_show_differences_without_reference'

    # CONFIGURATION_BUILDER
    REQUIRED_FIELD_MISSING = 'required_field_missing'
    TEXT_FILTER_TYPE_MISMATCH_STR = 'text_filter_type_mismatch_str'
    TEXT_FILTER_TYPE_MISMATCH_LIST = 'text_filter_type_mismatch_list'
    TEXT_FILTER_TYPE_MISMATCH_POSITIONAL = 'text_filter_type_mismatch_positional'
    TEXT_FILTER_LIST_ITEM_TYPE_ERROR = 'text_filter_list_item_type_error'
    INVALID_POSITIONAL_FILTER_CONFIG = 'invalid_positional_filter_config'

    # CONFIGURATION_MANAGER - Interactive configuration and preset handling
    SOURCE_START_CLUSTER_TEXT = 'source_start_cluster_text'
    SOURCE_END_CLUSTER_TEXT = 'source_end_cluster_text'
    REFERENCE_START_CLUSTER_TEXT = 'reference_start_cluster_text'
    REFERENCE_END_CLUSTER_TEXT = 'reference_end_cluster_text'
    LINE_NUMBER_REQUIRED = 'line_number_required'
    OCCURRENCE_NUMBER_REQUIRED = 'occurrence_number_required'
    NO_PRESETS_FOUND = 'no_presets_found'
    SKIPPING_PRESET = 'skipping_preset'
    SKIPPING_TARGET_FILE = 'skipping_target_file'
    SKIPPING_SOURCE_FILE = 'skipping_source_file'
    SKIPPING_REFERENCE_FILE = 'skipping_reference_file'
    CLI_PRINTING_DISABLED = 'cli_printing_disabled'


ENTER_IS_SKIP = '[gold]Enter[/gold]=[purple]skip[/purple]'
ENTER_IS_WHITESPACE = '[gold]Enter[/gold]=[purple]whitespace ( )[/purple]'
ENTER_IS_NEW_LINE = '[gold]Enter[/gold]=[purple]newline (\\n)[/purple]'
ENTER_IS_DOUBLE_NEW_LINE = '[gold]Enter[/gold]=[purple]double newline (\\n\\n)[/purple]'

prompts: dict[str, dict[Section, dict[Key, str]]] = {
    'common': {
        Section.SET_CONFIG: {
            Key.CLUSTER_FILTER: f'[bold cyan]Enter character(s) to split clusters[/bold cyan] \\[{ENTER_IS_NEW_LINE}]: ',
            Key.CLUSTER_FILTER_POSITIONAL: f'[bold cyan]Enter character(s) to split clusters[/bold cyan] \\[{ENTER_IS_DOUBLE_NEW_LINE}]: ',
            Key.CLUSTER_FILTER_REGEX: f'[bold cyan]Enter character(s) to split clusters[/bold cyan] \\[{ENTER_IS_NEW_LINE}]: ',
            Key.CLUSTER_FILTER_REGEX_LIST: f'[bold cyan]Enter character(s) to split clusters[/bold cyan] \\[{ENTER_IS_NEW_LINE}]: ',
            Key.SHOULD_SLICE_CLUSTERS: f'[bold cyan]Compare only a subsection of clusters?[/bold cyan] \\[yes/y, {ENTER_IS_SKIP}]: ',
            Key.CLUSTER_TEXT: ('[bold cyan]Text in {cluster} cluster where subsection should {position}[/bold cyan]'
                               f'\\[{ENTER_IS_SKIP}]: '),
            Key.TEXT_FILTER_TYPE: '[bold cyan]Choose filter type:[/bold cyan]',
            Key.UNSUPPORTED_FILTER_TYPE: '[bold red]ERROR:[/bold red] Unsupported filter type: [yellow]{filter_type}[/yellow]',
            Key.POSITIONAL_SEPARATOR: f'[bold cyan]Separator for counting[/bold cyan] \\[{ENTER_IS_WHITESPACE}]: ',
            Key.POSITIONAL_LINE: '[bold cyan]Line number in cluster:[/bold cyan] ',
            Key.POSITIONAL_OCCURRENCE: '[bold cyan]Occurrence number:[/bold cyan] ',
            Key.REGEX_FILTER: '[bold cyan]Regex filter:[/bold cyan] ',
            Key.REGEX_LIST_FILTER: '[bold cyan]Regex filter for search {search}:[/bold cyan] ',
            Key.REGEX_LIST_CONTINUE: f'[bold cyan]Add another search parameter?[/bold cyan] \\[yes/y, {ENTER_IS_SKIP}]: ',
            Key.SOURCE_START_CLUSTER_TEXT: f'[bold cyan]Source start cluster text[/bold cyan] \\[{ENTER_IS_SKIP}]: ',
            Key.SOURCE_END_CLUSTER_TEXT: f'[bold cyan]Source end cluster text[/bold cyan] \\[{ENTER_IS_SKIP}]: ',
            Key.REFERENCE_START_CLUSTER_TEXT: f'[bold cyan]Reference start cluster text[/bold cyan] \\[{ENTER_IS_SKIP}]: ',
            Key.REFERENCE_END_CLUSTER_TEXT: f'[bold cyan]Reference end cluster text[/bold cyan] \\[{ENTER_IS_SKIP}]: '
        },
        Section.USER_CHOICE: {
            Key.CHOICE: '[bold cyan]Select option[/bold cyan] [0-{max_index}]: ',
            Key.INVALID_CHOICE: '[bold red]ERROR: Invalid choice.[/bold red]',
            Key.EXIT_OPTION: '[bold]0.[/bold] [purple]Exit[/purple]'
        },
        Section.WRITE_CONFIG: {
            Key.REQUEST_SAVE: f'[bold cyan]Save this configuration?[/bold cyan] \\[yes/y, {ENTER_IS_SKIP}]: ',
            Key.NEW_PRESET_NAME: '[bold cyan]Preset name:[/bold cyan] ',
            Key.INVALID_PRESET_NAME: '[bold red]ERROR: Preset name cannot be empty.[/bold red]',
            Key.DESTINATION_FILE_NAME: ('[bold cyan]Destination YAML file[/bold cyan] (existing file will be appended).\n'
                                        'Default: [magenta]{presets_directory}[/magenta], or specify absolute path: '),
            Key.DESTINATION_FILE_FOUND: 'File [yellow]{file_path}[/yellow] exists → [green]appending preset[/green].',
            Key.DESTINATION_FILE_NOT_FOUND: 'File [yellow]{file_path}[/yellow] not found → [green]creating new file[/green].'
        },
        Section.ERROR_HANDLING: {
            Key.INVALID_REGEX: ('[bold red]ERROR: Invalid regex pattern:[/bold red] [yellow]{pattern}[/yellow]. '
                                '[bold red]Please enter a valid regex.[/bold red]'),
            Key.INVALID_REGEX_INPUT: '[bold red]Invalid regex pattern. Please enter a valid regex.[/bold red]',
            Key.INVALID_INTEGER: ('[bold red]ERROR:[/bold red] Invalid number: [yellow]{value}[/yellow]. '
                                  '[bold red]Please enter a valid integer{bounds}.[/bold red]'),
            Key.INVALID_LINE_NUMBER: '[bold red]Invalid line number. Please enter a positive integer.[/bold red]',
            Key.INVALID_OCCURRENCE_NUMBER: '[bold red]Invalid occurrence number. Please enter a positive integer.[/bold red]',
            Key.INVALID_FILE_PATH: '[bold red]ERROR: Invalid file path:[/bold red] [yellow]{path}[/yellow]. {reason}',
            Key.FILE_READ_ERROR: '[bold red]ERROR: Could not read file[/bold red] [yellow]{file_path}[/yellow]: {error}',
            Key.PRESET_LOAD_ERROR: '[bold red]PRESET ERROR: Failed to load preset[/bold red] [yellow]{preset}[/yellow]: {error}',
            Key.PRESET_VALIDATION_ERROR: '[bold red]PRESET ERROR:[/bold red] Invalid preset [yellow]{preset}[/yellow]: {error}',
            Key.REGEX_COMPILATION_ERROR: '[bold red]ERROR: Invalid regex pattern:[/bold red] [yellow]{error}[/yellow]',
            Key.REQUIRED_FIELD_MISSING: ('[bold red]ERROR: Required field[/bold red] [yellow]{field_name}[/yellow] '
                                         '[bold red]is missing[/bold red]'),
            Key.TEXT_FILTER_TYPE_MISMATCH_STR: ('[bold red]ERROR: text_filter must be str for[/bold red] '
                                                '[yellow]{filter_type}[/yellow], [bold red]got[/bold red] '
                                                '[yellow]{actual_type}[/yellow]'),
            Key.TEXT_FILTER_TYPE_MISMATCH_LIST: ('[bold red]ERROR: text_filter must be list for[/bold red] '
                                                 '[yellow]{filter_type}[/yellow], [bold red]got[/bold red] '
                                                 '[yellow]{actual_type}[/yellow]'),
            Key.TEXT_FILTER_TYPE_MISMATCH_POSITIONAL: ('[bold red]ERROR: text_filter must be PositionalFilterType for[/bold red] '
                                                       '[yellow]{filter_type}[/yellow], [bold red]got[/bold red] '
                                                       '[yellow]{actual_type}[/yellow]'),
            Key.TEXT_FILTER_LIST_ITEM_TYPE_ERROR: ('[bold red]ERROR: Item[/bold red] [yellow]{item_index}[/yellow] '
                                                   '[bold red]in text_filter must be string, got[/bold red] '
                                                   '[yellow]{actual_type}[/yellow]'),
            Key.INVALID_POSITIONAL_FILTER_CONFIG: ('[bold red]ERROR: Invalid positional filter configuration:[/bold red] '
                                                   '[yellow]{error}[/yellow]'),
            Key.LINE_NUMBER_REQUIRED: '[bold red]ERROR: Line number is required for positional filter[/bold red]',
            Key.OCCURRENCE_NUMBER_REQUIRED: '[bold red]ERROR: Occurrence number is required for positional filter[/bold red]',
            Key.NO_PRESETS_FOUND: '[bold red]ERROR: None of the provided presets were found[/bold red]',
            Key.SKIPPING_PRESET: '[yellow]Skipping preset {preset}: {error}[/yellow]',
            Key.SKIPPING_TARGET_FILE: '[yellow]Skipping target file {target_file}: {error}[/yellow]',
            Key.SKIPPING_SOURCE_FILE: '[bold red]source file[/bold red] {target_file} not found - [red]skipping analysis[/red]',
            Key.SKIPPING_REFERENCE_FILE: '[bold cyan]reference file[/bold cyan] {target_file} not found - [cyan]skipping comparison[/cyan]',
            Key.CLI_PRINTING_DISABLED: '[yellow]CLI printing disabled for performance. Use --print-results to enable.[/yellow]',
            Key.ONLY_SHOW_DIFFERENCES_WITHOUT_REFERENCE: ('[yellow]WARNING: --only-show-differences requires a --reference parameter[/yellow]')
        }
    }
}


def create_prompt(feature: Section, prompt_key: Key, workflow: str = 'common', **kwargs: object) -> str:
    """
    Retrieve a formatted CLI prompt string with optional filter-type context.

    Parameters
    ----------
    feature : Section
        Feature category of the prompt
    prompt_key : Key
        Specific prompt identifier
    workflow : str, optional
        Workflow context to use, by default 'common'
    filter_type : Optional[str], optional
        Filter type context for SET_CONFIG prompts, by default None

    Returns
    -------
    str
        Formatted prompt string ready for display or input()
    """
    text = prompts[workflow][feature][prompt_key]
    return text.format(**kwargs) if kwargs else text
