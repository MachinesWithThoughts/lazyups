# LazyUPS

<p align="center">
  <a href="https://github.com/MachinesWithThoughts/lazyups/actions/workflows/ci.yml">
    <img src="https://img.shields.io/github/actions/workflow/status/MachinesWithThoughts/lazyups/ci.yml?style=flat-square" />
  </a>
  <a href="https://github.com/MachinesWithThoughts/lazyups/releases">
    <img src="https://img.shields.io/github/v/release/MachinesWithThoughts/lazyups?style=flat-square" />
  </a>
  <a href="https://github.com/MachinesWithThoughts/lazyups/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/MachinesWithThoughts/lazyups?style=flat-square" />
  </a>
</p>

Terminal UI for monitoring NUT (`upsc`) UPS devices.

> Compatibility note: LazyUPS currently supports Python 3.12 only (`>=3.12,<3.13`) due to upstream `nut2`/`telnetlib` compatibility on some Python 3.13+ builds.

## Features

- Monitor view with live polling
- Details view for full `upsc <ups>@<host>` output
- Devices management (add/edit/remove endpoints)
- Fields view to control which values appear in Monitor/Details
  - Click any field to toggle it on/off
  - Selected fields are highlighted

## Install

### pipx (Python 3.12 required)

```bash
pipx install --python python3.12 "git+https://github.com/MachinesWithThoughts/lazyups.git@v01.03.07"
```

### uv tool

```bash
uv tool install "git+https://github.com/MachinesWithThoughts/lazyups.git@v01.03.07"
```

## Run

```bash
lazyups
```

Start on a specific page:

```bash
lazyups --screen monitor
lazyups --screen details
lazyups --screen devices
lazyups --screen fields
```

## Configuration (`.lazyups.config`)

LazyUPS reads config from the first existing file in this order:

```text
~/.lazyups.config
/etc/lazyups.config
/usr/local/etc/lazyups.config
```

Override at runtime:

```bash
lazyups --config-file /path/to/lazyups.config
```

In **Settings**, LazyUPS shows the active config source path and whether it is writable.

It currently stores:

- `endpoints` — list of NUT hosts/ports/names from **Settings → Devices**
- `monitor_fields` — selected fields from **Settings → Fields**

Example:

```json
{
  "endpoints": [
    {
      "host": "192.168.1.20",
      "port": 3493,
      "name": "rack-nut"
    }
  ],
  "monitor_fields": [
    "battery.charge",
    "battery.runtime",
    "input.voltage",
    "ups.load",
    "ups.status"
  ]
}
```

If the file is missing, LazyUPS creates/updates it automatically when you save device or field settings.

## Screenshots

### Monitor

![Monitor](screenshots/monitor.svg)

### Details

![Details](screenshots/details.svg)

### Devices

![Devices](screenshots/devices.svg)

### Fields

![Fields](screenshots/fields.svg)

