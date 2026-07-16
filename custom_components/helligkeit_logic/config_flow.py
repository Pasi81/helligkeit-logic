import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv

try:
    from homeassistant.helpers import selector
except ImportError:  # pragma: no cover
    selector = None

from .const import (
    CONF_ELEVATION,
    CONF_NAME,
    CONF_SENSOR1,
    CONF_SENSOR2,
    CONF_SONNE1,
    CONF_SONNE2,
    CONF_TIME_SONNE,
    CONF_TIME_WOLKE,
    CONF_WOLKE1,
    CONF_WOLKE2,
    DEFAULT_NAME,
    DOMAIN,
)


def _sensor_selector():
    if selector is not None and hasattr(selector, "EntitySelector"):
        return selector.EntitySelector({"domain": "sensor"})
    return cv.entity_id


class HelligkeitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def _build_schema(self, config_entry=None):
        current = {}
        if config_entry is not None:
            current = {**config_entry.data, **config_entry.options}

        return vol.Schema({
            vol.Required(CONF_NAME, default=current.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_SENSOR1, default=current.get(CONF_SENSOR1)): _sensor_selector(),
            vol.Required(CONF_SENSOR2, default=current.get(CONF_SENSOR2)): _sensor_selector(),
            vol.Required(CONF_ELEVATION, default=current.get(CONF_ELEVATION)): _sensor_selector(),
            vol.Required(CONF_SONNE1, default=current.get(CONF_SONNE1, 8000)): int,
            vol.Required(CONF_WOLKE1, default=current.get(CONF_WOLKE1, 3000)): int,
            vol.Required(CONF_SONNE2, default=current.get(CONF_SONNE2, 8000)): int,
            vol.Required(CONF_WOLKE2, default=current.get(CONF_WOLKE2, 3000)): int,
            vol.Required(CONF_TIME_SONNE, default=current.get(CONF_TIME_SONNE, 3)): int,
            vol.Required(CONF_TIME_WOLKE, default=current.get(CONF_TIME_WOLKE, 40)): int,
        })

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=user_input.get(CONF_NAME, DEFAULT_NAME), data=user_input)

        return self.async_show_form(step_id="user", data_schema=self._build_schema())

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            self.hass.config_entries.async_update_entry(entry, data=user_input)
            await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(step_id="reconfigure", data_schema=self._build_schema(entry))

    async def async_get_options_flow(self, config_entry):
        return HelligkeitOptionsFlow(config_entry)


class HelligkeitOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        current = {**self.config_entry.data, **self.config_entry.options}

        if user_input is not None:
            self.config_entry.async_update_entry(title=user_input.get(CONF_NAME, DEFAULT_NAME))
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_NAME, default=current.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_SENSOR1, default=current.get(CONF_SENSOR1)): _sensor_selector(),
            vol.Required(CONF_SENSOR2, default=current.get(CONF_SENSOR2)): _sensor_selector(),
            vol.Required(CONF_ELEVATION, default=current.get(CONF_ELEVATION)): _sensor_selector(),
            vol.Required(CONF_SONNE1, default=current.get(CONF_SONNE1, 8000)): int,
            vol.Required(CONF_WOLKE1, default=current.get(CONF_WOLKE1, 3000)): int,
            vol.Required(CONF_SONNE2, default=current.get(CONF_SONNE2, 8000)): int,
            vol.Required(CONF_WOLKE2, default=current.get(CONF_WOLKE2, 3000)): int,
            vol.Required(CONF_TIME_SONNE, default=current.get(CONF_TIME_SONNE, 3)): int,
            vol.Required(CONF_TIME_WOLKE, default=current.get(CONF_TIME_WOLKE, 40)): int,
        })

        return self.async_show_form(step_id="init", data_schema=schema)
