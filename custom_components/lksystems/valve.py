"""Valve platform for LK Systems integration."""

from __future__ import annotations

import logging

from homeassistant.components.valve import (
    ValveDeviceClass,
    ValveEntity,
    ValveEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import LKSystemCoordinator
from .const import (
    ATTRIBUTION,
    CUBIC_SECURE_MODEL,
    CUBIC_SECURE_VALVE_CLOSED,
    DOMAIN,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LK Systems valve entities from a config entry."""
    coordinator: LKSystemCoordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator.data.get("cubic_machine_info"):
        async_add_entities([LKCubicValve(coordinator)], True)


class LKCubicValve(CoordinatorEntity[LKSystemCoordinator], ValveEntity):
    """Valve entity for the CubicSecure main water shutoff."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_device_class = ValveDeviceClass.WATER
    _attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE
    _attr_reports_position = False
    _attr_name = "Valve"
    _attr_icon = "mdi:valve"

    def __init__(self, coordinator: LKSystemCoordinator) -> None:
        """Initialize the valve entity."""
        super().__init__(coordinator)
        machine_info = coordinator.data["cubic_machine_info"]
        self._id = machine_info["identity"]
        zone_name = machine_info["zone"]["zoneName"]
        device_name = f"Cubic Secure {zone_name}"

        self._attr_unique_id = f"LkUid_valve_{self._id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._id)},
            manufacturer=MANUFACTURER,
            model=CUBIC_SECURE_MODEL,
            name=device_name,
            serial_number=self._id,
        )

    @property
    def is_closed(self) -> bool | None:
        """Return True when the valve is closed."""
        config = self.coordinator.data.get("cubic_configuration") or {}
        valve_state = config.get("valveState")
        if valve_state is None:
            return None
        return valve_state == CUBIC_SECURE_VALVE_CLOSED

    async def async_open_valve(self) -> None:
        """Open the water valve."""
        try:
            await self.coordinator.cubic_secure_open_valve(self._id)
            await self.coordinator.async_refresh()
        except Exception as err:
            _LOGGER.error("Error opening valve %s: %s", self._id, err)

    async def async_close_valve(self) -> None:
        """Close the water valve."""
        try:
            await self.coordinator.cubic_secure_close_valve(self._id)
            await self.coordinator.async_refresh()
        except Exception as err:
            _LOGGER.error("Error closing valve %s: %s", self._id, err)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
