# Flower Care Calibration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20this%20project-FF5E5B?logo=ko-fi)](https://ko-fi.com/m80442)

> **Note:** This is a hobby project maintained in my spare time. Issues and PRs are welcome, but response times may vary.
>
> **Hinweis:** Dies ist ein Hobbyprojekt, das ich in meiner Freizeit pflege. Issues und PRs sind willkommen, aber ich kann nicht garantieren, dass ich zeitnah antworte.

---

## English

### What is this?

A Home Assistant custom integration to calibrate MI Flora / Flower Care (HHCCJCY01) plant sensors against a reference meter. Creates corrected sensor entities using linear regression from your own measurements.

### Why?

MI Flora / Flower Care sensors are known to report inaccurate values — especially illuminance, which can be off by a factor of 2 or more. This affects the accuracy of DLI (Daily Light Integral) calculations used by plant monitoring integrations like [homeassistant-plant](https://github.com/Olen/homeassistant-plant).

This integration lets you calibrate each sensor individually against a reference device and creates new corrected sensor entities that you can use instead of the raw values.

### Supported Devices

- HHCCJCY01 / HHCCJCY01HHCC (Flower Care)
- HHCCJCY09
- HHCCJCY10
- GCLS002

Requires the [Xiaomi BLE](https://www.home-assistant.io/integrations/xiaomi_ble/) integration.

### Installation

**Via HACS**

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/M804-42/ha-flower-care-calibration` as type **Integration**
3. Install **Flower Care Calibration**
4. Restart Home Assistant

**Manual**

1. Copy the `flower_care_calibration` folder to your `custom_components` directory
2. Restart Home Assistant

### Setup

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

**Tips for illuminance calibration**

- Calibrate at **night using artificial light only** — sunlight varies too much between measurements
- Choose 3 points **spread across your plant's typical operating range** (e.g. ~500 / ~2000 / ~8000 lx at the reference meter)
- Make sure the raw MI sensor values are also well spread — if two points give nearly identical raw values, the calibration will be inaccurate
- **Avoid near-darkness measurements** (< 50 lx reference) — the MI sensor is highly non-linear at very low light and these points distort the calibration for the relevant range
- Wait **at least 60 seconds** after changing the light level before noting the MI sensor value
- Wait **10–15 minutes** after switching on LED lamps — LEDs drop slightly in output as they warm up
- A dedicated lux meter gives much better results than a smartphone app
- With 3 measurement points, the integration automatically uses **piecewise linear calibration** (two separate correction curves below and above the middle point) for improved accuracy

### How it works

For each calibrated sensor type, the integration creates a new Home Assistant sensor entity that applies a linear correction:

```
corrected = factor × raw + offset
```

The factor and offset are calculated via **linear regression** from your measurement pairs. With a single pair, only the factor is used (offset = 0). With 2 or more pairs, both factor and offset are fitted.

### Recalibration

Go to **Settings → Devices & Services → Flower Care Calibration → Configure**

Existing measurement points are pre-filled. Leave fields empty to keep the current calibration for that sensor type.

### Calibrated sensor entities

After setup, new sensor entities are created for each calibrated type:

| Entity | Description |
|--------|-------------|
| `sensor.<device>_illuminance_calibrated` | Corrected illuminance (lx) |
| `sensor.<device>_moisture_calibrated` | Corrected moisture (%) |
| `sensor.<device>_conductivity_calibrated` | Corrected conductivity (µS/cm) |
| `sensor.<device>_temperature_calibrated` | Corrected temperature (°C) |

Use these entities in your plant configuration instead of the raw sensor values.

---

## Deutsch

### Was ist das?

Eine Home Assistant Custom Integration zur Kalibrierung von MI Flora / Flower Care (HHCCJCY01) Pflanzensensoren anhand eines Referenzgeräts. Die Integration erstellt korrigierte Sensor-Entitäten mittels linearer Regression aus deinen eigenen Messungen.

### Warum?

MI Flora / Flower Care Sensoren sind für ihre ungenauen Messwerte bekannt — besonders die Beleuchtungsstärke kann um Faktor 2 oder mehr abweichen. Das beeinträchtigt die Genauigkeit der DLI-Berechnung (Daily Light Integral), die von Pflanzenpflege-Integrationen wie [homeassistant-plant](https://github.com/Olen/homeassistant-plant) genutzt wird.

Diese Integration ermöglicht die individuelle Kalibrierung jedes Sensors gegen ein Referenzgerät und erstellt neue korrigierte Sensor-Entitäten, die anstelle der Rohwerte verwendet werden können.

### Unterstützte Geräte

- HHCCJCY01 / HHCCJCY01HHCC (Flower Care)
- HHCCJCY09
- HHCCJCY10
- GCLS002

Voraussetzung: die [Xiaomi BLE](https://www.home-assistant.io/integrations/xiaomi_ble/) Integration muss eingerichtet sein.

### Installation

**Über HACS**

1. HACS → Integrationen → ⋮ → Benutzerdefinierte Repositories
2. `https://github.com/M804-42/ha-flower-care-calibration` als Typ **Integration** hinzufügen
3. **Flower Care Calibration** installieren
4. Home Assistant neu starten

**Manuell**

1. Den Ordner `flower_care_calibration` in das Verzeichnis `custom_components` kopieren
2. Home Assistant neu starten

### Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach **Flower Care Calibration** suchen
3. Sensor aus der Liste auswählen
4. Kalibrierungsmessungen für jeden Sensortyp eingeben (Beleuchtungsstärke, Bodenfeuchte, Leitfähigkeit, Temperatur)

### Kalibrierung durchführen

Für jeden Messtyp **2–3 Wertepaare** bei unterschiedlichen Intensitäten aufnehmen:

1. Referenzgerät direkt neben den MI Flora Sensor legen
2. Ca. 60 Sekunden warten bis der MI-Sensor sich aktualisiert hat
3. Beide Werte notieren: MI-Sensor-Wert (aus Home Assistant) und Referenzgerät-Wert
4. Bei 2–3 verschiedenen Lichtstärken wiederholen (z.B. gedämpftes Licht, Tageslicht, Tageslicht + Pflanzenlicht)

Alle Felder leer lassen, um die Kalibrierung eines Sensortyps zu überspringen (Faktor 1,0 / Offset 0 wird verwendet).

**Tipps zur Beleuchtungsstärke-Kalibrierung**

- Kalibrierung **abends mit ausschließlich künstlichem Licht** — Tageslicht schwankt zwischen den Messungen zu stark
- 3 Messpunkte wählen die **gut über den typischen Betriebsbereich der Pflanze verteilt** sind (z.B. ~500 / ~2000 / ~8000 lx am Luxmeter)
- Sicherstellen dass auch die MI-Rohwerte gut verteilt sind — wenn zwei Punkte nahezu identische Rohwerte liefern, wird die Kalibrierung ungenau
- **Messungen im Dunkelbereich (< 50 lx)** vermeiden — der MI-Sensor ist dort stark nichtlinear und solche Punkte verfälschen die Kalibrierung im relevanten Bereich
- Nach jeder Lichtänderung **mindestens 60 Sekunden warten** bevor der MI-Sensor-Wert notiert wird
- Nach dem Einschalten von LED-Lampen **10–15 Minuten warten** — LEDs sinken beim Aufwärmen leicht in der Lichtleistung
- Ein dediziertes Luxmeter liefert deutlich bessere Ergebnisse als eine Smartphone-App
- Bei 3 Messpunkten verwendet die Integration automatisch eine **stückweise lineare Kalibrierung** (zwei separate Korrekturkurven unterhalb und oberhalb des mittleren Messpunkts) für höhere Genauigkeit

### Funktionsweise

Für jeden kalibrierten Sensortyp erstellt die Integration eine neue Sensor-Entität, die eine lineare Korrektur anwendet:

```
korrigiert = Faktor × Rohwert + Offset
```

Faktor und Offset werden per **linearer Regression** aus den Wertepaaren berechnet. Bei einem einzelnen Wertepaar wird nur der Faktor verwendet (Offset = 0). Ab zwei Wertepaaren werden beide Werte angepasst.

### Neu kalibrieren

**Einstellungen → Geräte & Dienste → Flower Care Calibration → Konfigurieren**

Bestehende Messpunkte werden vorausgefüllt. Felder leer lassen um die bestehende Kalibrierung beizubehalten.

### Kalibrierte Sensor-Entitäten

Nach der Einrichtung werden neue Sensor-Entitäten erstellt:

| Entität | Beschreibung |
|---------|--------------|
| `sensor.<gerät>_illuminance_calibrated` | Korrigierte Beleuchtungsstärke (lx) |
| `sensor.<gerät>_moisture_calibrated` | Korrigierte Bodenfeuchte (%) |
| `sensor.<gerät>_conductivity_calibrated` | Korrigierte Leitfähigkeit (µS/cm) |
| `sensor.<gerät>_temperature_calibrated` | Korrigierte Temperatur (°C) |

Diese Entitäten in der Pflanzenkonfiguration anstelle der Rohwerte verwenden.

---

## Support / Unterstützung

If this integration is useful to you, consider buying me a coffee! ☕
Wenn dir diese Integration hilft, freue ich mich über einen Kaffee! ☕

[![Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/m80442)

## License / Lizenz

MIT © 2026 M804-42
