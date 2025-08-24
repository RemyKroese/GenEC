# Preset-List Configuration

**[← Back to Documentation Overview](../overview.md)**

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

## Context

Preset-list configuration files enable batch processing by referencing multiple existing preset configurations and applying them to different target files. Unlike individual presets that contain extraction settings, preset-list files organize and orchestrate existing presets for comprehensive analysis workflows.

When you create a preset-list, you're building a collection of analysis tasks that run sequentially. Each entry references an existing preset configuration and specifies which file in your source directory should be processed with that preset. This allows you to apply different extraction strategies to different files in a single execution.

Preset-lists support variable substitution, making them dynamic and reusable across different datasets. You can use variables in target paths and substitute values at runtime using command-line parameters.

Preset-list files reference existing presets. To create the preset configurations themselves, see: [Preset Configuration documentation](preset.md)

## How to use

### YAML Structure

Preset-list files use a reference model structure:

```yaml
group_name_1:
  - preset: 'preset_file/preset_name'       # Reference to existing preset
    target: 'filename.txt'                  # Target file for this preset
  - preset: 'another_file/preset_name'      # Another preset reference
    target: 'another_file.txt'              # Different target file

group_name_2:
  - preset: 'preset_file/preset_name'       # Same preset, different target
    target: '{variable}_file.txt'           # Variable substitution supported
  - preset: 'preset_file/other_preset'      # Different preset
    target: 'static_file.txt'               # Static target file
```

### Configuration Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `preset` | string | Yes | Reference to existing preset in format `'<file_without_extension>/preset_name'` |
| `target` | string | Yes | Target filename within source directory |

### Group Organization

Groups organize related preset executions and create output directory structure:

```yaml
error_analysis:                             # Group name becomes output subdirectory
  - preset: 'log_presets/error_extraction'
    target: 'app.log'
  - preset: 'log_presets/critical_errors'
    target: 'system.log'

performance_analysis:                       # Second group creates separate subdirectory
  - preset: 'perf_presets/response_times'
    target: 'performance.log'
  - preset: 'perf_presets/memory_usage'
    target: 'memory.log'
```

### Output Organization

Preset-lists create structured output directories based on group names:

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
```

### Variable Substitution

Variable substitution enables dynamic target paths in preset-list configurations, making them reusable across different datasets and environments. Variables are specified in target paths and resolved at runtime through command-line parameters.

**Variable Syntax:**
```yaml
analysis_group:
  - preset: 'error_configs/basic_errors'
    target: '{environment}_{date}_application.log'
  - preset: 'perf_configs/response_times'
    target: '{environment}_performance.log'
  - preset: 'security_configs/audit_trail'
    target: '{project}_{environment}_security.log'
```

**Runtime Usage:**
```bash
# Provide variable values via --target-variables
genec preset-list --preset-list analysis_group --source logs/ \
  --target-variables environment=production date=2024-01-15 project=webapp
```

**Variable Features:**
- Use `{variable_name}` syntax in target paths
- Multiple variables supported in single target path
- Variables resolved during execution before file matching
- Each preset-list entry can use different variable combinations


### Example Preset-List File
```yaml
log_monitoring:
  - preset: 'monitoring_presets/error_tracking'
    target: '{env}_application.log'
  - preset: 'monitoring_presets/warning_analysis'
    target: '{env}_warnings.log'
  - preset: 'monitoring_presets/performance_metrics'
    target: '{env}_performance.log'

security_audit:
  - preset: 'security_presets/login_attempts'
    target: 'auth.log'
  - preset: 'security_presets/access_violations'
    target: 'security.log'
  - preset: 'security_presets/privilege_escalation'
    target: 'admin.log'

data_validation:
  - preset: 'validation_presets/data_integrity'
    target: '{dataset}_validation.txt'
  - preset: 'validation_presets/format_compliance'
    target: '{dataset}_format.txt'
```

For more examples, see the [Example preset list file](../../GenEC/presets/example_preset-list.yaml)
