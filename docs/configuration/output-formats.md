# Output Formats

[← Back to Documentation Overview](../overview.md)

<div align="center">
  <img src="../assets/logo/GenEC-logo-transparent.png" alt="GenEC Logo" width="200"/>
</div>

## Context

GenEC displays extraction results in the terminal by default. To save results to files, you must specify both an output directory and the desired file formats using `--output-directory` and `--output-types` parameters. The following file types are supported:
- TXT (tables similar to the ones shown in the CLI)
- JSON
- CSV
- YAML

## How to Use

### Required Parameters for File Output
Both parameters must be provided together:
- `--output-directory` (`-o`): Directory where output files will be saved
- `--output-types` (`-t`): List of file formats to generate

### Format Selection
```bash
# Terminal output only (default)
genec basic --source data.txt

# Save single format
genec basic --source data.txt --output-directory results --output-types json

# Save multiple formats
genec basic --source data.txt -o results -t json csv

# All available formats
genec basic --source data.txt -o results -t csv json txt yaml
```

## Examples

All examples show the actual structure GenEC outputs to files:

### JSON Format
```json
{
  "preset": "",
  "target": "",
  "data": {
    "ERROR": {"source": 157},
    "INFO": {"source": 1174},
    "WARNING": {"source": 322}
  }
}
```

### CSV Format
```csv
data,preset,source,target
ERROR,,157,
INFO,,1174,
WARNING,,322,
```

### TXT Format
```
┌───────────────────────────────────────────────┐
│                                  ╷            │
│                                  │  (count)   │
│   Data                           │   Source   │
│ ╶────────────────────────────────┼──────────╴ │
│   INFO                           │     1174   │
│   WARNING                        │      322   │
│   ERROR                          │      157   │
│                                  ╵            │
└───────────────────────────────────────────────┘
```

### YAML Format
```yaml
- preset: ''
  target: ''
  data:
    ERROR:
      source: 157
    INFO:
      source: 1174
    WARNING:
      source: 322
```
