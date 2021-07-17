"""Support for Prosegur alarm control panels."""
import logging

from pyprosegur.auth import Auth
from pyprosegur.installation import Installation, Status

import homeassistant.components.alarm_control_panel as alarm
from homeassistant.components.alarm_control_panel import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
)
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
)

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

STATE_MAPPING = {
    Status.DISARMED: STATE_ALARM_DISARMED,
    Status.ARMED: STATE_ALARM_ARMED_AWAY,
    Status.PARTIALLY: STATE_ALARM_ARMED_HOME,
    Status.ERROR_PARTIALLY: STATE_ALARM_ARMED_HOME,
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Prosegur alarm control panel platform."""
    async_add_entities(
        [ProsegurAlarm(entry.data["contract"], hass.data[DOMAIN][entry.entry_id])]
    )


class ProsegurAlarm(alarm.AlarmControlPanelEntity):
    """Representation of a Prosegur alarm status."""

    def __init__(self, contract: str, auth: Auth):
        """Initialize the Prosegur alarm panel."""
        self._attr_state = None
        self._changed_by = None

        self._installation = None
        self.contract = contract
        self._auth = auth

        self._attr_name = f"contract {self.contract}"
        self._attr_unique_id = self.contract
        self._attr_supported_features = SUPPORT_ALARM_ARM_AWAY | SUPPORT_ALARM_ARM_HOME

    async def async_update(self):
        """Update alarm status."""

        try:
            self._installation = await Installation.retrieve(self._auth)
        except ConnectionError as err:
            _LOGGER.error(err)
            self._attr_state = None
            return

        self._attr_state = STATE_MAPPING.get(self._installation.status)

    async def async_alarm_disarm(self, code=None):
        """Send disarm command."""
        if self._installation is None:
            await self.async_update()
        await self._installation.disarm(self._auth)

    async def async_alarm_arm_home(self, code=None):
        """Send arm away command."""
        if self._installation is None:
            await self.async_update()
        await self._installation.arm_partially(self._auth)

    async def async_alarm_arm_away(self, code=None):
        """Send arm away command."""
        if self._installation is None:
            await self.async_update()
        await self._installation.arm(self._auth)
