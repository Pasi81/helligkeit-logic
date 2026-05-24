from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry):
    hass.data.setdefault(DOMAIN, {})
    hass.helpers.discovery.load_platform("sensor", DOMAIN, entry.data, entry)
    return True
