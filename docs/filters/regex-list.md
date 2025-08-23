# Regex-list Filter

**[← Back to Documentation Overview](../overview.md)**

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

The Regex-list filter applies multiple regex patterns sequentially to progressively filter and refine text clusters before extracting data. It's designed for complex hierarchical data where you need to first filter to relevant sections, then extract specific information. The first patterns act as filters (clusters must contain these patterns), while the final pattern performs the actual data extraction from the remaining clusters.

When you use the Regex-list filter, GenEC applies your patterns in sequence, using the first patterns as filters and the last pattern for data extraction. For example, you might first filter for lines containing "WARNING", then filter those results for lines containing "SensorA", and finally extract sensor values with a pattern like `([0-9]+)`. This progressive refinement allows you to precisely target data in complex files where simple patterns would be too broad or capture unwanted information.

For each entry in the regex-list, clusters that do not match the regex pattern will be removed from further data extraction. So, each pattern must match within the same text cluster for data to be extracted. This means if you're processing line-by-line (the default), all your patterns must match elements within individual lines, not across multiple lines. The last regex pattern in the list behaves exactly the same as how the [regex filter type](regex.md) behaves.

### When to use
- **(Complex) pattern-based data extraction**
- **Conditional data extraction**
- **Low-performance regex patterns**

This filter type excels at simplifying regex patterns, whilst also improving performance. However, for very simple regex patterns, the normal [regex filter type](regex.md) can be used instead.

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
