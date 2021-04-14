"""Config flow for Prosegur Alarm integration."""
import logging

from pyprosegur.auth import COUNTRY, Auth
from pyprosegur.installation import Installation
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import aiohttp_client

from .const import CONF_COUNTRY, DOMAIN  # pylint:disable=unused-import

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_COUNTRY): vol.In(COUNTRY.keys()),
    }
)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect."""
    try:
        session = aiohttp_client.async_get_clientsession(hass)
        auth = Auth(
            session, data[CONF_USERNAME], data[CONF_PASSWORD], data[CONF_COUNTRY]
        )
        install = await Installation.retrieve(auth)
    except ConnectionRefusedError:
        raise InvalidAuth from ConnectionRefusedError
    except ConnectionError:
        raise CannotConnect from ConnectionError

    # Info to store in the config entry.
    return {
        "title": f"Contract {install.contract}",
        "contract": install.contract,
        "username": data[CONF_USERNAME],
        "password": data[CONF_PASSWORD],
        "country": data[CONF_COUNTRY],
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Prosegur Alarm."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input:
            try:
                info = await validate_input(self.hass, user_input)

                await self.async_set_unique_id(info["contract"])
                self._abort_if_unique_id_configured()

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as exception:  # pylint: disable=broad-except
                _LOGGER.exception(exception)
                errors["base"] = "unknown"
            else:
                user_input["contract"] = info["contract"]
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
