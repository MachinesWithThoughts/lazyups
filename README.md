# LazyUPS

LazyUPS is a Textual TUI for monitoring one or more
[Network UPS Tools (NUT)](https://networkupstools.org/) endpoints.

It lets you:
- manage NUT endpoints
- continuously monitor key UPS telemetry in a live table
- inspect full `upsc <name>@<host>` details per device
- view all discovered fields grouped by category

---

## Requirements

- Python **3.12**
- [`uv`](https://docs.astral.sh/uv/) installed and available in `PATH`
- Reachable NUT servers (`upsd`, usually on port `3493`)

---

## Install / Run

From the project root:

```bash
./run.sh
```

`run.sh` delegates directly to `uv run lazyups`.

You can also start on a specific screen:

```bash
./run.sh --start-screen monitor
./run.sh --start-screen details
./run.sh --start-screen devices
./run.sh --start-screen display-fields
```

---

## Screens

### Monitor

Live polling table across all configured endpoints/devices.

By default it shows:
- `battery.charge`
- `battery.runtime`
- `battery.voltage`
- `model`
- `input.voltage`
- `ups.beeper.status`
- `ups.load`
- `ups.status`

Rows are keyed by `DEVICENAME@HOSTNAME`.

### Details

Shows full `upsc`-style details for discovered devices:
- left pane: device selector
- right pane: full variable dump for the selected device

### Settings

Menu contains two settings sub-screens:

- `- Devices`
  - add/edit/remove endpoint host/port/name
- `- Display Fields`
  - shows **all discovered fields**, deduplicated and grouped
  - selected monitor fields are highlighted in green

---

## Configuration file

Path:

```text
~/.lazyups.config
```

Current schema:

```json
{
  "endpoints": [
    { "host": "ups1.local", "port": 3493, "name": "Rack UPS" }
  ],
  "monitor_fields": [
    "battery.charge",
    "ups.status"
  ]
}
```

Startup validates this file. If invalid, LazyUPS exits with a clear error.

---

## Validation / Tests

### Runtime import check

```bash
./run-code-validations.sh --validate-runtime
```

### Screen rendering check

```bash
./run-code-validations.sh --validate-screens
```

Or a subset:

```bash
./run-code-validations.sh --validate-screens --validation-screens settings
```

### Unit tests

```bash
uv sync --extra dev
.venv/bin/pytest -q
```

---

## Build a single executable (Linux)

```bash
./build-exe.sh --clean
```

Output binary:

```text
dist/lazyups
```

---

## Notes

- NUT backend is provided through `nut2`.
- `nut2` currently uses `telnetlib`, which emits a Python 3.12 deprecation warning for Python 3.13 removal.

---

## License

MIT License. See [LICENSE](LICENSE).
