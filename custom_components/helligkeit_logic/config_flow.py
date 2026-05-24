import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from .const import *

class HelligkeitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Helligkeits-Logik", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_SENSOR1): selector.EntitySelector({"domain": "sensor"}),
            vol.Required(CONF_SENSOR2): selector.EntitySelector({"domain": "sensor"}),
            vol.Required(CONF_ELEVATION): selector.EntitySelector({"domain": "sensor"}),

            vol.Required(CONF_SONNE1, default=30000): int,
            vol.Required(CONF_WOLKE1, default=15000): int,
            vol.Required(CONF_SONNE2, default=8000): int,
            vol.Required(CONF_WOLKE2, default=3000): int,

            vol.Required(CONF_TIME_SONNE, default=5): int,
            vol.Required(CONF_TIME_WOLKE, default=40): int,
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_options(self, user_input=None):
        return await self.async_step_user(user_input)
