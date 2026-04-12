"""Calibrated sensor entities for Flower Care Calibration."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_DEVICE_ID,
    CONF_FACTOR,
    CONF_OFFSET,
    CONF_SENSORS,
    CONF_SOURCE_ENTITY,
    DOMAIN,
    SENSOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)

DEVICE_CLASS_MAP = {
    "illuminance": SensorDeviceClass.ILLUMINANCE,
    "moisture": SensorDeviceClass.MOISTURE,
    "conductivity": None,
    "temperature": SensorDeviceClass.TEMPERATURE,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up calibrated sensor entities."""
    sensors_config = entry.data.get(CONF_SENSORS, {})
    # Options override data for recalibration
    if entry.options:
        sensors_config = entry.options.get(CONF_SENSORS, sensors_config)

    device_id = entry.data[CONF_DEVICE_ID]
    entities = []

    for sensor_type, config in sensors_config.items():
        source_entity_id = config.get(CONF_SOURCE_ENTITY)
        if not source_entity_id:
            continue
        factor = config.get(CONF_FACTOR, 1.0)
        offset = config.get(CONF_OFFSET, 0.0)

        entities.append(
            CalibratedSensor(
                hass=hass,
                entry=entry,
                device_id=device_id,
                sensor_type=sensor_type,
                source_entity_id=source_entity_id,
                factor=factor,
                offset=offset,
            )
        )

    async_add_entities(entities)


class CalibratedSensor(SensorEntity):
    """A calibrated version of a Flower Care sensor."""

    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device_id: str,
        sensor_type: str,
        source_entity_id: str,
        factor: float,
        offset: float,
    ) -> None:
        """Initialize."""
        self.hass = hass
        self._entry = entry
        self._device_id = device_id
        self._sensor_type = sensor_type
        self._source_entity_id = source_entity_id
        self._factor = factor
        self._offset = offset

        type_info = SENSOR_TYPES[sensor_type]
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}_calibrated"
        self._attr_name = f"{type_info['name']} (calibrated)"
        self._attr_native_unit_of_measurement = type_info["unit"]
        self._attr_device_class = DEVICE_CLASS_MAP.get(sensor_type)
        self._attr_icon = type_info["icon"]
        self._attr_native_value = None
        self._attr_extra_state_attributes = {
            "source_entity": source_entity_id,
            "factor": factor,
            "offset": offset,
            "formula": f"value × {factor} + {offset}",
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Link to the original Flower Care device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=f"{self._entry.title} (kalibriert)",
            manufacturer="HHCC Plant Technology Co. Ltd",
            model="Flower Care (calibrated)",
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to source entity state changes."""
        self._update_from_source()

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._source_entity_id],
                self._handle_source_state_change,
            )
        )

    @callback
    def _handle_source_state_change(self, event) -> None:
        """Handle state change of source entity."""
        self._update_from_source()
        self.async_write_ha_state()

    def _update_from_source(self) -> None:
        """Read source entity state and apply calibration."""
        state = self.hass.states.get(self._source_entity_id)
        if state is None or state.state in ("unknown", "unavailable", None):
            self._attr_native_value = None
            return

        try:
            raw = float(state.state)
            calibrated = self._factor * raw + self._offset
            # Round reasonably
            if self._sensor_type == "illuminance":
                self._attr_native_value = round(calibrated, 0)
            elif self._sensor_type == "temperature":
                self._attr_native_value = round(calibrated, 1)
            else:
                self._attr_native_value = round(calibrated, 1)
        except (ValueError, TypeError):
            self._attr_native_value = None
