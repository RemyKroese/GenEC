# Preset Configuration

**[← Back to Documentation Overview](../overview.md)**

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

## Context

Preset configuration files define the extraction settings that GenEC applies to your data. These YAML files contain all the parameters that would normally be entered interactively in the Basic Workflow.

When you create a preset, you're essentially saving a recipe for data extraction that can be reused across multiple files and runs. This makes your analysis repeatable and allows you to standardize extraction procedures. Presets support inheritance patterns, so you can create base configurations and extend them for specific use cases.

Preset files are stored with `.yaml` extensions and can contain multiple preset configurations within a single file. Each preset has a unique name and can be referenced individually when running the Preset Workflow.

## How to use
Preset files are part of both the [Preset workflow](../workflows/preset.md) and the [Preset-list workflow](../workflows/preset-list.md). Note that in both workflows a preset is provided through the following syntax: `<preset_file_name_without_extension>/<preset_name>`
- in the preset workflow: Provide the preset through the CLI `--preset` / `-p` parameter.
- in the preset-list workflow: Provide the preset as a list entry within a preset-list.yaml file
  - Preset-lists and presets must be in the same directory.
- The default location for presets is in `GenEC/presets`. However, custom locations can be used through the `--presets-directory` / `-d` command.

### YAML Structure

Preset files follow this structure:

```yaml
preset_name:
  cluster_filter: '\n'                      # Character(s) to split text into clusters
  text_filter_type: 'Regex'                 # Filter type: 'Regex', 'Regex-list', 'Positional'
  text_filter: 'ERROR: (.+)'                # Filter configuration (varies by type)
  should_slice_clusters: false              # Enable/disable cluster range selection
  src_start_cluster_text: ''                # Source slice start marker (optional)
  src_end_cluster_text: ''                  # Source slice end marker (optional)
  ref_start_cluster_text: ''                # Reference slice start marker (optional)
  ref_end_cluster_text: ''                  # Reference slice end marker (optional)
```

### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cluster_filter` | string | Yes | Character(s) used to split text into processable chunks |
| `text_filter_type` | string | Yes | Filter method: `'Regex'`, `'Regex-list'`, `'Positional'` |
| `text_filter` | varies | Yes | Filter specification (pattern for regex, object for positional) |
| `should_slice_clusters` | boolean | No | Whether to process only a subset of clusters (default: false) |
| `src_start_cluster_text` | string | No | (slicing) Text marker to start processing in source file |
| `src_end_cluster_text` | string | No | (slicing) Text marker to end processing in source file |
| `ref_start_cluster_text` | string | No | (slicing) Text marker to start processing in reference file |
| `ref_end_cluster_text` | string | No | (slicing) Text marker to end processing in reference file |

### Filter Type Examples

**Regex Filter:**
```yaml
error_extraction:
  cluster_filter: '\n'
  text_filter_type: 'Regex'
  text_filter: 'ERROR: (.+)'
  should_slice_clusters: false
```

**Regex-list Filter:**
```yaml
multi_pattern_filter:
  cluster_filter: '\n'
  text_filter_type: 'Regex-list'
  text_filter:
    - 'WARNING'
    - 'SensorA'
    - '([0-9]+)'
  should_slice_clusters: false
```

**Positional Filter:**
```yaml
word_position_filter:
  cluster_filter: '\n\n'
  text_filter_type: 'Positional'
  text_filter:
    separator: ' '
    line: 4
    occurrence: 5
  should_slice_clusters: false
```

### Cluster Slicing

Cluster slicing allows you to process only specific sections of files by defining text markers that indicate where processing should start, and end. This is useful when working with large files where you only need data from specific sections.

**Configuration:**
```yaml
sliced_preset:
  cluster_filter: '\n'
  text_filter_type: 'Regex'
  text_filter: 'ERROR: (.+)'
  should_slice_clusters: true
  src_start_cluster_text: '=== LOG START ==='
  src_end_cluster_text: '=== LOG END ==='
  ref_start_cluster_text: '--- BASELINE BEGIN ---'
  ref_end_cluster_text: '--- BASELINE END ---'
```

**Slicing Parameters:**
- `should_slice_clusters`: Must be `true` to enable slicing
- `src_start_cluster_text`: Text marker to start processing in source file
- `src_end_cluster_text`: Text marker to end processing in source file
- `ref_start_cluster_text`: Text marker to start processing in reference file
- `ref_end_cluster_text`: Text marker to end processing in reference file

**Behavior:**
- Empty start marker means begin from first cluster
- Empty end marker means continue to last cluster
- Markers use substring matching within clusters
- Slice ranges include both start and end marker clusters

### Preset Inheritance

Create reusable configuration templates using YAML anchors to share common settings across multiple presets. This reduces duplication and makes configuration maintenance easier.

**Basic Inheritance:**
```yaml
# Define base configuration template
base_log_config: &base_settings
  cluster_filter: '\n'
  should_slice_clusters: false
  src_start_cluster_text: ''
  src_end_cluster_text: ''
  ref_start_cluster_text: ''
  ref_end_cluster_text: ''

# Presets inheriting base configuration
error_preset:
  <<: *base_settings
  text_filter_type: 'Regex'
  text_filter: 'ERROR: (.+)'

warning_preset:
  <<: *base_settings
  text_filter_type: 'Regex'
  text_filter: 'WARNING: (.+)'
```

**Advanced Inheritance with Overrides:**
```yaml
base_config: &base
  cluster_filter: '\n'
  should_slice_clusters: false

# Inherit base and override specific settings
sliced_preset:
  <<: *base
  text_filter_type: 'Regex'
  text_filter: 'INFO: (.+)'
  should_slice_clusters: true
  src_start_cluster_text: '=== SECTION START ==='
  src_end_cluster_text: '=== SECTION END ==='
```

**Inheritance Syntax:**
- `&anchor_name`: Define reusable configuration block
- `<<: *anchor_name`: Inherit all settings from anchor
- Override specific values by listing them after the inheritance line


### Example Preset File
```yaml
# log_analysis.yaml
base_log_config: &base_log
  cluster_filter: '\n'
  should_slice_clusters: false
  src_start_cluster_text: ''
  src_end_cluster_text: ''
  ref_start_cluster_text: ''
  ref_end_cluster_text: ''

error_analysis:
  <<: *base_log
  text_filter_type: 'Regex'
  text_filter: 'ERROR: (.+)'

warning_analysis:
  <<: *base_log
  text_filter_type: 'Regex'
  text_filter: 'WARNING: (.+)'

sensor_data:
  <<: *base_log
  text_filter_type: 'Regex-list'
  text_filter:
    - 'SENSOR'
    - 'Temperature'
    - '([0-9]+\.?[0-9]*)'

extract_numbers:
  cluster_filter: '\n\n'
  text_filter_type: 'Regex'
  text_filter: '[0-9]+'
  should_slice_clusters: false
```
