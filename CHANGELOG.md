# Changelog

All notable changes to this project will be documented in this file.

---

## [0.2.0] - 2026-04-12

### Added
- **Piecewise linear calibration**: with 3 measurement points, two separate correction curves are calculated (below and above the middle point) for significantly improved accuracy across a wide light range
- Calibration date stored in sensor attributes (`calibrated_at`)
- Calibration steps are automatically skipped if a sensor type is not available on the device

### Changed
- Calibrated values are now clamped to the valid physical range (e.g. moisture 0–100%)
- Options flow now shows the full current correction formula including piecewise info
- Improved README with detailed calibration guidance and tips

### Fixed
- Device list no longer shows devices without a model (e.g. Sun, HACS, Withings)
- Virtual calibration device now shows correct name instead of "Unknown device"

---

## [0.1.0] - 2026-04-12

### Added
- Initial release
- Config flow wizard for device selection and calibration of illuminance, moisture, conductivity and temperature
- Linear regression calibration from up to 3 measurement pairs
- Calibrated sensor entities linked to original Flower Care device
- Options flow for recalibration with pre-filled existing values
- German and English UI translations
- Supports HHCCJCY01, HHCCJCY01HHCC, HHCCJCY09, HHCCJCY10, GCLS002
