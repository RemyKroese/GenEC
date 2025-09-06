# Preset-List Workflow

**[← Back to Documentation Overview](../overview.md)**

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

The Preset-List Workflow enables batch processing of multiple configurations defined within a single YAML file, allowing users to execute numerous extraction and comparison operations in sequence. This workflow is GenEC's most powerful automation mode, designed for comprehensive analysis scenarios where multiple extraction patterns need to be applied to the same dataset.

When you use the Preset-List Workflow, GenEC reads a special YAML file that references multiple existing preset configurations and applies each one sequentially to your source directory. Instead of creating inline configurations, preset-list files reference your existing preset files, making it easy to mix and match different extraction strategies. Each preset runs independently and saves its results to separate directories, giving you a comprehensive analysis from multiple perspectives in a single execution.

This workflow is particularly powerful because it allows you to leverage all your existing presets in combination. You can apply different filter types, extraction patterns, and comparison logic to the same dataset without running separate commands. GenEC handles the organization automatically, creating structured output directories that make it easy to review and compare results from different extraction approaches.

### When to use
- **Comprehensive analysis**
- **Batch data processing**
- **Automated reporting**

Preset-list mass-executes [presets](preset.md). So in situations where folders, instead of files should be analyzed, preset-list should be used.

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
| `--print-results` | flag | No | Print results to CLI (disabled by default when output files are specified for performance) |

**Basic syntax:**
```bash
uv run python GenEC/main.py preset-list --preset-list <preset_list_name> --source <source_directory> [--reference <reference_directory>]
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

### Performance Optimization

For large dataset processing, GenEC automatically optimizes performance by disabling CLI printing when output files are specified:

- **Default behavior**: When `--output-directory` and `--output-types` are provided, CLI printing is disabled for better performance
- **Override option**: Use `--print-results` to force CLI printing even when output files are specified
- **Terminal-only mode**: When no output files are specified, results are always printed to CLI

### YAML Configuration Structure
Preset list files reference existing preset configurations:

```yaml
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
- `preset` field references existing preset files in format `file/preset_name`
- `target` field specifies the filename within source/reference directories
- Variable names in target fields must be provided via CLI with the `--target-variables` parameter

### Preset List Management
**Creating preset lists:**
- First create individual preset files with desired configurations
- Create preset list files that reference existing presets
- Ensure all referenced preset files exist before execution
- Store in `GenEC/presets/` directory with `.yaml` extension for automatic discovery
- Alternatively the presets can be stored elsewhere, but then the `--presets-directory` parameter must be provided.

### Output Organization
The Preset-List Workflow creates a structured output hierarchy:
```
<specified_output_directory>/
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
└──────────────────────────────────────
```

## File and Preset Handling

GenEC gracefully handles missing files and failed presets during batch processing:

**Missing source files:** Skips analysis for that file and continues with remaining files.

**Missing reference files:** Continues with extraction-only mode (skips comparison).

**Missing presets:** Skips the preset and processes remaining ones normally.

This ensures preset-list workflows complete successfully even when some components are unavailable.
