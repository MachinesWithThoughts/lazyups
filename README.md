# lazyups

LazyUPS is a command-line utility for collecting and summarising information from multiple [Network UPS Tools](https://networkupstools.org/) (NUT) endpoints. Point LazyUPS at one or more UPS daemons, and it will consolidate key telemetry such as model, status, charge, runtime estimates, and alerts into a concise report suitable for dashboards or operational runbooks.

## Features

- Connect to one or more NUT servers over TCP (default port 3493)
- Query multiple UPS devices exposed by each server
- Extract a curated subset of metrics (status, charge, runtime, voltage, load, temperature, alarms)
- Present results as a terminal table, JSON document, or Markdown summary
- Gracefully handle connectivity errors and partial data
- Provide exit codes that reflect overall fleet health for automation hooks

## Quick start

> **Note:** This project is under active development. Interfaces may change.

### Requirements

- Python 3.12+
- Access to one or more NUT servers (for example, `upsd`) reachable over the network

### Installation

```bash
pip install -e .
```

### Usage

```bash
lazyups --server ups1.example.com --server ups2.example.com --format table
```

Use `--help` to review all options.

## Development

```bash
# Install dependencies
pip install -e .[dev]

# Run tests
pytest
```

## Roadmap

- Configuration file support (YAML / TOML)
- Prometheus metrics exporter
- Web dashboard with historical trends
- Automated discovery via SRV records and/or environment variables

## License

MIT License. See [LICENSE](LICENSE).
