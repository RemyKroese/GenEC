# Regex Filter

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

### What is it
The Regex Filter uses **regular expressions** to extract data from text based on pattern matching. It's the most flexible filter type, capable of handling complex patterns and extracting specific parts of matching text using capture groups.

### How does it work
1. **Pattern matching**: Applies a regex pattern to each text cluster
2. **Capture group extraction**: Extracts data from the first capture group `(...)` in the pattern
3. **Line-by-line processing**: Each cluster is processed independently
4. **Match validation**: Only clusters matching the pattern produce extracted data

**Implementation details to be aware of:**
- Uses Python's `re` module with compiled patterns for performance
- Extracts only the **first capture group** - use `(.+)` to capture desired text
- Empty capture groups result in empty extracted data (not skipped)
- Pattern compilation errors are caught and reported with helpful messages

### When to use
- **Structured log parsing** with consistent patterns
- **Configuration file extraction** with key-value patterns
- **Error message parsing** with variable content
- **Data validation** requiring pattern matching

## How to use

### CLI Parameters
When using Basic Workflow:
1. Select "Regex" as filter type
2. Enter regex pattern when prompted

### Configuration Parameters
In YAML preset files:
```yaml
text_filter_type: "Regex"
text_filter: "ERROR: (.+)"
```

**Pattern Guidelines:**
- Use `(.+)` to capture any text
- Use `(\d+)` to capture numbers only
- Use `([A-Za-z]+)` to capture letters only
- Use `(.*?)` for non-greedy matching

## Example

### Input
```bash
# Source data
2024-01-15 ERROR: Database connection failed
2024-01-15 INFO: Application started
2024-01-15 ERROR: User authentication failed
2024-01-15 WARN: Cache miss detected

# Regex pattern
ERROR: (.+)
```

### Output
```json
[
  {
    "file_name": "application.log",
    "line_number": 1,
    "line_content": "2024-01-15 ERROR: Database connection failed",
    "extracted_data": "Database connection failed"
  },
  {
    "file_name": "application.log",
    "line_number": 3,
    "line_content": "2024-01-15 ERROR: User authentication failed",
    "extracted_data": "User authentication failed"
  }
]
```

**→ [Complete Regex Filter Demo](../demos/filter-comparison-demo.md#regex-filter)**
