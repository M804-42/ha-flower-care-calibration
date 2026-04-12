"""Constants for Flower Care Calibration."""

DOMAIN = "flower_care_calibration"

CONF_DEVICE_ID = "device_id"
CONF_SENSORS = "sensors"
CONF_FACTOR = "factor"
CONF_OFFSET = "offset"
CONF_POINTS = "points"
CONF_SOURCE_ENTITY = "source_entity_id"

# Supported MI Flora / HHCC device models
SUPPORTED_MODELS = [
    "HHCCJCY01",
    "HHCCJCY01HHCC",
    "HHCCJCY10",
    "GCLS002",
    "HHCCJCY09",
]

# Sensor types with their device_class for discovery
SENSOR_TYPES = {
    "illuminance": {
        "name": "Illuminance",
        "name_de": "Beleuchtungsstärke",
        "unit": "lx",
        "device_class": "illuminance",
        "icon": "mdi:sun-wireless",
        "min_value": 0,
        "max_value": 200000,
    },
    "moisture": {
        "name": "Moisture",
        "name_de": "Bodenfeuchte",
        "unit": "%",
        "device_class": "moisture",
        "icon": "mdi:water-percent",
        "min_value": 0,
        "max_value": 100,
    },
    "conductivity": {
        "name": "Conductivity",
        "name_de": "Leitfähigkeit",
        "unit": "µS/cm",
        "device_class": None,
        "icon": "mdi:lightning-bolt-circle",
        "min_value": 0,
        "max_value": 10000,
    },
    "temperature": {
        "name": "Temperature",
        "name_de": "Temperatur",
        "unit": "°C",
        "device_class": "temperature",
        "icon": "mdi:thermometer",
        "min_value": -10,
        "max_value": 60,
    },
}
