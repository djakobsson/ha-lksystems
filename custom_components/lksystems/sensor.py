"""Support for LK Systems sensors."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
import homeassistant.util.dt as dt_util

from . import LKSystemCoordinator
from .const import (
    ATTRIBUTION,
    C_NEXT_UPDATE_TIME,
    C_UPDATE_TIME,
    CUBIC_DETECTOR_MODEL,
    CUBIC_SECURE_MODEL,
    DOMAIN,
    INTEGRATION_NAME,
    LK_CUBIC_DETECTOR_SENSORS,
    LK_CUBICSECURE_CONFIG_SENSORS,
    LK_CUBICSECURE_SENSORS,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LK Systems sensor based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # --- CubicSecure sensors ---
    if coordinator.data.get("cubic_machine_info"):
        zone_name = coordinator.data["cubic_machine_info"]["zone"]["zoneName"]
        _LOGGER.debug("Setting up CubicSecure sensors for %s", zone_name)
        cubic_entities: list[LKCubicSensor] = [
            LKCubicSensor(coordinator, desc)
            for desc in LK_CUBICSECURE_SENSORS.values()
        ] + [
            LKCubicSensor(coordinator, desc, data_source="configuration")
            for desc in LK_CUBICSECURE_CONFIG_SENSORS.values()
        ]
        async_add_entities(cubic_entities, True)

    # --- CubicDetector sensors ---
    for detector in coordinator.data.get("cubic_detectors", []):
        machine_info = detector.get("machine_info", {})
        if not machine_info.get("identity"):
            continue
        _LOGGER.debug(
            "Setting up CubicDetector sensors for %s",
            machine_info.get("zone", {}).get("zoneName", "unknown"),
        )
        detector_entities: list[LKCubicDetectorSensor] = [
            LKCubicDetectorSensor(coordinator, detector, desc)
            for desc in LK_CUBIC_DETECTOR_SENSORS.values()
        ]
        async_add_entities(detector_entities, True)

    # --- Arc Hub and Arc Sense sensors ---
    hub_map: dict[str, dict] = {}
    device_to_hub_map: dict[str, str] = {}
    created_entity_ids: set[str] = set()

    # Step 1: collect hubs from main device list
    for device in coordinator.data.get("devices", []):
        device_title = device.get("deviceTitle", {})
        if device_title.get("deviceType") != "arc-hub":
            continue
        hub_identity = device_title.get("identity") or device.get("mac", "unknown")
        hub_map[hub_identity] = {
            "device": device,
            "name": device_title.get("name", "LK ARC Hub"),
            "children": [],
            "parent": device_title.get("parentIdentity"),
        }

    # Also collect hubs from hub_data
    for hub_id, hub_data in coordinator.data.get("hub_data", {}).items():
        if hub_id in hub_map or ":" not in hub_id:
            continue
        # Try to find matching device entry first
        for device in coordinator.data.get("devices", []):
            if (
                device.get("mac") == hub_id
                or device.get("deviceTitle", {}).get("identity") == hub_id
            ):
                device_title = device.get("deviceTitle", {})
                hub_map[hub_id] = {
                    "device": device,
                    "name": device_title.get("name", f"LK ARC Hub {hub_id[-5:]}"),
                    "children": [],
                    "parent": device_title.get("parentIdentity"),
                }
                break
        else:
            hub_map[hub_id] = {
                "device": {"mac": hub_id, "deviceTitle": {"identity": hub_id, "deviceType": "arc-hub"}},
                "name": f"LK ARC Hub {hub_id[-5:]}",
                "children": [],
                "parent": None,
            }

    # Step 2: map child devices to their parent hub
    for device in coordinator.data.get("devices", []):
        device_title = device.get("deviceTitle", {})
        if device_title.get("deviceType") == "arc-hub":
            continue
        parent = device_title.get("parentIdentity")
        identity = device_title.get("identity") or device.get("mac")
        if parent and parent in hub_map and identity:
            hub_map[parent]["children"].append(identity)
            device_to_hub_map[identity] = parent

    for hub_id, hub_data in coordinator.data.get("hub_data", {}).items():
        if not isinstance(hub_data, dict):
            continue
        for device in hub_data.get("devices", []):
            device_title = device.get("deviceTitle", {})
            if device_title.get("deviceType") == "arc-hub":
                continue
            identity = device_title.get("identity") or device.get("mac")
            parent = device_title.get("parentIdentity") or hub_id
            if identity and parent in hub_map and identity not in hub_map[parent]["children"]:
                hub_map[parent]["children"].append(identity)
                device_to_hub_map[identity] = parent

    # Step 3: create hub entities
    hub_entities: list[LKArcHubEntity] = []
    for hub_identity, hub_info in hub_map.items():
        entity_id = f"{DOMAIN}_{hub_identity}_status"
        if entity_id not in created_entity_ids:
            hub_entities.append(
                LKArcHubEntity(coordinator, hub_info["device"], "status", "Status", "mdi:router-wireless", None, None)
            )
            created_entity_ids.add(entity_id)

    if hub_entities:
        async_add_entities(hub_entities)

    # Step 4: create Arc Sense sensor entities
    sensor_entities: list[LKArcSensorEntity] = []

    def _add_arc_sense_entities(device: dict) -> None:
        device_title = device.get("deviceTitle", {})
        if (
            device_title.get("deviceGroup") != "arc"
            or device_title.get("deviceType") != "arc-sense"
        ):
            return
        identity = device_title.get("identity") or device.get("mac")
        if not identity:
            return
        # Ensure parent is set
        parent = device_to_hub_map.get(identity) or device_title.get("parentIdentity")
        if parent:
            device["deviceTitle"]["parentIdentity"] = parent

        measurement = device.get("measurement") or {}
        for key, device_class, state_class, unit, icon, name in [
            ("currentTemperature", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, UnitOfTemperature.CELSIUS, "mdi:thermometer", "Temperature"),
            ("currentHumidity", SensorDeviceClass.HUMIDITY, SensorStateClass.MEASUREMENT, PERCENTAGE, "mdi:water-percent", "Humidity"),
            ("currentBattery", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, PERCENTAGE, "mdi:battery", "Battery"),
            ("currentRssi", SensorDeviceClass.SIGNAL_STRENGTH, SensorStateClass.MEASUREMENT, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, "mdi:wifi", "RSSI"),
        ]:
            if measurement.get(key) is None:
                continue
            entity_id = f"{DOMAIN}_{identity}_{key}"
            if entity_id not in created_entity_ids:
                sensor_entities.append(
                    LKArcSensorEntity(coordinator, device, key, name, icon, device_class, state_class, unit)
                )
                created_entity_ids.add(entity_id)

    for device in coordinator.data.get("devices", []):
        _add_arc_sense_entities(device)

    if sensor_entities:
        async_add_entities(sensor_entities)
        _LOGGER.debug("Added %d Arc Sense sensor entities", len(sensor_entities))


class LKArcSensorEntity(CoordinatorEntity, SensorEntity):
    """Representation of an LK Systems Arc Sense sensor entity."""

    def __init__(
        self,
        coordinator: LKSystemCoordinator,
        device: dict,
        entity_key: str,
        name_suffix: str,
        icon: str,
        device_class: Optional[str] = None,
        state_class: Optional[str] = None,
        unit_of_measurement: Optional[str] = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._device = device
        self._entity_key = entity_key
        self._attr_icon = icon
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit_of_measurement

        device_title = device.get("deviceTitle", {})
        device_id = device.get("mac")
        device_identity = device_title.get("identity") or device_id
        device_type = device_title.get("deviceType", "unknown")
        parent_identity = device_title.get("parentIdentity")

        self._device_identity = device_identity
        self._attr_unique_id = f"{DOMAIN}_{device_identity}_{entity_key}"

        friendly_name = device_title.get("name")
        if friendly_name:
            self._attr_name = f"{friendly_name} {name_suffix}"
        else:
            zone_name = device_title.get("zone", {}).get("zoneName") if device_title.get("zone") else None
            self._attr_name = f"LK {zone_name} {name_suffix}" if zone_name else f"LK Sensor {name_suffix}"

        device_info: dict = {
            "identifiers": {(DOMAIN, device_identity)},
            "name": self._attr_name.replace(f" {name_suffix}", ""),
            "manufacturer": "LK Systems",
            "model": device_type,
        }
        if parent_identity:
            device_info["via_device"] = (DOMAIN, parent_identity)

        self._attr_device_info = DeviceInfo(**device_info)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        for device in self.coordinator.data.get("devices", []):
            device_title = device.get("deviceTitle", {})
            if device.get("mac") == self._device.get("mac") or device_title.get("identity") == self._device_identity:
                return True
        for hub_data in self.coordinator.data.get("hub_data", {}).values():
            if isinstance(hub_data, dict):
                for device in hub_data.get("devices", []):
                    device_title = device.get("deviceTitle", {})
                    if device.get("mac") == self._device.get("mac") or device_title.get("identity") == self._device_identity:
                        return True
        return False

    def _get_measurement_value(self, measurement: dict) -> Any:
        """Extract this sensor's value from a measurement dict."""
        raw = measurement.get(self._entity_key)
        if raw is None:
            return None
        if self._entity_key in ("currentTemperature", "currentHumidity", "desiredTemperature"):
            return float(raw) / 10
        return raw

    @property
    def native_value(self) -> Any:
        """Return the value of the sensor."""
        # Prefer device_details (freshest data)
        device_details = self.coordinator.data.get("device_details", {}).get(self._device_identity)
        if device_details and "measurement" in device_details:
            value = self._get_measurement_value(device_details["measurement"])
            if value is not None:
                return value

        # Fall back to devices list
        for device in self.coordinator.data.get("devices", []):
            device_title = device.get("deviceTitle", {})
            if device.get("mac") == self._device.get("mac") or device_title.get("identity") == self._device_identity:
                if "measurement" in device:
                    value = self._get_measurement_value(device["measurement"])
                    if value is not None:
                        return value

        # Fall back to hub_data
        for hub_data in self.coordinator.data.get("hub_data", {}).values():
            if isinstance(hub_data, dict):
                for device in hub_data.get("devices", []):
                    device_title = device.get("deviceTitle", {})
                    if device.get("mac") == self._device.get("mac") or device_title.get("identity") == self._device_identity:
                        if "measurement" in device:
                            value = self._get_measurement_value(device["measurement"])
                            if value is not None:
                                return value

        return None

    async def async_update(self) -> None:
        """Force update this device."""
        if hasattr(self.coordinator, "force_device_update"):
            try:
                await self.coordinator.force_device_update(self._device_identity)
            except Exception as ex:
                _LOGGER.error("Error during manual device update: %s", ex)
        await super().async_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional sensor attributes."""
        attrs: dict[str, Any] = {}
        if self.coordinator and hasattr(self.coordinator, "update_interval"):
            attrs["update_interval_minutes"] = self.coordinator.update_interval.total_seconds() / 60
        if self.coordinator and hasattr(self.coordinator, "_last_update_time"):
            attrs["last_updated"] = self.coordinator._last_update_time.isoformat()
            attrs["next_update"] = (self.coordinator._last_update_time + self.coordinator.update_interval).isoformat()
        return attrs


class LKArcHubEntity(CoordinatorEntity, SensorEntity):
    """Representation of an LK Systems ARC Hub entity."""

    def __init__(
        self,
        coordinator: LKSystemCoordinator,
        device: dict,
        entity_key: str,
        name_suffix: str,
        icon: str,
        device_class: Optional[str] = None,
        state_class: Optional[str] = None,
    ) -> None:
        """Initialize the hub entity."""
        super().__init__(coordinator)

        self._device = device
        self._entity_key = entity_key
        self._attr_icon = icon
        self._attr_state_class = state_class

        device_title = device.get("deviceTitle", {})
        device_id = device.get("mac")
        device_identity = device_title.get("identity") or device_id
        device_type = device_title.get("deviceType", "unknown")
        parent_identity = device_title.get("parentIdentity")

        self._device_identity = device_identity
        self._attr_unique_id = f"{DOMAIN}_{device_identity}_{entity_key}"

        friendly_name = device_title.get("name")
        self._attr_name = f"{friendly_name} {name_suffix}" if friendly_name else f"LK ARC Hub {name_suffix}"

        device_info: dict = {
            "identifiers": {(DOMAIN, device_identity)},
            "name": self._attr_name.replace(f" {name_suffix}", ""),
            "manufacturer": "LK Systems",
            "model": device_type,
            "sw_version": None,
        }
        if parent_identity:
            device_info["via_device"] = (DOMAIN, parent_identity)

        self._attr_device_info = DeviceInfo(**device_info)

    @property
    def native_value(self) -> Any:
        """Return the connection state of the hub."""
        # Check device_details first
        device_details = self.coordinator.data.get("device_details", {}).get(self._device_identity)
        if device_details and "measurement" in device_details:
            return device_details["measurement"].get("connectionState", "Unknown")

        # Check devices list
        for device in self.coordinator.data.get("devices", []):
            device_title = device.get("deviceTitle", {})
            if device.get("mac") == self._device.get("mac") or device_title.get("identity") == self._device_identity:
                if "measurement" in device:
                    return device["measurement"].get("connectionState", "Unknown")

        # Check hub_data
        for hub_data in self.coordinator.data.get("hub_data", {}).values():
            if isinstance(hub_data, dict):
                for device in hub_data.get("devices", []):
                    device_title = device.get("deviceTitle", {})
                    if device.get("mac") == self._device.get("mac") or device_title.get("identity") == self._device_identity:
                        if "measurement" in device:
                            return device["measurement"].get("connectionState", "Connected")
                        return "Connected"

        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class AbstractLkCubicSensor(CoordinatorEntity[LKSystemCoordinator], SensorEntity):
    """Abstract base for LK CubicSecure sensors."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LKSystemCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        machine_info = coordinator.data["cubic_machine_info"]
        self._device_model = CUBIC_SECURE_MODEL
        self._device_name = f"Cubic Secure {machine_info['zone']['zoneName']}"
        self._id = machine_info["identity"]
        self.entity_description = description
        self._attr_unique_id = f"LkUid_{description.key}_{self._id}"
        self._attr_extra_state_attributes = {}

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._id)},
            manufacturer=MANUFACTURER,
            model=self._device_model,
            name=self._device_name,
            serial_number=self._id,
        )


class LKCubicSensor(AbstractLkCubicSensor):
    """Sensor for a CubicSecure measurement or configuration value."""

    def __init__(
        self,
        coordinator: LKSystemCoordinator,
        description: SensorEntityDescription,
        data_source: str = "measurement",
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, description=description)
        self._data_source = data_source
        self._data_key = description.key
        self._attr_extra_state_attributes = {}

        if "update_time" in self._coordinator.data:
            self._attr_extra_state_attributes[C_UPDATE_TIME] = self._coordinator.data["update_time"]
        if "next_update_time" in self._coordinator.data:
            self._attr_extra_state_attributes[C_NEXT_UPDATE_TIME] = self._coordinator.data["next_update_time"]

        self._attr_available = False

    async def async_update(self) -> None:
        """Mark the entity as available on first update."""
        self._attr_available = True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle coordinator update."""
        if "update_time" in self._coordinator.data:
            self._attr_extra_state_attributes[C_UPDATE_TIME] = self._coordinator.data["update_time"]
        if "next_update_time" in self._coordinator.data:
            self._attr_extra_state_attributes[C_NEXT_UPDATE_TIME] = self._coordinator.data["next_update_time"]
        super()._handle_coordinator_update()

    @property
    def native_value(self) -> Any:
        """Return the sensor value with any necessary transformations."""
        data = self._coordinator.data.get(
            "cubic_configuration" if self._data_source == "configuration" else "cubic_last_measurement"
        )
        if not data:
            return None

        # Navigate dot-separated keys (e.g. "leak.meanFlow")
        if "." in self._data_key:
            value: Any = data
            for key in self._data_key.split("."):
                if not isinstance(value, dict):
                    return None
                value = value.get(key)
                if value is None:
                    return None
        else:
            value = data.get(self._data_key)

        if value is None:
            return None

        # waterPressure: API returns units of 0.1 bar → convert to bar
        if self._data_key == "waterPressure" and isinstance(value, (int, float)):
            return round(value / 10, 1)

        # Timestamp fields: convert Unix timestamp to UTC datetime
        if (
            self.entity_description.device_class == SensorDeviceClass.TIMESTAMP
            and isinstance(value, (int, float))
            and value > 0
        ):
            return datetime.fromtimestamp(value, tz=timezone.utc)

        return value


def _voltage_to_battery_percent(millivolts: int) -> int:
    """Convert battery voltage in mV to a percentage (matches Homey conversion)."""
    if millivolts >= 2880:
        return round(50 + (millivolts - 2880) / (3300 - 2880) * 50)
    if millivolts >= 2550:
        return round(10 + (millivolts - 2550) / (2880 - 2550) * 40)
    if millivolts >= 2100:
        return round(1 + (millivolts - 2100) / (2550 - 2100) * 9)
    return 0


class LKCubicDetectorSensor(CoordinatorEntity[LKSystemCoordinator], SensorEntity):
    """Sensor entity for a single CubicDetector measurement value."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: LKSystemCoordinator,
        detector: dict,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        machine_info = detector["machine_info"]
        self._identity = machine_info["identity"]
        zone_name = machine_info.get("zone", {}).get("zoneName", "Unknown")
        device_name = f"Cubic Detector {zone_name}"

        self.entity_description = description
        self._data_key = description.key
        self._attr_unique_id = f"LkUid_detector_{description.key}_{self._identity}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._identity)},
            manufacturer=MANUFACTURER,
            model=CUBIC_DETECTOR_MODEL,
            name=device_name,
            serial_number=self._identity,
        )

    def _current_measurement(self) -> dict:
        """Return the freshest measurement dict for this detector."""
        for detector in self.coordinator.data.get("cubic_detectors", []):
            if detector.get("machine_info", {}).get("identity") == self._identity:
                return detector.get("measurement") or {}
        return {}

    @property
    def available(self) -> bool:
        """Return True when the coordinator has data for this detector."""
        if not self.coordinator.last_update_success:
            return False
        for detector in self.coordinator.data.get("cubic_detectors", []):
            if detector.get("machine_info", {}).get("identity") == self._identity:
                return detector.get("measurement") is not None
        return False

    @property
    def native_value(self) -> Any:
        """Return the sensor value with any necessary transformations."""
        measurement = self._current_measurement()
        if not measurement:
            return None

        value = measurement.get(self._data_key)
        if value is None:
            return None

        # Humidity: API returns ×10 (e.g. 550 = 55.0 %)
        if self._data_key == "currentHumidity" and isinstance(value, (int, float)):
            return round(value / 10, 1)

        # Battery: API returns millivolts — convert to percentage
        if self._data_key == "currentBattery" and isinstance(value, int):
            return _voltage_to_battery_percent(value)

        # Timestamp fields: convert Unix timestamp to UTC datetime
        if (
            self.entity_description.device_class == SensorDeviceClass.TIMESTAMP
            and isinstance(value, (int, float))
            and value > 0
        ):
            return datetime.fromtimestamp(value, tz=timezone.utc)

        return value

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
