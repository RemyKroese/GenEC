# Regex Filter

**[← Back to Documentation Overview](../overview.md)**

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

The Regex filter uses [regular expressions](https://en.wikipedia.org/wiki/Regular_expression) to extract data from text based on pattern matching. It's the most flexible filter type, capable of handling complex patterns and extracting specific parts of matching text using capture groups. It is highly recommended to construct your regex using [regex101](https://regex101.com/) and test it using the [Basic workflow](../workflows/basic.md) to ensure you have the correct regex for your goal.

When you use the Regex Filter, GenEC applies your regular expression pattern to each cluster of text, and **extracts data from the first match in the cluster**. This allows you to precisely target the information you need while ignoring surrounding text. When a match is found, each section of text within a capturing group `()` is stored. This will later be visualized again through the following syntax: `{group_1} | {group 2} | ...`. When no capturing group is used, the entire match is visualized instead.

The filter processes each text cluster independently, so your pattern only needs to match within individual clusters. This makes it perfect for line-based log files, structured data formats, or any text where you can define a clear pattern for the information you want to extract.

### When to use
- **(Simple) pattern-based data extraction**

When a regex pattern is starting to become complicated for your use case, and you notice it takes a while to get the data, the [regex-list filter type](regex-list.md) can be used instead. This filter type aims to improve performance when uses regex-based data extraction.

## How to use

### CLI Parameters
When using Basic Workflow:
1. Select "Regex" as filter type
2. Enter cluster filter (Enter for newlines '\n')
3. Enter regex pattern when prompted

### Configuration Parameters
In YAML preset files:
```yaml
text_filter_type: "Regex"
text_filter: "ERROR: (.+)"
```
