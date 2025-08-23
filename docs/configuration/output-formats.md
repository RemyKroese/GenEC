# Output Formats

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

### What is it
GenEC supports multiple output formats to accommodate different analysis workflows and integration requirements. Each format provides the same extracted data with different structural representations optimized for specific use cases.

### How does it work
Output format generation operates through a centralized `OutputManager` system:

1. **Data collection**: Extracted data is collected into standardized `Entry` objects containing file metadata and extracted content
2. **Format selection**: Users specify desired output types via the `--output-types` CLI parameter
3. **Writer dispatch**: The OutputManager uses a registry pattern to route data to appropriate format writers
4. **File generation**: Each writer creates formatted output files in the specified output directory
5. **Consistent naming**: All formats use identical base filenames with format-specific extensions

**Implementation details to be aware of:**
- Uses writer registry pattern with `@register_writer()` decorators for extensibility
- All formats contain identical data with different structural representations
- Output files are organized by source file name in subdirectories
- Comparison results (when reference files are provided) are included in all formats
- File naming follows the pattern: `result.{extension}` within source-named directories

### When to use
Different output formats serve specific purposes:
- **JSON**: Machine-readable integration, API consumption, programmatic analysis
- **YAML**: Human-readable configuration-style output, documentation generation
- **CSV**: Spreadsheet analysis, data science workflows, tabular processing
- **TXT**: Quick visual inspection, simple text processing, debugging

## How to use

### CLI Parameters

| Parameter | Short | Required | Description |
|-----------|-------|----------|-------------|
| `--output-directory` | `-o` | Optional | Directory path where output files will be created |
| `--output-types` | `-t` | Optional | List of output formats to generate |

**Validation rules:**
- Both `--output-directory` and `--output-types` must be provided together or omitted together
- At least one output type must be specified when using output directory
- Output directory will be created if it doesn't exist

**Basic syntax:**
```bash
uv run python GenEC/main.py [workflow] --source <file> --output-directory <path> --output-types <formats>
# Available formats: csv, json, txt, yaml
```

### Configuration Options

**Single format:**
```bash
uv run python GenEC/main.py basic --source data.txt -o results/ -t json
```

**Multiple formats:**
```bash
uv run python GenEC/main.py basic --source data.txt -o results/ -t json csv yaml txt
```

**Extract-and-compare with output:**
```bash
uv run python GenEC/main.py preset --preset my_preset --source data.txt --reference ref.txt -o analysis/ -t json csv
```

## Example

### Input
```bash
uv run python GenEC/main.py basic --source application.log --output-directory results/ --output-types json csv txt
# Interactive configuration follows...
```

### Output Directory Structure
```
results/
└── application/
    ├── result.json
    ├── result.csv
    └── result.txt
```

### JSON Output Format
```json
[
  {
    "file_name": "application.log",
    "line_number": 1,
    "line_content": "2024-01-15 ERROR Database Connection failed",
    "extracted_data": "Connection failed"
  },
  {
    "file_name": "application.log",
    "line_number": 3,
    "line_content": "2024-01-15 INFO Application Started successfully",
    "extracted_data": "Started successfully"
  }
]
```

### CSV Output Format
```csv
file_name,line_number,line_content,extracted_data
application.log,1,"2024-01-15 ERROR Database Connection failed","Connection failed"
application.log,3,"2024-01-15 INFO Application Started successfully","Started successfully"
```

### TXT Output Format
```
Results for: application.log

1: 2024-01-15 ERROR Database Connection failed
   → Connection failed

3: 2024-01-15 INFO Application Started successfully
   → Started successfully

Total extractions: 2
```

### YAML Output Format
```yaml
- file_name: application.log
  line_number: 1
  line_content: "2024-01-15 ERROR Database Connection failed"
  extracted_data: "Connection failed"
- file_name: application.log
  line_number: 3
  line_content: "2024-01-15 INFO Application Started successfully"
  extracted_data: "Started successfully"
```

**→ [Complete Output Demo](../demos/quick_start/)**
