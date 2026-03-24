"""LK Systems service actions."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .pylksystems import LKPressureThresholds, LKThresholds

_LOGGER = logging.getLogger(__name__)


async def async_setup_services(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Register LK Systems service actions."""

    def _get_serial(call: ServiceCall) -> str | None:
        """Extract the device serial number from a service call's device_id."""
        device_id = call.data.get("device_id")
        device_entry = dr.async_get(hass).async_get(device_id)
        if device_entry is None:
            _LOGGER.error("Device not found: %s", device_id)
            return None
        sn = device_entry.serial_number
        if not sn:
            _LOGGER.error("No serial number for device %s", device_id)
        return sn

    async def pause_leak_detection(call: ServiceCall) -> None:
        """Pause leak detection for the given number of seconds."""
        sn = _get_serial(call)
        if not sn:
            return
        seconds = int(call.data.get("seconds", 3600))
        coordinator = hass.data[DOMAIN][entry.entry_id]
        try:
            await coordinator.cubic_secure_pause_leak_detection(sn, seconds)
        except Exception as err:
            _LOGGER.error("Error pausing leak detection: %s", err)

    async def close_valve(call: ServiceCall) -> None:
        """Close the main water valve."""
        sn = _get_serial(call)
        if not sn:
            return
        coordinator = hass.data[DOMAIN][entry.entry_id]
        try:
            await coordinator.cubic_secure_close_valve(sn)
        except Exception as err:
            _LOGGER.error("Error closing valve: %s", err)

    async def open_valve(call: ServiceCall) -> None:
        """Open the main water valve."""
        sn = _get_serial(call)
        if not sn:
            return
        coordinator = hass.data[DOMAIN][entry.entry_id]
        try:
            await coordinator.cubic_secure_open_valve(sn)
        except Exception as err:
            _LOGGER.error("Error opening valve: %s", err)

    async def set_pressure_test_schedule(call: ServiceCall) -> None:
        """Set the pressure test schedule."""
        sn = _get_serial(call)
        if not sn:
            return
        hour = call.data.get("hour", 2)
        minute = call.data.get("minute", 0)
        coordinator = hass.data[DOMAIN][entry.entry_id]
        try:
            await coordinator.cubic_secure_set_pressure_test_schedule(sn, hour, minute)
        except Exception as err:
            _LOGGER.error("Error setting pressure test schedule: %s", err)

    async def set_thresholds(call: ServiceCall) -> None:
        """Set leak detection thresholds."""
        sn = _get_serial(call)
        if not sn:
            return
        thresholds = LKThresholds(
            pressure=LKPressureThresholds(
                sensitivity=call.data.get("pressure_sensitivity", 0.3),
                duration=call.data.get("pressure_test_duration", 45),
                closeDelay=call.data.get("pressure_close_delay", 255600),
                notificationDelay=call.data.get("pressure_notification_delay", 169200),
            ),
            leakMedium={
                "threshold": call.data.get("medium_leak_threshold", 5.0),
                "closeDelay": call.data.get("medium_leak_close_delay", 2700),
                "notificationDelay": call.data.get("medium_leak_notification_delay", 2700),
            },
            leakLarge={
                "threshold": call.data.get("large_leak_threshold", 1500.0),
                "closeDelay": call.data.get("large_leak_close_delay", 90),
                "notificationDelay": call.data.get("large_leak_notification_delay", 90),
            },
        )
        coordinator = hass.data[DOMAIN][entry.entry_id]
        try:
            await coordinator.cubic_secure_set_thresholds(sn, thresholds)
        except Exception as err:
            _LOGGER.error("Error setting thresholds: %s", err)

    hass.services.async_register(DOMAIN, "pause_leak_detection", pause_leak_detection)
    hass.services.async_register(DOMAIN, "close_valve", close_valve)
    hass.services.async_register(DOMAIN, "open_valve", open_valve)
    hass.services.async_register(DOMAIN, "set_pressure_test_schedule", set_pressure_test_schedule)
    hass.services.async_register(DOMAIN, "set_thresholds", set_thresholds)
