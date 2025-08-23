# Positional Filter

**[← Back to Documentation Overview](../overview.md)**

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

The Positional filter extracts data based on character position and occurrence counting within text clusters. It's designed for structured data formats like CSV, TSV, or fixed-width files where data location is predictable.

When you use the Positional Filter, GenEC locates data by position rather than pattern matching. You specify which line within each cluster to examine, what character to use for splitting that line into elements, and which element to extract. For example, in a CSV file, you might extract the third column from the second line of each cluster by using a comma separator, line 2, and occurrence 3.

This approach is particularly useful when your data has a consistent structure but varies in content, making regex patterns difficult to maintain. Instead of trying to match varying text patterns, you can simply point to where the data should be located within the structure. This filter requires less technical knowledge to use than other filter tpyes within GenEC.

**Note:** by default, the clusters are split by paragraph (\n\n), but it's possible create clusters on lines instead (\n). So, each cluster is only 1 line. **When doing this, the line number to extract on, should always be 1**. Otherwise no data will be found.

### When to use
- **Simple data extraction**

The [regex filter type](regex.md) is a more reliable method of extracting data. However, the positional filter type requires less in-depth knowledge of the data and is easier to use if the data positions are always in the same spot within the files.

## How to use

### CLI Parameters
When using Basic Workflow:
1. Select "Positional" as filter type
2. Enter cluster filter (Enter for paragraphs '\n\n')
3. Enter separator character (Enter for whitespace)
4. Enter line number within cluster
5. Enter occurrence number on that line

### Configuration Parameters
In YAML preset files:
```yaml
text_filter_type: "Positional"
text_filter:
  separator: ","
  line: 1
  occurrence: 3
```
