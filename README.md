# GenEC: Generic Extraction & Comparison Tool

![1.0.0 Release Progress](https://img.shields.io/badge/progress-88%25-brightgreen)
[![Build](https://github.com/RemyKroese/GenEC/actions/workflows/python-ci.yml/badge.svg)](https://github.com/RemyKroese/GenEC/actions)
[![Last Commit](https://img.shields.io/github/last-commit/RemyKroese/GenEC)](https://github.com/RemyKroese/GenEC/commits)
![Contributors](https://img.shields.io/github/contributors/RemyKroese/GenEC)
[![License: Apache 2.0](https://img.shields.io/github/license/RemyKroese/GenEC)](./LICENSE)
[![Top Language](https://img.shields.io/github/languages/top/RemyKroese/GenEC)](https://github.com/RemyKroese/GenEC)
<!-- [![codecov](https://codecov.io/gh/RemyKroese/GenEC/branch/main/graph/badge.svg)](https://codecov.io/gh/RemyKroese/GenEC) -->



### 1.0.0 release progress

`████████████████████████████████████████████████████████████████████████████████████████            `


&#x20;

## Overview

GenEC (Generic Extraction & Comparison) is a Python-based tool for extracting structured data from files or folders.
It offers a flexible, one-size-fits-all extraction framework that you can tailor precisely using configuration parameters.

With presets and preset lists, you can easily repeat your extraction methods on single files or entire directories.
Beyond extraction, GenEC can also compare the extracted data against reference files or folders to highlight differences.

Designed for users of all technical levels, GenEC supports both manual workflows and automated pipelines,
making data analysis straightforward and accessible.

## Installation

GenEC requires **Python 3.9 or higher**

### Using uv (recommended)

For execution:
```bash
pip install uv
uv sync
uv run <command>
```

For developing:
```bash
uv sync --group dev   # include dev packages
uv sync --group dist  # include distribution packages
```

---


## Usage

GenEC supports three workflow commands, which utilize different CLI arguments:
- **basic** — define extraction and comparison directly at runtime.
- **preset** — use a single YAML preset for configuration.
- **preset-list** — run bulk analysis with multiple presets listed in a YAML file.


### Common Arguments

| Argument             | Short | Required | Description                                                        |
|----------------------|-------|----------|--------------------------------------------------------------------|
| `--source`*           | `-s`  | Yes      | Path to the source for data extraction.                      |
| `--reference`        | `-r`  | No       | Path to the reference for comparison. |
| `--output-directory`* | `-o`  | No       | Directory to save output files. |
| `--output-types`*     | `-t`  | No       | List of output file types to generate. Choices: `csv`, `json`, `txt`, `yaml`. Note that multiple can be selected. |

*`--source` and `--reference` arguments accept **file paths** for the basic and preset workflows, and **directory paths** when using `preset-list` workflow.
**`--output-directory` and `--output-types` must be used together.

### Workflow-Specific Arguments

| Workflow       | Argument              | Short | Required | Description                                               |
|----------------|-----------------------|-------|----------|-----------------------------------------------------------|
| **basic**      | (none additional)     |       |          | Extraction strategy defined at runtime.     |
| **preset**     | `--preset`            | `-p`  | Yes      | Extraction strategy determined through a preset.     |
|                | `--presets-directory` | `-x`  | No       | Directory containing preset YAML files (default: `GenEC/presets/`). |
| **preset-list**| `--preset-list`       | `-l`  | Yes      | YAML file listing multiple presets for batch processing.  |
|                | `--presets-directory` | `-x`  | No       | Directory containing preset YAML files (default: `GenEC/presets/`). |
|                | `--target-variables`  |       | No       | Key-value pairs (`key=value`) to dynamically substitute variables in preset target paths. Can be specified multiple times.|

### Example Commands

#### Basic workflow

```bash
python -m GenEC.main basic -s <source_file> [options]

python -m GenEC.main basic -s <source_file> -r <reference_file> -o <output_directory> -t txt csv json yaml
```

#### Preset workflow

```bash
python -m GenEC.main preset -s <source_file> -r <reference_file> -p <file_name_without_extension/preset_name> -x <preset_directory> [options]
```

#### Preset-list workflow

```bash
python -m GenEC.main preset-list -s <source_directory> -r <reference_directory> -l <file_name_without_extension> -x <preset_directory> [options]

python -m GenEC.main preset-list -s <source_directory> -r <reference_directory> -l <file_name_without_extension> -x <preset_directory> -v myvar1=value1 myvar2=value2
```

---

## Configuration

GenEC allows customization through YAML configuration files. A sample preset  may look like:

```yaml
preset_a:
  cluster_filter: '\n'
  text_filter_type: 'Regex'
  text_filter: '\| ([A-Za-z]+) \|'
  should_slice_clusters: false
  src_start_cluster_text: ''
  src_end_cluster_text: ''
  ref_start_cluster_text: ''
  ref_end_cluster_text: ''
```

Note that GenEC can use grouping within the Regex filter type `()` to construct more complex output data.

Modify these parameters according to your extraction and comparison needs. Please see the [Sample preset
YAML](GenEC/presets/sample_preset.yaml) for more information. Creation of more in-depth documentation on these yaml configurations
files is still in progress.

---

## Demos

### Preset-list demo
Comparison of multiple files using the `preset-list` workflow with regex configurations:

![preset-list demo](docs/demos/preset-list_demo_1/output.png)

---

## Testing

Run the test suite from the root directory. Requires dev packages to be installed

### Full test
```bash
uv run pytest
```

### Coverage
```bash
uv run pytest --cov=. --cov-branch
```


### Subtests
```bash
uv run pytest -m system    # Runs system-level tests

uv run pytest -m unit      # Runs unit tests
```

### Repeat tests
```bash
uv run pytest --count 10
```

## License
Copyright [2025] [Remy Kroese]

Licensed under the Apache License, Version 2.0 See the [LICENSE file](LICENSE) for details.
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
