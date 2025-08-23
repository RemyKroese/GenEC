# Preset Workflow

**[← Back to Documentation Overview](../overview.md)**

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

The Preset Workflow executes predefined configurations stored in YAML files, enabling consistent and repeatable data extraction and comparison operations. This workflow is GenEC's primary automation mode, designed for production environments, scheduled tasks, and standardized analysis procedures.

When you use the Preset Workflow, GenEC reads your specified YAML configuration file and applies those settings directly to your source files without any interactive prompts. This allows you to standardize your analysis procedures and ensure exactly the same extraction and comparison logic is applied every time. You simply point GenEC to your preset file and source data, and it handles everything automatically based on your predefined configuration.

Preset files contain all the configuration details that would normally be entered interactively in the Basic Workflow. This makes the Preset Workflow perfect for situations where you've already determined the optimal settings for your data and want to apply them consistently across multiple files or runs.

### When to use
- **Repetitive tasks**
- **Automated**
- **Automated Single file data extraction / analysis**
- **Structured large data files investigation**

When (automated) analysis of more than 1 file at a time is required, [preset-lists](preset-list.md) should be used instead

## How to use

### CLI Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--preset` / `-p` | string | Yes | Name of the preset file (without .yaml extension) or `file/preset_name` format |
| `--source` / `-s` | string | Yes | Path to the source file for data extraction |
| `--reference` / `-r` | string | No | Path to reference file for comparison (enables comparison mode) |
| `--presets-directory` / `-d` | string | No | Directory containing preset YAML files (default: `GenEC/presets/`) |
| `--output-directory` / `-o` | string | No | Directory to save output files (must be used with `--output-types`) |
| `--output-types` / `-t` | list | No | List of output file types: `csv`, `json`, `txt`, `yaml` (multiple allowed) |

**Basic syntax:**
```bash
uv run python GenEC/main.py preset --preset <preset_name> --source <source_file> [--reference <reference_file>]
```

**Extract-only mode:**
```bash
uv run python GenEC/main.py preset --preset error_analysis --source logs/current.log
```

**Extract-and-compare mode:**
```bash
uv run python GenEC/main.py preset --preset error_analysis --source logs/current.log --reference logs/baseline.log
```

### YAML Configuration Structure
Preset files use this structure:

```yaml
preset_name:
  cluster_filter: '\n'                    # Character(s) to split text into clusters
  text_filter_type: 'Regex'               # Options: 'Regex', 'Regex-list', 'Positional'
  text_filter: 'ERROR: (.+)'              # Filter configuration (varies by type)
  should_slice_clusters: false            # Enable/disable cluster slicing
  src_start_cluster_text: ''              # Source slice start marker (if slicing enabled)
  src_end_cluster_text: ''                # Source slice end marker (if slicing enabled)
  ref_start_cluster_text: ''              # Reference slice start marker (if slicing enabled)
  ref_end_cluster_text: ''                # Reference slice end marker (if slicing enabled)
```

**Configuration validation rules:**
- `text_filter_type` must be one of: `'Regex'`, `'Regex-list'`, `'Positional'` (case-sensitive)
- `text_filter` structure varies by filter type (string for Regex, list for Regex-list, object for Positional)
- `should_slice_clusters` can be `true`/`false` to enable/disable text slicing
- All cluster text fields are optional and default to empty strings

### Preset File Management
**Creating presets:**
- Use the Basic Workflow and save configuration at completion
- Manually create YAML files following the structure above
- Copy and modify existing preset files as templates
- Store in `GenEC/presets/` directory with `.yaml` extension for automatic discovery
- Alternatively the presets can be stored elsewhere, but then the `--presets-directory` parameter must be provided.
