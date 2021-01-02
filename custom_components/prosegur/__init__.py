"""The Prosegur Alarm integration."""
import asyncio

from pyprosegur.auth import Auth
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["alarm_control_panel"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Prosegur Alarm component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Prosegur Alarm from a config entry."""
    session = aiohttp_client.async_get_clientsession(hass)
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = Auth(
        session, entry.data["username"], entry.data["password"]
    )

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
