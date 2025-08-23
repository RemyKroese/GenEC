# Reference Comparison

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

### What is it
Reference comparison is GenEC's capability to extract data from two files (source and reference) and identify differences between the extracted datasets. This feature enables validation, change detection, and comparative analysis workflows.

### How does it work
Reference comparison operates through a two-stage extraction and comparison process:

1. **Dual extraction**: GenEC applies the same configuration to both source and reference files independently
2. **Data normalization**: Extracted data from both files is collected into comparable formats
3. **Difference detection**: The `Comparer` class identifies additions, deletions, and common elements
4. **Result integration**: Comparison results are merged with extraction data in all output formats
5. **Comprehensive reporting**: Output includes both individual extractions and comparative analysis

**Implementation details to be aware of:**
- Uses the same text filter configuration for both source and reference files
- Slice configuration (start/end cluster text) can be different for source vs reference files
- Comparison operates on extracted text values, not raw file content
- Results include both extraction data and comparison metadata
- All output formats contain integrated comparison information

### When to use
Reference comparison is optimal for:
- **Validation workflows**: Verifying that data extraction produces expected results
- **Change detection**: Identifying what has been added, removed, or modified between versions
- **Quality assurance**: Comparing actual vs expected data extraction outputs
- **Regression testing**: Ensuring data processing changes don't affect extraction results
- **Data synchronization**: Finding differences between datasets from different sources

## How to use

### CLI Parameters

| Parameter | Short | Required | Description |
|-----------|-------|----------|-------------|
| `--reference` | `-r` | Optional | Reference file to extract data from and compare against source |

**Usage patterns:**
- **Extract-only mode**: Omit `--reference` parameter for standard data extraction
- **Extract-and-compare mode**: Include `--reference` parameter for comparative analysis

### Configuration Parameters

For preset-based workflows, reference file behavior can be configured with slice parameters:

```yaml
# Preset configuration example
preset_name:
  cluster_filter: '\n'
  text_filter_type: 'Regex'
  text_filter: '([A-Z]+)'
  should_slice_clusters: true
  src_start_cluster_text: 'START_MARKER'     # Source file slice start
  src_end_cluster_text: 'END_MARKER'         # Source file slice end
  ref_start_cluster_text: 'BEGIN_SECTION'    # Reference file slice start
  ref_end_cluster_text: 'FINISH_SECTION'     # Reference file slice end
```

**Slice configuration options:**
- `src_start_cluster_text` - Text marking where to start extraction in source file
- `src_end_cluster_text` - Text marking where to end extraction in source file
- `ref_start_cluster_text` - Text marking where to start extraction in reference file
- `ref_end_cluster_text` - Text marking where to end extraction in reference file
- Empty values mean extract from beginning/end of file

## Example

### Input
```bash
uv run python GenEC/main.py basic --source current_data.log --reference baseline_data.log
# Interactive configuration follows...
```

### Source File: current_data.log
```
2024-01-15 INFO Application started
2024-01-15 ERROR Database connection failed
2024-01-15 INFO Service initialized
2024-01-15 WARN Cache miss detected
```

### Reference File: baseline_data.log
```
2024-01-14 INFO Application started
2024-01-14 INFO Database connected successfully
2024-01-14 INFO Service initialized
```

### Output with Comparison Results
```json
{
  "extractions": {
    "source": [
      {
        "file_name": "current_data.log",
        "line_number": 1,
        "line_content": "2024-01-15 INFO Application started",
        "extracted_data": "started"
      },
      {
        "file_name": "current_data.log",
        "line_number": 2,
        "line_content": "2024-01-15 ERROR Database connection failed",
        "extracted_data": "failed"
      },
      {
        "file_name": "current_data.log",
        "line_number": 3,
        "line_content": "2024-01-15 INFO Service initialized",
        "extracted_data": "initialized"
      },
      {
        "file_name": "current_data.log",
        "line_number": 4,
        "line_content": "2024-01-15 WARN Cache miss detected",
        "extracted_data": "detected"
      }
    ],
    "reference": [
      {
        "file_name": "baseline_data.log",
        "line_number": 1,
        "line_content": "2024-01-14 INFO Application started",
        "extracted_data": "started"
      },
      {
        "file_name": "baseline_data.log",
        "line_number": 2,
        "line_content": "2024-01-14 INFO Database connected successfully",
        "extracted_data": "successfully"
      },
      {
        "file_name": "baseline_data.log",
        "line_number": 3,
        "line_content": "2024-01-14 INFO Service initialized",
        "extracted_data": "initialized"
      }
    ]
  },
  "comparison": {
    "in_source_only": ["failed", "detected"],
    "in_reference_only": ["successfully"],
    "in_both": ["started", "initialized"]
  }
}
```

**→ [Complete Comparison Demo](../demos/quick_start/)**
