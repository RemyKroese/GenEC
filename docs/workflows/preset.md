# Preset Workflow

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

### What is it
The Preset Workflow executes predefined configurations stored in YAML files, enabling consistent and repeatable data extraction and comparison operations. This workflow is GenEC's primary automation mode, designed for production environments, scheduled tasks, and standardized analysis procedures.

### How does it work
The Preset Workflow operates through a streamlined execution model:

1. **Configuration loading**: GenEC reads the specified YAML preset file and validates its structure
2. **Parameter resolution**: Command-line arguments (source/reference files) are merged with preset configuration
3. **Validation**: Complete configuration is validated for consistency and completeness
4. **Direct execution**: GenEC processes files using the preset settings without user interaction
5. **Results output**: Data is extracted and optionally compared, with results saved in multiple formats

**Implementation details to be aware of:**
- Uses the `PresetWorkflow` class registered via the registry pattern (`@register_workflow("preset")`)
- Leverages YAML configuration files stored in the `GenEC/presets/` directory
- Supports both initialized (partial) and finalized (complete) configuration states
- Configuration merging follows a strict precedence: CLI args override preset values where applicable
- All filter types (regex, regex-list, positional) are supported through the same preset structure
- Validation occurs at both YAML parsing and configuration finalization stages

### When to use
The Preset Workflow is optimal for:
- **Production environments** requiring consistent, repeatable analysis
- **Automated systems** and scheduled tasks where human interaction isn't possible
- **Standardized procedures** with established extraction and comparison patterns
- **Batch processing** of multiple files using the same configuration
- **Quality assurance** where configuration consistency is critical
- **Team collaboration** where sharing analysis configurations is necessary

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
# Alternative syntax:
python -m GenEC.main preset --preset <preset_name> --source <source_file> [--reference <reference_file>]
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
# Single preset configuration
preset_name:
  cluster_filter: '\n'                    # Character(s) to split text into clusters
  text_filter_type: 'Regex'               # Options: 'Regex', 'Regex-list', 'Positional'
  text_filter: 'ERROR: (.+)'              # Filter configuration (varies by type)
  should_slice_clusters: false            # Enable/disable cluster slicing
  src_start_cluster_text: ''              # Source slice start marker (if slicing enabled)
  src_end_cluster_text: ''                # Source slice end marker (if slicing enabled)
  ref_start_cluster_text: ''              # Reference slice start marker (if slicing enabled)
  ref_end_cluster_text: ''                # Reference slice end marker (if slicing enabled)

# Multiple presets with inheritance (using YAML anchors)
main_preset: &main_preset
  cluster_filter: '\n'
  text_filter_type: 'Regex'
  text_filter: 'ERROR: (.+)'
  should_slice_clusters: false
  src_start_cluster_text: ''
  src_end_cluster_text: ''
  ref_start_cluster_text: ''
  ref_end_cluster_text: ''

# Preset inheriting from main_preset with overrides
specialized_preset:
  <<: *main_preset
  text_filter: 'WARNING: (.+)'
  should_slice_clusters: true
```

**Filter-specific text_filter examples:**
```yaml
# Regex filter
text_filter_type: 'Regex'
text_filter: 'ERROR: (.+)'

# Regex-list filter (uses lists in YAML)
text_filter_type: 'Regex-list'
text_filter: ['WARNING', 'SensorA', '(.+)']

# Positional filter (uses object structure)
text_filter_type: 'Positional'
text_filter:
  separator: ': '
  line: 3
  occurrence: 2
```**Configuration validation rules:**
- `text_filter_type` must be one of: `'Regex'`, `'Regex-list'`, `'Positional'` (case-sensitive)
- `cluster_filter` defaults to `'\n'` if not specified
- `should_slice_clusters` can be `true`/`false` to enable/disable text slicing
- All cluster text fields are optional and default to empty strings
- `text_filter` structure varies by filter type (string for Regex, list for Regex-list, object for Positional)
- All text values support escape sequences (`\n`, `\t`, etc.)
- YAML anchors (`&`) and references (`<<: *`) allow preset inheritance and reuse

### Preset File Management
**Creating presets:**
- Use the Basic Workflow and save configuration at completion
- Manually create YAML files following the structure above
- Copy and modify existing preset files as templates

**Preset naming conventions:**
- Use descriptive names reflecting the analysis purpose
- Follow snake_case naming: `error_analysis`, `sensor_data_extraction`
- Store in `GenEC/presets/` directory with `.yaml` extension

## Example

### Configuration File: `GenEC/presets/error_analysis.yaml`
```yaml
error_extraction:
  cluster_filter: '\n'
  text_filter_type: 'Regex'
  text_filter: 'ERROR: (.+)'
  should_slice_clusters: false
  src_start_cluster_text: ''
  src_end_cluster_text: ''
  ref_start_cluster_text: ''
  ref_end_cluster_text: ''
```

### Input
```bash
uv run python GenEC/main.py preset --preset error_analysis/error_extraction --source logs/application.log --reference logs/baseline.log
```

### Output
```
Loading preset: error_analysis
Processing source file: logs/application.log
Processing reference file: logs/baseline.log

Extraction completed:
  Source: 12 entries found
  Reference: 8 entries found

Comparison completed:
  Unique to source: 5 entries
  Unique to reference: 1 entry
  Common entries: 7 entries

Results saved to: output/preset_error_analysis/
```

**Results directory structure:**
```
output/preset_error_analysis/
├── result.json           # Complete structured data and comparison results
├── result.txt            # Human-readable formatted output
├── result.csv            # Tabular format for data analysis
├── result.yaml           # YAML format output
└── comparison_summary.txt # Detailed comparison analysis (if reference provided)
```

**Sample result.json:**
```json
{
  "extraction_results": {
    "source": [
      {"cluster_id": 1, "data": "Database connection failed"},
      {"cluster_id": 5, "data": "Authentication timeout"}
    ],
    "reference": [
      {"cluster_id": 2, "data": "Configuration error"}
    ]
  },
  "comparison_results": {
    "unique_to_source": ["Database connection failed", "Authentication timeout"],
    "unique_to_reference": ["Configuration error"],
    "common": []
  }
}
```

→ [Complete Preset Workflow Demo](../demos/preset-workflow-demo.md)
