# Basic Workflow

**[← Back to Documentation Overview](../overview.md)**

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

> **Prerequisites**: Ensure GenEC is properly installed → [Setup and Installation](../setup.md)

## Context

The Basic Workflow is GenEC's interactive mode that guides users through configuration setup via command-line prompts. Unlike the preset workflows where configuration is defined in YAML files, the Basic Workflow walks you through each configuration decision step-by-step, making it ideal for learning GenEC's capabilities and experimenting with different settings.

When you run the Basic Workflow, GenEC will ask you a series of questions about how you want to extract data from your files. You'll choose what type of text filter to use (regex patterns, positional extraction, or multi-stage filtering), define how your text should be divided into processable chunks, and specify the exact patterns or positions for data extraction. The workflow validates your inputs in real-time, providing helpful error messages and allowing you to retry if something doesn't work as expected.

### When to use
- **First-time users**
- **Experimental analysis**
- **One-off tasks**
- **Preset creation**

When using the same parameters repeatedly in the basic workflow, considering creating a [preset](preset.md) instead.

## How to use

### CLI Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `--source` / `-s` | string | Yes | Path to the source file for data extraction |
| `--reference` / `-r` | string | No | Path to reference file for comparison (enables comparison mode) |
| `--output-directory` / `-o` | string | No | Directory to save output files (must be used with `--output-types`) |
| `--output-types` / `-t` | list | No | List of output file types: `csv`, `json`, `txt`, `yaml` (multiple allowed) |
| `--only-show-differences` | flag | No | When comparing source and reference, only show elements with non-zero differences |

**Basic syntax:**
```bash
uv run python GenEC/main.py basic --source <source_file> [--reference <reference_file>]
```

**With custom output control:**
```bash
uv run python GenEC/main.py basic -s <source_file> -r <reference_file> -o <output_dir> -t json csv txt
```

**Extract-only mode:**
```bash
uv run python GenEC/main.py basic --source logs/application.log
```

**Extract-and-compare mode:**
```bash
uv run python GenEC/main.py basic --source logs/app_current.log --reference logs/app_previous.log
```

**Filter comparison output to show only differences:**
```bash
uv run python GenEC/main.py basic --source logs/app_current.log --reference logs/app_previous.log --only-show-differences
```

**With custom output directory and formats:**
```bash
uv run python GenEC/main.py basic -s logs/app.log -r logs/baseline.log -o /path/to/results -t json csv txt yaml
```

### Configuration Parameters
The Basic Workflow prompts for all configuration parameters interactively. No YAML configuration file is required, but the following parameters will be requested:

| Configuration | Options | Description |
|---------------|---------|-------------|
| **Filter Type** | Regex, Regex-list, Positional | Text extraction method |
| **Cluster Filter** | Any string | How to divide text into processable clusters |
| **Text Filter** | Varies by filter type | Pattern or position specification for data extraction |
| **Slice Clusters** | yes/no | Whether to limit processing to specific text clusters |
| **Save Configuration** | yes/no | Option to save settings as preset for future use |
