# GenEC: Generic Extraction & Comparison Tool

![1.0.0 Release Progress](https://img.shields.io/badge/progress-75%25-brightgreen)
[![Build](https://github.com/RemyKroese/GenEC/actions/workflows/python-package.yml/badge.svg)](https://github.com/RemyKroese/GenEC/actions)
[![Last Commit](https://img.shields.io/github/last-commit/RemyKroese/GenEC)](https://github.com/RemyKroese/GenEC/commits)
![Contributors](https://img.shields.io/github/contributors/RemyKroese/GenEC)
[![License: Apache 2.0](https://img.shields.io/github/license/RemyKroese/GenEC)](./LICENSE)
[![Top Language](https://img.shields.io/github/languages/top/RemyKroese/GenEC)](https://github.com/RemyKroese/GenEC)


### 1.0.0 release progress

`███████████████████████████████████████████████████████████████████████████                         `


&#x20;

## Overview

GenEC (Generic Extraction & Comparison) is a Python-based tool designed for extracting structured data from source and reference files, then comparing their contents based on defined rules. It allows customization through YAML-based configuration files and supports both command-line and programmatic usage.

## Installation

GenEC requires Python 3.7 or later. Install dependencies from the root directory (GenEC) using Pipenv:

```
pipenv install
```

## Usage

GenEC can be used via the command line or directly in Python scripts.

### Command-Line Interface (CLI)

Run GenEC from the command line as follows:

```
python -m GenEC.main --source <source_file> --reference <reference_file> [--preset <preset_file_name/preset_name>] [--output_dir <output_directory>]
```

**Arguments:**

- `--source` (`-s`): Path to the source file for data extraction.
- `--reference` (`-r`): Path to the reference file for comparison.
- `--preset` (`-t`): (Optional) YAML preset specifying extraction rules.
- `--output_dir` (`-o`): (Optional) Directory where the output files should be stored.

**Example:**

```
python -m GenEC.main --source /source.txt --reference reference.txt --preset sample_preset/sub_preset_A --output_dir results/
```

### Python Integration

For advanced users, GenEC can be imported into Python scripts to allow deeper customization:

```python
import GenEC.core.analyze as analyze
import GenEC.utils as utils

# Define file paths
source_file = 'source.txt'
reference_file = 'reference.txt'

# Define preset
preset = 'sample_preset/sub_preset_A'

# Read files
source, reference = utils.read_files([source_file, reference_file])

# Initialize InputManager with preset
input_manager = analyze.InputManager(preset_file)
input_manager.set_config()

# Initialize Extractor with configuration
extractor = analyze.Extractor(input_manager.config)

# Extract data
source_data = extractor.extract_from_data(source, analyze.Files.SOURCE)
reference_data = extractor.extract_from_data(reference, analyze.Files.REFERENCE)

# Compare data
comparer = analyze.Comparer(source_filtered_text, ref_filtered_text)
differences = comparer.compare()
```

## Configuration

GenEC allows customization through YAML configuration files. A sample preset  may look like:

```yaml
main_preset: &main_preset
  cluster_filter: ''
  text_filter_type: 0
  text_filter: ''
  should_slice_clusters: false
  src_start_cluster_text: ''
  src_end_cluster_text: ''
  ref_start_cluster_text: ''
  ref_end_cluster_text: ''

sub_preset_A:
  <<: *main_preset
  should_slice_clusters: true

sub_preset_B:
  <<: *main_preset
  cluster_filter: '\n'
  text_filter_type: 1
  text_filter: '[a-zA-z]{4}'
```

Modify these parameters according to your extraction and comparison needs. Please see the [Sample preset YAML](GenEC/presets/sample_preset.yaml) for more information.

## Testing

Run the test suite from the root directory using:

```
pipenv run pytest
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
This project is licensed under the MIT License.
