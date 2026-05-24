from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN

async def async_setup(hass: HomeAssistant, config: dict):
    """Wird benötigt, damit HA die Integration akzeptiert."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setup über ConfigFlow."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Sensor registrieren
    hass.helpers.discovery.load_platform(
        "sensor",
        DOMAIN,
        entry.data,
        entry
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Integration sauber entladen."""
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
