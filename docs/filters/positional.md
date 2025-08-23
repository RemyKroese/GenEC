# Positional Filter

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

### What is it
The Positional Filter extracts data based on **character position and occurrence counting** within text clusters. It's designed for structured data formats like CSV, TSV, or fixed-width files where data location is predictable.

### How does it work
1. **Cluster selection**: Identifies the specified line number within each cluster
2. **Character splitting**: Splits the line using the specified separator character(s)
3. **Occurrence selection**: Selects the Nth element from the split results
4. **Data extraction**: Extracts the selected element as the result

**Implementation details to be aware of:**
- Line numbers are **1-indexed** (first line = 1)
- Occurrence numbers are **1-indexed** (first element after split = 1)
- Splits line by separator and selects the occurrence-th element (not text after it)
- Empty separators default to whitespace (single space character)
- Clusters with insufficient lines or split elements are skipped

### When to use
- **CSV/TSV file processing** with known column positions
- **Fixed-width data extraction** with consistent formatting
- **Structured log parsing** where position is more reliable than patterns
- **Simple data extraction** without complex pattern matching needs

## How to use

### CLI Parameters
When using Basic Workflow:
1. Select "Positional" as filter type
2. Enter separator character (Enter for whitespace)
3. Enter line number within cluster
4. Enter occurrence number on that line

### Configuration Parameters
In YAML preset files:
```yaml
text_filter_type: "Positional"
text_filter:
  separator: ","
  line: 1
  occurrence: 3
```

**Configuration Fields:**
- `separator` - Character(s) to split on (empty string = whitespace)
- `line` - Line number within cluster (1-indexed)
- `occurrence` - Occurrence number on the line (1-indexed)

## Example

### Input
```bash
# Source data (CSV format)
Date,Level,Component,Message
2024-01-15,ERROR,Database,Connection failed
2024-01-15,INFO,Application,Started successfully
2024-01-15,ERROR,Authentication,User login failed

# Positional filter configuration
separator: ","
line: 1
occurrence: 4
```

### Output
```json
[
  {
    "file_name": "application.csv",
    "line_number": 2,
    "line_content": "2024-01-15,ERROR,Database,Connection failed",
    "extracted_data": "Connection failed"
  },
  {
    "file_name": "application.csv",
    "line_number": 3,
    "line_content": "2024-01-15,INFO,Application,Started successfully",
    "extracted_data": "Started successfully"
  },
  {
    "file_name": "application.csv",
    "line_number": 4,
    "line_content": "2024-01-15,ERROR,Authentication,User login failed",
    "extracted_data": "User login failed"
  }
]
```

**→ [Complete Positional Filter Demo](../demos/filter-comparison-demo.md#positional-filter)**
