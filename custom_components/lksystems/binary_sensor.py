"""Binary sensor platform for LK Systems integration."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LKSystemCoordinator
from .const import (
    ATTRIBUTION,
    CUBIC_DETECTOR_MODEL,
    CUBIC_SECURE_LEAK_NO_LEAK,
    CUBIC_SECURE_MODEL,
    DOMAIN,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LK Systems binary sensors from a config entry."""
    coordinator: LKSystemCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []

    if coordinator.data.get("cubic_machine_info"):
        entities.append(LKCubicLeakBinarySensor(coordinator))

    for detector in coordinator.data.get("cubic_detectors", []):
        if detector.get("machine_info", {}).get("identity"):
            entities.append(LKCubicDetectorLeakBinarySensor(coordinator, detector))

    if entities:
        async_add_entities(entities, True)


class LKCubicLeakBinarySensor(CoordinatorEntity[LKSystemCoordinator], BinarySensorEntity):
    """Binary sensor that is on when the CubicSecure detects a water leak."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_name = "Water Leak"
    _attr_icon = "mdi:water-alert"

    def __init__(self, coordinator: LKSystemCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        machine_info = coordinator.data["cubic_machine_info"]
        self._id = machine_info["identity"]
        zone_name = machine_info["zone"]["zoneName"]
        device_name = f"Cubic Secure {zone_name}"

        self._attr_unique_id = f"LkUid_leak_alarm_{self._id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._id)},
            manufacturer=MANUFACTURER,
            model=CUBIC_SECURE_MODEL,
            name=device_name,
            serial_number=self._id,
        )

    @property
    def is_on(self) -> bool | None:
        """Return True when a leak is active."""
        measurement = self.coordinator.data.get("cubic_last_measurement") or {}
        leak = measurement.get("leak") or {}
        leak_state = leak.get("leakState")
        if leak_state is None:
            return None
        return leak_state != CUBIC_SECURE_LEAK_NO_LEAK

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class LKCubicDetectorLeakBinarySensor(CoordinatorEntity[LKSystemCoordinator], BinarySensorEntity):
    """Binary sensor that is on when a CubicDetector detects water or freezing."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_name = "Water Leak"
    _attr_icon = "mdi:water-alert"

    def __init__(self, coordinator: LKSystemCoordinator, detector: dict) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        machine_info = detector["machine_info"]
        self._identity = machine_info["identity"]
        zone_name = machine_info.get("zone", {}).get("zoneName", "Unknown")
        device_name = f"Cubic Detector {zone_name}"

        self._attr_unique_id = f"LkUid_detector_leak_alarm_{self._identity}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._identity)},
            manufacturer=MANUFACTURER,
            model=CUBIC_DETECTOR_MODEL,
            name=device_name,
            serial_number=self._identity,
        )

    @property
    def is_on(self) -> bool | None:
        """Return True when a leak or freeze is detected."""
        for detector in self.coordinator.data.get("cubic_detectors", []):
            if detector.get("machine_info", {}).get("identity") == self._identity:
                measurement = detector.get("measurement") or {}
                leak = measurement.get("leak") or {}
                leak_state = leak.get("leakState")
                if leak_state is None:
                    return None
                return leak_state != CUBIC_SECURE_LEAK_NO_LEAK
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
