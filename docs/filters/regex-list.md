# Regex-List Filter

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)egex-list Filter

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

### What is it
The Regex-list Filter applies **multiple regex patterns sequentially** to progressively filter and refine text clusters before extracting data. It's designed for complex hierarchical data where you need to first filter to relevant sections, then extract specific information.

### How does it work
1. **Sequential filtering**: Applies N-1 patterns as filters to reduce the dataset
2. **Final extraction**: The last pattern extracts data using its first capture group
3. **Progressive refinement**: Each filter step reduces the number of clusters
4. **All-or-nothing matching**: Clusters must match ALL filter patterns to be processed

**Implementation details to be aware of:**
- Filters are applied in the order specified in the list
- First N-1 patterns act as **filters only** (no extraction)
- Only the **last pattern** extracts data using its capture group
- If any pattern fails to match a cluster, that cluster is excluded
- Each pattern is applied within individual clusters (not across clusters)

### When to use
- **Complex log analysis** requiring multi-level filtering
- **Hierarchical data extraction** from structured text
- **Conditional extraction** based on multiple criteria
- **Precision filtering** when simple regex is too broad

## How to use

### CLI Parameters
When using Basic Workflow:
1. Select "Regex-list" as filter type
2. Enter patterns one by one when prompted
3. Confirm when finished adding patterns

### Configuration Parameters
In YAML preset files:
```yaml
text_filter_type: "Regex-list"
text_filter:
  - "ERROR"
  - "database"
  - "connection (.+)"
```

**Pattern Guidelines:**
- **Filter patterns** (first N-1): Should match desired content (no capture groups needed)
- **Extraction pattern** (last): Must have exactly one capture group `(.+)`
- Order matters: most restrictive to least restrictive typically works best

## Example

### Input
```bash
# Source data
2024-01-15 ERROR: Database connection failed to server-01
2024-01-15 ERROR: User authentication failed
2024-01-15 INFO: Database query completed successfully
2024-01-15 ERROR: Database connection timeout to server-02
2024-01-15 WARN: Cache miss detected

# Regex-list patterns
1. "ERROR"           # Filter: only ERROR lines
2. "Database"        # Filter: only database-related errors
3. "connection (.+)" # Extract: connection details
```

### Output
```json
[
  {
    "file_name": "application.log",
    "line_number": 1,
    "line_content": "2024-01-15 ERROR: Database connection failed to server-01",
    "extracted_data": "failed to server-01"
  },
  {
    "file_name": "application.log",
    "line_number": 4,
    "line_content": "2024-01-15 ERROR: Database connection timeout to server-02",
    "extracted_data": "timeout to server-02"
  }
]
```

**→ [Complete Regex-list Filter Demo](../demos/filter-comparison-demo.md#regex-list-filter)**
