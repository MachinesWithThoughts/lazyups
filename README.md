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

## Features

- Monitor view with live polling
- Details view for full `upsc <ups>@<host>` output
- Devices management (add/edit/remove endpoints)
- Fields view to control which values appear in Monitor/Details
  - Click any field to toggle it on/off
  - Selected fields are highlighted

## Install

Build the executable:

```bash
build-exectuable.exe
```

Then install it system-wide:

```bash
sudo cp dist/lazyups /usr/local/bin
```

## Run

```bash
./run.sh
```

Start on a specific page:

```bash
./run.sh --screen monitor
./run.sh --screen details
./run.sh --screen devices
./run.sh --screen fields
```

## Configuration (`.lazyups.config`)

LazyUPS stores its settings in a JSON file named `.lazyups.config`.

Default location:

```text
~/.lazyups.config
```

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

