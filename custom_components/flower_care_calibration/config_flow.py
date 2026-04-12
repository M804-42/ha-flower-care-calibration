"""Config flow for Flower Care Calibration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr, entity_registry as er

from datetime import datetime

from .const import (
    CONF_CALIBRATED_AT,
    CONF_DEVICE_ID,
    CONF_FACTOR,
    CONF_FACTOR2,
    CONF_OFFSET,
    CONF_OFFSET2,
    CONF_POINTS,
    CONF_SENSORS,
    CONF_SOURCE_ENTITY,
    CONF_THRESHOLD,
    DOMAIN,
    SENSOR_TYPES,
    SUPPORTED_MODELS,
)

_LOGGER = logging.getLogger(__name__)


def calculate_calibration(points: list[tuple[float, float]]) -> tuple[float, float]:
    """Calculate factor and offset from measurement point pairs.

    Returns (factor, offset) for: corrected = factor * raw + offset
    """
    valid = [(x, y) for x, y in points if x is not None and y is not None and x > 0]

    if not valid:
        return 1.0, 0.0

    if len(valid) == 1:
        x, y = valid[0]
        return round(y / x, 4), 0.0

    n = len(valid)
    sum_x = sum(p[0] for p in valid)
    sum_y = sum(p[1] for p in valid)
    sum_xy = sum(p[0] * p[1] for p in valid)
    sum_x2 = sum(p[0] ** 2 for p in valid)

    denom = n * sum_x2 - sum_x ** 2
    if denom == 0:
        return round(sum_y / sum_x, 4), 0.0

    factor = (n * sum_xy - sum_x * sum_y) / denom
    offset = (sum_y - factor * sum_x) / n

    return round(factor, 4), round(offset, 4)


def calculate_piecewise_calibration(
    points: list[tuple[float, float]],
) -> tuple[float | None, float, float, float, float]:
    """Calculate piecewise linear calibration from measurement points.

    With 3 points: splits into two segments at the middle point.
    With < 3 points: falls back to single linear segment.

    Returns (threshold, factor1, offset1, factor2, offset2).
    threshold=None means single segment (factor2/offset2 unused).
    """
    valid = sorted(
        [(x, y) for x, y in points if x is not None and y is not None and x > 0],
        key=lambda p: p[0],
    )

    if len(valid) < 3:
        f, o = calculate_calibration(valid)
        return None, f, o, f, o

    # Middle point is the threshold
    x1, y1 = valid[0]
    x2, y2 = valid[1]
    x3, y3 = valid[2]
    threshold = x2

    # Segment 1: points 0 → 1
    if x2 != x1:
        f1 = (y2 - y1) / (x2 - x1)
        o1 = y1 - f1 * x1
    else:
        f1, o1 = 1.0, 0.0

    # Segment 2: points 1 → 2
    if x3 != x2:
        f2 = (y3 - y2) / (x3 - x2)
        o2 = y2 - f2 * x2
    else:
        f2, o2 = 1.0, 0.0

    return round(threshold, 4), round(f1, 4), round(o1, 4), round(f2, 4), round(o2, 4)


def find_sensor_entities(hass, device_id: str) -> dict[str, str]:
    """Find source sensor entity_ids for a device, keyed by sensor type."""
    entity_reg = er.async_get(hass)
    found: dict[str, str] = {}

    for sensor_type, info in SENSOR_TYPES.items():
        device_class = info["device_class"]
        unit = info["unit"]
        for entity in entity_reg.entities.values():
            if entity.device_id != device_id:
                continue
            if entity.platform != "xiaomi_ble":
                continue
            # Match by device_class or unit
            if device_class and entity.original_device_class == device_class:
                found[sensor_type] = entity.entity_id
                break
            if unit in (entity.unit_of_measurement or ""):
                found[sensor_type] = entity.entity_id
                break

    return found


def get_supported_devices(hass) -> dict[str, str]:
    """Return dict of device_id -> device_name for supported HHCC devices."""
    device_reg = dr.async_get(hass)
    devices = {}

    for device in device_reg.devices.values():
        model = device.model or ""
        model_clean = model.replace(" ", "").upper()
        for supported in SUPPORTED_MODELS:
            if model_clean and (supported in model_clean or model_clean in supported):
                name = device.name_by_user or device.name or device.id
                devices[device.id] = f"{name} ({model})"
                break

    return devices


class FlowerCareCalibrationConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Flower Care Calibration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._device_id: str = ""
        self._device_name: str = ""
        self._source_entities: dict[str, str] = {}
        self._calibration_data: dict[str, dict] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Step 1: Select device."""
        devices = get_supported_devices(self.hass)

        if not devices:
            return self.async_abort(reason="no_devices_found")

        errors = {}

        if user_input is not None:
            self._device_id = user_input[CONF_DEVICE_ID]
            self._device_name = devices[self._device_id].split(" (")[0]
            self._source_entities = find_sensor_entities(self.hass, self._device_id)

            # Check for duplicate entry
            await self.async_set_unique_id(self._device_id)
            self._abort_if_unique_id_configured()

            return await self.async_step_calibrate_illuminance()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_ID): vol.In(devices),
            }),
            description_placeholders={
                "count": str(len(devices))
            },
            errors=errors,
        )

    async def async_step_calibrate_illuminance(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Step 2: Illuminance calibration."""
        return await self._calibration_step(
            step_id="calibrate_illuminance",
            sensor_type="illuminance",
            next_step="calibrate_moisture",
            user_input=user_input,
        )

    async def async_step_calibrate_moisture(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Step 3: Moisture calibration."""
        return await self._calibration_step(
            step_id="calibrate_moisture",
            sensor_type="moisture",
            next_step="calibrate_conductivity",
            user_input=user_input,
        )

    async def async_step_calibrate_conductivity(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Step 4: Conductivity calibration."""
        return await self._calibration_step(
            step_id="calibrate_conductivity",
            sensor_type="conductivity",
            next_step="calibrate_temperature",
            user_input=user_input,
        )

    async def async_step_calibrate_temperature(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Step 5: Temperature calibration."""
        return await self._calibration_step(
            step_id="calibrate_temperature",
            sensor_type="temperature",
            next_step=None,
            user_input=user_input,
        )

    async def _calibration_step(
        self,
        step_id: str,
        sensor_type: str,
        next_step: str | None,
        user_input: dict[str, Any] | None,
    ) -> dict:
        """Generic calibration step for any sensor type."""
        source_entity = self._source_entities.get(sensor_type)

        # Auto-skip if sensor type not available on this device
        if not source_entity:
            if next_step:
                return await getattr(self, f"async_step_{next_step}")()
            return self._create_entry()

        if user_input is not None:
            points = self._extract_points(user_input)
            threshold, f1, o1, f2, o2 = calculate_piecewise_calibration(points)
            self._calibration_data[sensor_type] = {
                CONF_SOURCE_ENTITY: source_entity,
                CONF_POINTS: points,
                CONF_FACTOR: f1,
                CONF_OFFSET: o1,
                CONF_FACTOR2: f2,
                CONF_OFFSET2: o2,
                CONF_THRESHOLD: threshold,
                CONF_CALIBRATED_AT: datetime.now().isoformat(timespec="seconds"),
            }

            if next_step:
                return await getattr(self, f"async_step_{next_step}")()

            return self._create_entry()

        # Get current sensor value for reference
        current_value = "—"
        if source_entity:
            state = self.hass.states.get(source_entity)
            if state and state.state not in ("unknown", "unavailable"):
                unit = SENSOR_TYPES[sensor_type]["unit"]
                current_value = f"{state.state} {unit}"

        schema = self._build_calibration_schema(sensor_type)

        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
            description_placeholders={
                "sensor_name": SENSOR_TYPES[sensor_type]["name_de"],
                "current_value": current_value,
                "entity_id": source_entity or "nicht gefunden",
            },
        )

    def _build_calibration_schema(self, sensor_type: str) -> vol.Schema:
        """Build schema for 3 calibration point pairs."""
        return vol.Schema({
            vol.Optional("p1_raw"): vol.Coerce(float),
            vol.Optional("p1_ref"): vol.Coerce(float),
            vol.Optional("p2_raw"): vol.Coerce(float),
            vol.Optional("p2_ref"): vol.Coerce(float),
            vol.Optional("p3_raw"): vol.Coerce(float),
            vol.Optional("p3_ref"): vol.Coerce(float),
        })

    def _extract_points(self, user_input: dict) -> list[tuple[float, float]]:
        """Extract valid measurement pairs from user input."""
        points = []
        for i in range(1, 4):
            raw = user_input.get(f"p{i}_raw")
            ref = user_input.get(f"p{i}_ref")
            if raw is not None and ref is not None:
                points.append((float(raw), float(ref)))
        return points

    def _create_entry(self) -> dict:
        """Create the config entry."""
        return self.async_create_entry(
            title=self._device_name,
            data={
                CONF_DEVICE_ID: self._device_id,
                CONF_SENSORS: self._calibration_data,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return options flow."""
        return FlowerCareCalibrationOptionsFlow(config_entry)


class FlowerCareCalibrationOptionsFlow(OptionsFlow):
    """Options flow — recalibrate existing sensors."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize."""
        self._config_entry = config_entry
        self._device_id = config_entry.data[CONF_DEVICE_ID]
        self._source_entities = {
            stype: sdata.get(CONF_SOURCE_ENTITY, "")
            for stype, sdata in config_entry.data.get(CONF_SENSORS, {}).items()
        }
        # Refresh source entities in case new sensors appeared
        self._calibration_data: dict[str, dict] = dict(
            config_entry.data.get(CONF_SENSORS, {})
        )

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        """Start options flow."""
        # Refresh source entity discovery
        self._source_entities = find_sensor_entities(
            self.hass, self._device_id
        )
        return await self.async_step_calibrate_illuminance()

    async def async_step_calibrate_illuminance(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        return await self._calibration_step("calibrate_illuminance", "illuminance", "calibrate_moisture", user_input)

    async def async_step_calibrate_moisture(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        return await self._calibration_step("calibrate_moisture", "moisture", "calibrate_conductivity", user_input)

    async def async_step_calibrate_conductivity(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        return await self._calibration_step("calibrate_conductivity", "conductivity", "calibrate_temperature", user_input)

    async def async_step_calibrate_temperature(
        self, user_input: dict[str, Any] | None = None
    ) -> dict:
        return await self._calibration_step("calibrate_temperature", "temperature", None, user_input)

    async def _calibration_step(
        self,
        step_id: str,
        sensor_type: str,
        next_step: str | None,
        user_input: dict[str, Any] | None,
    ) -> dict:
        """Generic calibration step."""
        source_entity = self._source_entities.get(sensor_type)

        # Auto-skip if sensor type not available on this device
        if not source_entity:
            if next_step:
                return await getattr(self, f"async_step_{next_step}")()
            return self.async_create_entry(
                title="",
                data={CONF_SENSORS: self._calibration_data},
            )

        if user_input is not None:
            points = self._extract_points(user_input)
            threshold, f1, o1, f2, o2 = calculate_piecewise_calibration(points)
            if points or sensor_type in self._calibration_data:
                existing = self._calibration_data.get(sensor_type, {})
                self._calibration_data[sensor_type] = {
                    CONF_SOURCE_ENTITY: source_entity,
                    CONF_POINTS: points,
                    CONF_FACTOR: f1,
                    CONF_OFFSET: o1,
                    CONF_FACTOR2: f2,
                    CONF_OFFSET2: o2,
                    CONF_THRESHOLD: threshold,
                    CONF_CALIBRATED_AT: datetime.now().isoformat(timespec="seconds") if points else existing.get(CONF_CALIBRATED_AT, ""),
                }

            if next_step:
                return await getattr(self, f"async_step_{next_step}")()

            return self.async_create_entry(
                title="",
                data={CONF_SENSORS: self._calibration_data},
            )

        current_value = "—"
        if source_entity:
            state = self.hass.states.get(source_entity)
            if state and state.state not in ("unknown", "unavailable"):
                unit = SENSOR_TYPES[sensor_type]["unit"]
                current_value = f"{state.state} {unit}"

        # Pre-fill existing calibration points
        existing = self._calibration_data.get(sensor_type, {})
        existing_points = existing.get(CONF_POINTS, [])
        defaults = {}
        for i, (raw, ref) in enumerate(existing_points[:3], 1):
            defaults[f"p{i}_raw"] = raw
            defaults[f"p{i}_ref"] = ref

        schema = vol.Schema({
            vol.Optional("p1_raw", default=defaults.get("p1_raw")): vol.Any(None, vol.Coerce(float)),
            vol.Optional("p1_ref", default=defaults.get("p1_ref")): vol.Any(None, vol.Coerce(float)),
            vol.Optional("p2_raw", default=defaults.get("p2_raw")): vol.Any(None, vol.Coerce(float)),
            vol.Optional("p2_ref", default=defaults.get("p2_ref")): vol.Any(None, vol.Coerce(float)),
            vol.Optional("p3_raw", default=defaults.get("p3_raw")): vol.Any(None, vol.Coerce(float)),
            vol.Optional("p3_ref", default=defaults.get("p3_ref")): vol.Any(None, vol.Coerce(float)),
        })

        existing_factor = existing.get(CONF_FACTOR, 1.0)
        existing_offset = existing.get(CONF_OFFSET, 0.0)
        existing_threshold = existing.get(CONF_THRESHOLD)
        existing_factor2 = existing.get(CONF_FACTOR2, existing_factor)
        existing_offset2 = existing.get(CONF_OFFSET2, existing_offset)

        if existing_threshold:
            correction = (
                f"≤{existing_threshold}: ×{existing_factor}+{existing_offset} | "
                f">{existing_threshold}: ×{existing_factor2}+{existing_offset2}"
            )
        else:
            correction = f"×{existing_factor}+{existing_offset}"

        return self.async_show_form(
            step_id=step_id,
            data_schema=schema,
            description_placeholders={
                "sensor_name": SENSOR_TYPES[sensor_type]["name_de"],
                "current_value": current_value,
                "entity_id": source_entity or "nicht gefunden",
                "current_correction": correction,
            },
        )

    def _extract_points(self, user_input: dict) -> list[tuple[float, float]]:
        points = []
        for i in range(1, 4):
            raw = user_input.get(f"p{i}_raw")
            ref = user_input.get(f"p{i}_ref")
            if raw is not None and ref is not None:
                points.append((float(raw), float(ref)))
        return points
