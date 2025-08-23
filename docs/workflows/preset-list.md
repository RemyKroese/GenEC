# Preset-List Workflow

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

### What is it
The Preset-List Workflow enables batch processing of multiple configurations defined within a single YAML file, allowing users to execute numerous extraction and comparison operations in sequence. This workflow is GenEC's most powerful automation mode, designed for comprehensive analysis scenarios where multiple extraction patterns need to be applied to the same dataset.

### How does it work
The Preset-List Workflow operates through a batch execution model:

1. **Preset list loading**: GenEC reads a YAML file containing multiple preset configurations
2. **Sequential execution**: Each preset configuration is processed individually in the order defined
3. **Independent validation**: Each preset is validated separately before execution
4. **Isolated processing**: Each configuration runs independently with its own output directory
5. **Aggregated results**: Results from all presets are saved in separate directories under a common parent folder
6. **Progress tracking**: GenEC provides status updates for each preset execution

**Implementation details to be aware of:**
- Uses the `PresetListWorkflow` class registered via the registry pattern (`@register_workflow("preset-list")`)
- Processes YAML files containing a list of preset configurations under a single key
- Each preset within the list follows the same structure as individual preset files
- Execution order follows the sequence defined in the YAML file
- Each preset execution is independent - failure of one preset doesn't stop others
- Output directories are created with indexed naming for organization
- All filter types (regex, regex-list, positional) are supported within each preset

### When to use
The Preset-List Workflow is optimal for:
- **Comprehensive analysis** requiring multiple extraction patterns on the same data
- **Batch processing scenarios** where different configurations need to be applied systematically
- **Quality assurance testing** with multiple validation patterns
- **Research and exploration** where various extraction approaches are being compared
- **Automated reporting** requiring data extraction from multiple perspectives
- **Migration scenarios** where data needs to be extracted using different legacy patterns
- **Performance testing** of different filter configurations

## How to use

### CLI Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--preset-list` / `-l` | string | Yes | Name of the preset list file (without .yaml extension) |
| `--source` / `-s` | string | Yes | Path to the source directory for data extraction |
| `--reference` / `-r` | string | No | Path to reference directory for comparison (enables comparison mode) |
| `--presets-directory` / `-d` | string | No | Directory containing preset YAML files (default: `GenEC/presets/`) |
| `--target-variables` / `-v` | list | No | Key-value pairs (`key=value`) for variable substitution (can be specified multiple times) |
| `--output-directory` / `-o` | string | No | Directory to save output files (must be used with `--output-types`) |
| `--output-types` / `-t` | list | No | List of output file types: `csv`, `json`, `txt`, `yaml` (multiple allowed) |

**Basic syntax:**
```bash
uv run python GenEC/main.py preset-list --preset-list <preset_list_name> --source <source_directory> [--reference <reference_directory>]
# Alternative syntax:
python -m GenEC.main preset-list --preset-list <preset_list_name> --source <source_directory> [--reference <reference_directory>]
```

**Extract-only mode:**
```bash
uv run python GenEC/main.py preset-list --preset-list comprehensive_analysis --source logs/
```

**Extract-and-compare mode:**
```bash
uv run python GenEC/main.py preset-list --preset-list comprehensive_analysis --source logs/current/ --reference logs/baseline/
```

**With variable substitution:**
```bash
uv run python GenEC/main.py preset-list -l analysis_suite -s logs/current/ -r logs/baseline/ -v environment=production version=1.2.3
```

### YAML Configuration Structure
Preset list files reference existing preset configurations:

```yaml
# Preset list referencing existing preset configurations
group_name_1:
  - preset: 'preset_file/preset_name'    # Reference to existing preset
    target: 'filename.txt'               # Target file for this preset
  - preset: 'another_file/preset_name'   # Second preset in group
    target: 'another_file.txt'           # Target file for second preset

group_name_2:
  - preset: 'preset_file/preset_name'    # Same preset, different target
    target: '{variable}_file.txt'        # Variable substitution supported
  - preset: 'preset_file/other_preset'   # Different preset
    target: 'static_file.txt'            # Static target file
```

**Configuration validation rules:**
- Top-level keys are group names for organizing preset executions
- Each group contains a list of preset-target pairs
- `preset` field references existing preset files in format `file/preset_name`
- `target` field specifies the filename within source/reference directories
- Variable substitution uses `{variable_name}` syntax in target fields
- Referenced preset files must exist in the presets directory
- All target files must exist in the specified source directory

**Variable Substitution:**
```yaml
# Preset list with variables
analysis_group:
  - preset: 'error_patterns/critical_errors'
    target: '{environment}_application.log'
  - preset: 'error_patterns/warnings'
    target: '{environment}_warnings.log'

# CLI usage with variables:
# --target-variables environment=production
# Results in targets: production_application.log, production_warnings.log
```**Configuration validation rules:**
- Top-level keys are group names for organizing preset executions
- Each group contains a list of preset-target pairs
- `preset` field references existing preset files in format `file/preset_name`
- `target` field specifies the filename within source/reference directories
- Variable substitution uses `{variable_name}` syntax in target fields
- Referenced preset files must exist in the presets directory
- All target files must exist in the specified source directory

### Preset List Management
**Creating preset lists:**
- First create individual preset files with desired configurations
- Create preset list files that reference existing presets
- Use descriptive group names for logical organization
- Ensure all referenced preset files exist before execution

**Naming conventions:**
- Use descriptive list names: `daily_analysis`, `error_monitoring`, `performance_checks`
- Group names should be clear: `critical_errors`, `warning_patterns`, `info_messages`
- Follow snake_case naming throughout
- Store in `GenEC/presets/` directory with `.yaml` extension

**Prerequisites:**
- All referenced preset files must exist in presets directory
- All target files must exist in source directory
- Variable names in target fields must be provided via CLI

### Output Organization
The Preset-List Workflow creates a structured output hierarchy:
```
output/preset_list_<preset_list_name>/
├── <source_directory_name>/
│   ├── <group_1>/
│   │   ├── result.json
│   │   ├── result.txt
│   │   ├── result.csv
│   │   └── result.yaml
│   ├── <group_2>/
│   │   ├── result.json
│   │   ├── result.txt
│   │   ├── result.csv
│   │   └── result.yaml
│   └── (additional groups as defined)
└── execution_summary.json  # Overall execution status
```

## Example

### Configuration File: `GenEC/presets/log_analysis.yaml`
```yaml
error_monitoring:
  - preset: 'error_patterns/critical_errors'
    target: 'application.log'
  - preset: 'error_patterns/warnings'
    target: 'application.log'

performance_monitoring:
  - preset: 'performance_patterns/response_times'
    target: 'performance.log'
  - preset: 'performance_patterns/memory_usage'
    target: 'system.log'
```

**Referenced preset files must exist:**
- `GenEC/presets/error_patterns.yaml` containing `critical_errors` and `warnings` presets
- `GenEC/presets/performance_patterns.yaml` containing `response_times` and `memory_usage` presets

### Input
```bash
uv run python GenEC/main.py preset-list --preset-list log_analysis --source logs/ --reference baseline_logs/
```

### Output
```
Loading preset list: log_analysis
Found 2 groups to process

Processing group 1/2: error_monitoring
  Preset: error_patterns/critical_errors → application.log
    Source: 8 entries found
    Reference: 5 entries found
  Preset: error_patterns/warnings → application.log
    Source: 15 entries found
    Reference: 12 entries found

Processing group 2/2: performance_monitoring
  Preset: performance_patterns/response_times → performance.log
    Source: 42 entries found
    Reference: 38 entries found
  Preset: performance_patterns/memory_usage → system.log
    Source: 23 entries found
    Reference: 19 entries found

All groups completed successfully
Results saved to: output/preset_list_log_analysis/
```

**Results directory structure:**
```
output/preset_list_log_analysis/
├── logs/                           # Source directory name
│   ├── error_monitoring/           # First group results
│   │   ├── result.json            # Combined results from group presets
│   │   ├── result.txt             # Human-readable format
│   │   ├── result.csv             # Tabular format
│   │   ├── result.yaml            # YAML format
│   │   └── comparison_summary.txt # Comparison details (if reference provided)
│   ├── performance_monitoring/    # Second group results
│   │   ├── result.json
│   │   ├── result.txt
│   │   ├── result.csv
│   │   ├── result.yaml
│   │   └── comparison_summary.txt
└── execution_summary.json         # Overall execution status and statistics
```

**Sample execution_summary.json:**
```json
{
  "preset_list_name": "log_analysis",
  "total_groups": 2,
  "successful_groups": 2,
  "failed_groups": 0,
  "group_summary": [
    {
      "group_name": "error_monitoring",
      "status": "success",
      "presets_executed": 2,
      "total_source_entries": 23,
      "total_reference_entries": 17
    },
    {
      "group_name": "performance_monitoring",
      "status": "success",
      "presets_executed": 2,
      "total_source_entries": 65,
      "total_reference_entries": 57
    }
  ]
}
```

→ [Complete Preset-List Workflow Demo](../demos/preset-list-workflow-demo.md)
