# LK Systems for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)

Cloud-polling integration for LK Systems smart home devices using the MyLK API.

Supports:
- [LK CubicSecure](https://www.lksystems.se/sv/produkter/teknisk-armatur/vattenfelsutrustning/vattenfelsbrytare/lk-cubicsecure-77792594) — water protection unit
- [LK CubicDetector](https://www.lksystems.se/sv/produkter/teknisk-armatur/vattenfelsutrustning/) — wireless water/freeze sensor
- [LK Arc](https://www.lksystems.se/sv/produktsystem/golvvarme/lk-rumsreglering-arc/) — wireless thermostats and sensors

## Features

### LK CubicSecure

#### Sensors

| Entity | Description |
|--------|-------------|
| Water Pressure | Current pressure (bar) |
| Ambient Temperature | Temperature around the unit (°C) |
| Average Water Temperature | Average water temperature (°C) |
| Min / Max Water Temperature | Min and max water temperature (°C) |
| Total Volume Day | Water consumed today (L) |
| Total Volume | Cumulative water volume (L) |
| Leak Mean Flow | Flow rate during active leak event (L/h) |
| Leak Started At / Updated At | Timestamps for the current leak event |
| Leak Acknowledged | Whether the active leak has been acknowledged |
| Signal Strength | RSSI (dBm) — diagnostic |
| Last Status / Cache Updated | Device timestamps — diagnostic |
| Firmware / Hardware Version | Versions — diagnostic |

#### Binary sensor

| Entity | Triggers on |
|--------|-------------|
| Water Leak | Any active leak state (`noLeak` = off) |

#### Valve

| Entity | Description |
|--------|-------------|
| Valve | Open or close the main water shutoff |

#### Services

| Service | Description |
|---------|-------------|
| `lksystems.pause_leak_detection` | Pause leak alerts for N seconds |
| `lksystems.set_pressure_test_schedule` | Schedule the daily pressure test |
| `lksystems.set_thresholds` | Configure medium/large leak and pressure thresholds |

### LK CubicDetector

Battery-powered wireless sensor. Multiple detectors per household are supported.

| Entity | Description |
|--------|-------------|
| Temperature | Ambient temperature (°C) |
| Humidity | Relative humidity (%) |
| Battery | Battery level (%) |
| Signal Strength | RSSI (dBm) — diagnostic |
| Last Status | Last device timestamp — diagnostic |
| Water Leak | `on` when water or freeze is detected |

### LK Arc

| Entity | Description |
|--------|-------------|
| Thermostat | Temperature control, 0.5 °C steps, 5–30 °C range (arc-tune devices) |
| Temperature | Current room temperature (°C) |
| Humidity | Relative humidity (%) |
| Battery | Battery level (%) |
| Signal Strength | RSSI (dBm) |

> **Note:** Early development — use at own risk, breaking changes may occur.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=angoyd&repository=ha-lksystems&category=integration)

### Manual

1. Copy the `custom_components/lksystems` folder into your HA `custom_components` directory.
2. Restart Home Assistant.

## Setup

Go to **Settings → Devices & Services → Integrations**, click **+ ADD INTEGRATION**, and search for **LK Systems**. Enter your MyLK account credentials.
