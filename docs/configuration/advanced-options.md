# Advanced Options

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

### What is it
Advanced options in GenEC provide fine-grained control over data extraction behavior, cluster processing, and workflow customization. These options enable power users to optimize GenEC for specific data formats, performance requirements, and complex extraction scenarios.

### How does it work
Advanced options operate through various configuration mechanisms:

1. **Cluster slicing**: Precise control over which sections of files are processed
2. **Custom separators**: Flexible text clustering for different data formats
3. **Variable substitution**: Dynamic path resolution in preset-list workflows
4. **Preset inheritance**: YAML anchor patterns for configuration reuse
5. **Performance optimization**: Settings to optimize processing for specific use cases

**Implementation details to be aware of:**
- Configuration precedence: CLI args override preset values override defaults
- Cluster slicing uses text matching, not line numbers, for robustness
- Variable substitution supports nested path structures and complex patterns
- All advanced options maintain backward compatibility with basic usage patterns

### When to use
Advanced options are optimal for:
- **Complex data formats**: Files with irregular structure or multiple sections
- **Performance optimization**: Large files requiring selective processing
- **Automation workflows**: Dynamic configuration based on runtime parameters
- **Specialized extraction**: Data sources with unique formatting requirements
- **Enterprise deployments**: Standardized configurations across multiple environments

## How to use

### Cluster Slicing Configuration

Control which sections of files are processed using start and end markers:

```yaml
# Advanced slice configuration
advanced_extraction:
  cluster_filter: '\n'
  text_filter_type: 'Regex'
  text_filter: '([0-9]{4}-[0-9]{2}-[0-9]{2})'
  should_slice_clusters: true
  src_start_cluster_text: '=== DATA START ==='
  src_end_cluster_text: '=== DATA END ==='
  ref_start_cluster_text: '--- BASELINE BEGIN ---'
  ref_end_cluster_text: '--- BASELINE FINISH ---'
```

**Cluster slicing options:**
- `should_slice_clusters`: Enable/disable cluster slicing functionality
- `src_start_cluster_text`: Text pattern marking start of extraction in source file
- `src_end_cluster_text`: Text pattern marking end of extraction in source file
- `ref_start_cluster_text`: Text pattern marking start of extraction in reference file
- `ref_end_cluster_text`: Text pattern marking end of extraction in reference file

**Slicing behavior:**
- Empty start marker = begin from first cluster
- Empty end marker = continue to last cluster
- Markers use substring matching within clusters
- Slice ranges are inclusive of start and end markers

### Custom Cluster Separators

Optimize processing for different data formats using custom separators:

```yaml
# Different separator configurations
newline_processing:
  cluster_filter: '\n'          # Line-based processing (default)

paragraph_processing:
  cluster_filter: '\n\n'        # Paragraph-based processing

record_processing:
  cluster_filter: '---'         # Custom delimiter processing

no_clustering:
  cluster_filter: ''            # Process entire file as single cluster
```

**Separator guidelines:**
- `'\n'` - Standard line-based processing for most log files
- `'\n\n'` - Paragraph-based processing for documentation or multi-line records
- Custom delimiters - For structured data with specific separators
- Empty string - Treat entire file as single cluster (useful for small files or specific patterns)

### Variable Substitution (Preset-List)

Dynamic path resolution using variable substitution in preset-list workflows:

```yaml
# preset-list configuration with variables
analysis_groups:
  - group_name: "environment_analysis"
    presets:
      - preset: 'monitoring/cpu_analysis'
        target: '${environment}/servers/${hostname}/cpu_metrics.txt'
      - preset: 'monitoring/memory_analysis'
        target: '${environment}/servers/${hostname}/memory_metrics.txt'

  - group_name: "application_logs"
    presets:
      - preset: 'logging/error_extraction'
        target: '${app_name}/logs/${date}/errors.log'
      - preset: 'logging/performance_extraction'
        target: '${app_name}/logs/${date}/performance.log'
```

**Variable syntax:**
- Use `${variable_name}` syntax for substitution
- Variables passed via `--target-variables` CLI parameter: `-v environment=prod hostname=server01`
- Supports nested directory structures and complex path patterns
- Variables can be used in any part of the target path

### Preset Inheritance Patterns

Leverage YAML anchors for configuration reuse and maintenance:

```yaml
# Base configuration template
base_config: &base_settings
  cluster_filter: '\n'
  should_slice_clusters: false
  src_start_cluster_text: ''
  src_end_cluster_text: ''
  ref_start_cluster_text: ''
  ref_end_cluster_text: ''

# Specialized configurations inheriting from base
error_extraction:
  <<: *base_settings
  text_filter_type: 'Regex'
  text_filter: 'ERROR.*: (.*)'

performance_extraction:
  <<: *base_settings
  text_filter_type: 'Positional'
  text_filter:
    separator: ','
    line: 1
    occurrence: 3

debug_extraction:
  <<: *base_settings
  text_filter_type: 'Regex-list'
  text_filter:
    - 'DEBUG'
    - 'Performance'
    - 'Time: ([0-9]+)ms'
```

### Performance Optimization Settings

Optimize GenEC performance for specific use cases:

```yaml
# Large file optimization
large_file_config:
  cluster_filter: '\n'           # Use line-based clustering for memory efficiency
  should_slice_clusters: true    # Enable slicing to limit processing scope
  src_start_cluster_text: 'START_PROCESSING'
  src_end_cluster_text: 'END_PROCESSING'

# Complex pattern optimization
complex_pattern_config:
  cluster_filter: '\n\n'         # Use larger clusters for multi-line patterns
  text_filter_type: 'Regex'
  text_filter: '(?s)START.*?([A-Z]+).*?END'  # Enable DOTALL mode for multi-line
```

**Performance guidelines:**
- Use appropriate cluster separators for your data format
- Enable cluster slicing for large files to limit processing scope
- Consider memory usage with very large cluster sizes
- Test pattern complexity against performance requirements

## Example

### Advanced Slice Configuration
```bash
# Extract data between specific markers
uv run python GenEC/main.py preset --preset advanced_slice --source large_log.txt
```

### Variable Substitution Usage
```bash
# Dynamic path resolution in preset-list
uv run python GenEC/main.py preset-list --preset-list deployment_analysis \
    --source /data/servers/ \
    -v environment=production hostname=web01 date=2024-01-15
```

### Custom Separator Processing
```bash
# Process structured data with custom delimiters
uv run python GenEC/main.py preset --preset record_parser --source structured_data.txt
```

**→ [Complete Advanced Demo](../demos/quick_start/)**
