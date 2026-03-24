"""Constants for the LK Systems integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfVolume,
)

DOMAIN = "lksystems"
INTEGRATION_NAME = "LK Systems"
ATTRIBUTION = "Data provided by LK Systems API"
MANUFACTURER = "LK Systems"

C_NEXT_UPDATE_TIME = "next_update"
C_UPDATE_TIME = "last_update"

CUBIC_SECURE_MODEL = "Cubic Secure"
CUBIC_DETECTOR_MODEL = "Cubic Detector"
CUBIC_SECURE_VALVE_CLOSED = "closed"
CUBIC_SECURE_LEAK_NO_LEAK = "noLeak"

CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 5


LK_CUBICSECURE_SENSORS: dict[str, SensorEntityDescription] = {
    "volumetotalday": SensorEntityDescription(
        key="volumeTotalDay",
        name="Total Volume Day",
        icon="mdi:water",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL,
        translation_key="volume_total_day_sensor",
    ),
    "volumetotal": SensorEntityDescription(
        key="volumeTotal",
        name="Total Volume",
        icon="mdi:water",
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL,
        translation_key="volume_total_sensor",
    ),
    "tempWaterAverage": SensorEntityDescription(
        key="tempWaterAverage",
        name="Average Water Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="temp_water_average_sensor",
    ),
    "tempWaterMin": SensorEntityDescription(
        key="tempWaterMin",
        name="Min Water Temperature",
        icon="mdi:thermometer-minus",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="temp_water_min_sensor",
    ),
    "tempWaterMax": SensorEntityDescription(
        key="tempWaterMax",
        name="Max Water Temperature",
        icon="mdi:thermometer-plus",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="temp_water_max_sensor",
    ),
    "waterPressure": SensorEntityDescription(
        key="waterPressure",
        name="Water Pressure",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.PRESSURE,
        # API returns values in units of 0.1 bar (e.g. 35 → 3.5 bar).
        # native_value divides by 10 before returning.
        native_unit_of_measurement=UnitOfPressure.BAR,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="water_pressure_sensor",
    ),
    "ambientTemp": SensorEntityDescription(
        key="tempAmbient",
        name="Ambient Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="temp_ambient_sensor",
    ),
    "rssi": SensorEntityDescription(
        key="currentRssi",
        name="Signal Strength",
        icon="mdi:wifi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="signal_strength_sensor",
    ),
    "lastStatus": SensorEntityDescription(
        key="lastStatus",
        name="Last Status",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="last_status_sensor",
    ),
    "cacheUpdated": SensorEntityDescription(
        key="cacheUpdated",
        name="Cache Updated",
        icon="mdi:clock-sync-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="cache_updated_sensor",
    ),
    "leak.meanFlow": SensorEntityDescription(
        key="leak.meanFlow",
        name="Leak Mean Flow",
        icon="mdi:waves-arrow-right",
        native_unit_of_measurement="L/h",
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="leak_mean_flow_sensor",
    ),
    "leak.dateStartedAt": SensorEntityDescription(
        key="leak.dateStartedAt",
        name="Leak Started At",
        icon="mdi:calendar-start",
        device_class=SensorDeviceClass.TIMESTAMP,
        translation_key="leak_date_started_at_sensor",
    ),
    "leak.dateUpdatedAt": SensorEntityDescription(
        key="leak.dateUpdatedAt",
        name="Leak Updated At",
        icon="mdi:calendar-sync",
        device_class=SensorDeviceClass.TIMESTAMP,
        translation_key="leak_date_updated_at_sensor",
    ),
    "leak.acknowledged": SensorEntityDescription(
        key="leak.acknowledged",
        name="Leak Acknowledged",
        icon="mdi:check-circle-outline",
        translation_key="leak_acknowledged_sensor",
    ),
}

LK_CUBIC_DETECTOR_SENSORS: dict[str, SensorEntityDescription] = {
    "temperature": SensorEntityDescription(
        key="tempAmbient",
        name="Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="temp_ambient_sensor",
    ),
    "humidity": SensorEntityDescription(
        key="currentHumidity",
        name="Humidity",
        icon="mdi:water-percent",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        translation_key="humidity_sensor",
    ),
    "battery": SensorEntityDescription(
        key="currentBattery",
        name="Battery",
        icon="mdi:battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="battery_sensor",
    ),
    "rssi": SensorEntityDescription(
        key="rssi",
        name="Signal Strength",
        icon="mdi:wifi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="signal_strength_sensor",
    ),
    "lastStatus": SensorEntityDescription(
        key="lastStatus",
        name="Last Status",
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="last_status_sensor",
    ),
}

LK_CUBICSECURE_CONFIG_SENSORS: dict[str, SensorEntityDescription] = {
    "firmwareVersion": SensorEntityDescription(
        key="firmwareVersion",
        name="Firmware Version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="firmware_version_sensor",
    ),
    "hardwareVersion": SensorEntityDescription(
        key="hardwareVersion",
        name="Hardware Version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        translation_key="hardware_version_sensor",
    ),
}
