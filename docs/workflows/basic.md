# Basic Workflow

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

### What is it
The Basic Workflow is GenEC's interactive mode that guides users through configuration setup via command-line prompts. It's designed for first-time users, ad-hoc analysis, and situations where you want to experiment with different settings before saving them as presets.

### How does it work
The Basic Workflow operates through a step-by-step interactive process:

1. **Command execution**: Run `uv run python GenEC/main.py basic --source <file>` with required source file
2. **Interactive prompts**: GenEC presents a series of configuration questions in logical order
3. **Real-time validation**: Each input is validated immediately with helpful error messages and retry prompts
4. **Configuration building**: Responses are compiled into a complete configuration object
5. **Execution**: GenEC processes the files using the configured settings
6. **Optional saving**: After successful execution, users can save the configuration as a preset for future use

**Implementation details to be aware of:**
- Uses the `BasicWorkflow` class registered via the registry pattern (`@register_workflow("basic")`)
- Leverages input strategies (`get_input_strategy()`) for filter-specific prompts
- Configuration is built incrementally using the `ConfigManager.set_config()` method
- All user prompts are centralized in `prompts.py` with Rich formatting for consistency
- Supports both extract-only and extract-and-compare modes based on whether reference file is provided
- Configuration validation occurs at each step to prevent invalid combinations

### When to use
The Basic Workflow is optimal for:
- **First-time users** learning GenEC's capabilities and understanding available options
- **Experimental analysis** where you want to test different filter types and settings
- **One-off tasks** that don't require automation or repeatability
- **Configuration development** before creating reusable preset files
- **Training scenarios** where understanding the full configuration process is valuable

## How to use

### CLI Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--source` / `-s` | string | Yes | Path to the source file for data extraction |
| `--reference` / `-r` | string | No | Path to reference file for comparison (enables comparison mode) |
| `--output-directory` / `-o` | string | No | Directory to save output files (must be used with `--output-types`) |
| `--output-types` / `-t` | list | No | List of output file types: `csv`, `json`, `txt`, `yaml` (multiple allowed) |

**Basic syntax:**
```bash
uv run python GenEC/main.py basic --source <source_file> [--reference <reference_file>]
# Alternative syntax:
python -m GenEC.main basic --source <source_file> [--reference <reference_file>]
```

**With custom output control:**
```bash
uv run python GenEC/main.py basic -s <source_file> -r <reference_file> -o <output_dir> -t json csv txt
```

**Extract-only mode:**
```bash
uv run python GenEC/main.py basic --source logs/application.log
```

**Extract-and-compare mode:**
```bash
uv run python GenEC/main.py basic --source logs/app_current.log --reference logs/app_previous.log
```

**With custom output directory and formats:**
```bash
uv run python GenEC/main.py basic -s logs/app.log -r logs/baseline.log -o /path/to/results -t json csv txt yaml
```

### Configuration Parameters
The Basic Workflow prompts for all configuration parameters interactively. No YAML configuration file is required, but the following parameters will be requested:

| Configuration | Options | Description |
|---------------|---------|-------------|
| **Filter Type** | Regex, Regex-list, Positional | Text extraction method |
| **Cluster Filter** | Any string (default: `\n`) | How to divide text into processable chunks |
| **Text Filter** | Varies by filter type | Pattern or position specification for data extraction |
| **Slice Clusters** | yes/no | Whether to limit processing to specific text sections |
| **Save Configuration** | yes/no | Option to save settings as preset for future use |

## Example

### Input
```bash
uv run python GenEC/main.py basic --source logs/application.log
```

### Output
```
Choose filter type:
0. Exit
1. Regex
2. Regex-list
3. Positional
Select option (0-3): 1

Enter character(s) to split clusters [Enter=newline (\n)]:
Regex filter: ERROR: (.+)

Compare only a subsection of clusters? [yes/y, Enter=skip]:

Processing source file: logs/application.log
Extraction completed: 5 entries found

Save this configuration? [yes/y, Enter=skip]: y
Preset name: error_extraction
Destination YAML file: error_analysis

Configuration saved successfully.
Results saved to: output/basic_error_extraction/
```

**Results directory structure:**
```
output/basic_error_extraction/
├── <source_filename>/
│   ├── result.json    # Structured JSON output
│   ├── result.txt     # Human-readable text format
│   ├── result.csv     # Tabular CSV format
│   └── result.yaml    # YAML format output
└── (additional files for other sources if multiple runs)
```

**Saved preset file:**
```
/path/to/specified/location/error_analysis.yaml  # User-specified preset location
```

→ [Complete Basic Workflow Demo](../demos/basic-workflow-demo.md)
