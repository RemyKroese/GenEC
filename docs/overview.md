# Documentation Overview

<div align="center">
  <img src="assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

## Overview

GenEC (Generic Extraction & Comparison) is a powerful data extraction and comparison tool with three workflows and flexible text filtering capabilities. This documentation provides comprehensive guides for all features and use cases.

## Quick Start

- **Setup** → [Setup and Installation](setup.md)
- **New to GenEC?** → [Basic Workflow](workflows/basic.md)
- **Want automation?** → [Preset Workflow](workflows/preset.md)
- **Need batch processing?** → [Preset-list Workflow](workflows/preset-list.md)

## Technical Reference

### Setup
Essential information for using GenEC:

- **[Setup and Installation](setup.md)** - Environment setup and dependency management

### Workflows
How to use GenEC's three main execution modes:

- **[Basic Workflow](workflows/basic.md)** - Interactive configuration and execution
- **[Preset Workflow](workflows/preset.md)** - YAML-based automated workflows
- **[Preset-List Workflow](workflows/preset-list.md)** - Batch processing multiple presets

### Text Filters
Understanding GenEC's data extraction capabilities:

- **[Regex Filter](filters/regex.md)** - Pattern-based text extraction
- **[Regex-list Filter](filters/regex-list.md)** - Sequential multi-pattern filtering
- **[Positional Filter](filters/positional.md)** - Position-based text extraction

## Configuration
Setup and customization options:

- **[Preset Configuration](configuration/preset.md)** - Creating and managing YAML preset files
- **[Preset-List Configuration](configuration/preset-list.md)** - Batch processing with preset references
- **[Output Formats](configuration/output-formats.md)** - JSON, TXT, CSV, YAML output options

# Feature Matrix

| Feature                | Basic | Preset | Preset-list |
|-----------------------:|:-----:|:------:|:-----------:|
| **Interactive Setup**  | ✅    | ❌    | ❌          |
| **All Filter Types**   | ✅    | ✅    | ✅          |
| **Comparison Mode**    | ✅    | ✅    | ✅          |
| **Automation**         | ❌    | ✅    | ✅          |
| **YAML Configuration** | ❌    | ✅    | ✅          |
| **Batch Processing**   | ❌    | ❌    | ✅          |

# Support

- **Codebase** - [Github Repository](https://github.com/RemyKroese/GenEC)
- **Issues** - [GitHub Issues](https://github.com/RemyKroese/GenEC/issues)
- **Discussions** - [GitHub Discussions](https://github.com/RemyKroese/GenEC/discussions)
- **License** - [Apache 2.0](../LICENSE)
