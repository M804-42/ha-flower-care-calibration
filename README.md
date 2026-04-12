# Flower Care Calibration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration to calibrate MI Flora / Flower Care (HHCCJCY01) plant sensors against a reference meter. Creates corrected sensor entities using linear regression from your own measurements.

## Why?

MI Flora / Flower Care sensors are known to report inaccurate values — especially illuminance, which can be off by a factor of 2 or more. This affects the accuracy of DLI (Daily Light Integral) calculations used by plant monitoring integrations like [homeassistant-plant](https://github.com/Olen/homeassistant-plant).

This integration lets you calibrate each sensor individually against a reference device and creates new corrected sensor entities that you can use instead of the raw values.

## Supported Devices

- HHCCJCY01 / HHCCJCY01HHCC (Flower Care)
- HHCCJCY09
- HHCCJCY10
- GCLS002

Requires the [Xiaomi BLE](https://www.home-assistant.io/integrations/xiaomi_ble/) integration.

## Installation

### Via HACS

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/M804-42/ha-flower-care-calibration` as type **Integration**
3. Install **Flower Care Calibration**
4. Restart Home Assistant

### Manual

1. Copy the `flower_care_calibration` folder to your `custom_components` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Flower Care Calibration**
3. Select your sensor from the list
4. Enter calibration measurements for each sensor type (illuminance, moisture, conductivity, temperature)

### How to calibrate

For each measurement type, take **2–3 measurement pairs** at different levels:

1. Place your reference meter directly next to the MI Flora sensor
2. Wait ~60 seconds for the MI sensor to update
3. Note both values: the MI sensor reading (from Home Assistant) and the reference meter reading
4. Repeat at 2–3 different levels (e.g. low light, daylight, daylight + grow light)

Leave all fields empty for a sensor type to skip calibration (factor 1.0, offset 0 will be used).

### Tips for illuminance calibration

- Calibrate at **night using artificial light only** — sunlight varies too much
- Use 3 levels spread across your plant's typical light range (e.g. ~200 / ~800 / ~3000 lx)
- A dedicated lux meter gives much better results than a smartphone app
- Avoid the extreme low-light range (< 10 lx) as MI sensors are highly non-linear there

## How it works

For each calibrated sensor type, the integration creates a new Home Assistant sensor entity that applies a linear correction:

```
corrected = factor × raw + offset
```

The factor and offset are calculated via **linear regression** from your measurement pairs. With a single pair, only the factor is used (offset = 0). With 2 or more pairs, both factor and offset are fitted.

The calibrated sensor entity shows the correction formula and source entity in its attributes.

## Recalibration

To update calibration values: **Settings → Devices & Services → Flower Care Calibration → Configure**

Existing measurement points are pre-filled. Leave fields empty to keep the current calibration for that sensor type.

## Calibrated sensor entities

After setup, new sensor entities are created for each calibrated type, e.g.:

| Entity | Description |
|--------|-------------|
| `sensor.plant_sensor_xxxx_illuminance_calibrated` | Corrected illuminance (lx) |
| `sensor.plant_sensor_xxxx_moisture_calibrated` | Corrected moisture (%) |
| `sensor.plant_sensor_xxxx_conductivity_calibrated` | Corrected conductivity (µS/cm) |
| `sensor.plant_sensor_xxxx_temperature_calibrated` | Corrected temperature (°C) |

Use these entities in your plant configuration instead of the raw sensor values.

## License

MIT
