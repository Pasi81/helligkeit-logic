from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from datetime import datetime
import logging
from .const import (
    CONF_NAME,
    CONF_SENSOR1,
    CONF_SENSOR2,
    CONF_ELEVATION,
    CONF_SONNE1,
    CONF_WOLKE1,
    CONF_SONNE2,
    CONF_WOLKE2,
    CONF_TIME_SONNE,
    CONF_TIME_WOLKE,
    DEFAULT_NAME,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities):
    """Setup über ConfigFlow."""
    add_entities([HelligkeitLogicSensor(hass, entry)], True)


class HelligkeitLogicSensor(SensorEntity):

    def __init__(self, hass, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self.cfg = {**entry.data, **entry.options}

        integration_name = self.cfg.get(CONF_NAME, DEFAULT_NAME)
        self._attr_name = f"{integration_name} Status"
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_icon = "mdi:brightness-auto"
        self._attr_native_unit_of_measurement = None

        self._state = "Unbekannt"
        self.last_change = datetime.now()
        self.zustand = 0
        self.wechsel_sonne = 0
        self.wechsel_wolken = 0

    @property
    def icon(self):
        if self.zustand == 2:
            return "mdi:weather-sunny"
        if self.zustand == 1:
            return "mdi:weather-cloudy"
        return "mdi:weather-night"

    @property
    def native_value(self):
        return self.zustand

    @property
    def state(self):
        return self.zustand

    @property
    def extra_state_attributes(self):
        return {
            "zustand_text": self._state,
            "wechsel_zu_sonne": self.wechsel_sonne,
            "wechsel_zu_wolken": self.wechsel_wolken,
            "last_change": self.last_change.isoformat(),
        }

    async def async_update(self):
        def _safe_float(entity):
            if entity is None:
                return 0.0
            try:
                return float(entity.state)
            except (ValueError, TypeError):
                return 0.0

        h1_state = self.hass.states.get(self.cfg[CONF_SENSOR1])
        h2_state = self.hass.states.get(self.cfg[CONF_SENSOR2])
        elev_state = self.hass.states.get(self.cfg[CONF_ELEVATION])

        h1 = _safe_float(h1_state)
        h2 = _safe_float(h2_state)
        elev = _safe_float(elev_state)

        _LOGGER.debug(f"Sensoren: h1={h1}, h2={h2}, elev={elev}")

        sonne1 = self.cfg[CONF_SONNE1]
        wolke1 = self.cfg[CONF_WOLKE1]
        sonne2 = self.cfg[CONF_SONNE2]
        wolke2 = self.cfg[CONF_WOLKE2]
        
        _LOGGER.debug(f"Konfiguration: sonne1={sonne1}, wolke1={wolke1}, sonne2={sonne2}, wolke2={wolke2}")

        elev_max = 65
        elevmin = 3

        if elev >= elevmin:
            sonne1_b = sonne1 * elev / elev_max
            sonne2_b = sonne2 * elev / elev_max
            wolke1_b = wolke1 * elev / elev_max
            wolke2_b = wolke2 * elev / elev_max
        else:
            sonne1_b = sonne1
            sonne2_b = sonne2
            wolke1_b = wolke1
            wolke2_b = wolke2
        
        if h1 < 10 and h2 < 5 or elev < elevmin:
            status = 0
        elif h1 > 100 and h2 > 50 and elev >= elevmin:
            if h1 > sonne1_b or h2 > sonne2_b:
                status = 2
            elif h1 < wolke1_b and h2 < wolke2_b:
                status = 1
            else:
                status = 99
        else:
            status = 99

        now = datetime.now()
        diff = (now - self.last_change).total_seconds() / 60
        
        _LOGGER.debug(f"Status: {status}, zustand: {self.zustand}, diff: {diff}")

        if status == 0:
            self.zustand = 0
            self.wechsel_sonne = 0
            self.wechsel_wolken = 0
            self.last_change = now

        elif status == 1:
            if self.zustand == 2 and self.wechsel_wolken == 0:
                self.wechsel_wolken = 1
                self.wechsel_sonne = 0
                self.last_change = now

            if self.wechsel_wolken == 1 and diff > self.cfg[CONF_TIME_WOLKE]:
                self.zustand = 1
                self.wechsel_wolken = 0
                self.wechsel_sonne = 0

        elif status == 2:
            if self.zustand == 1 and self.wechsel_sonne == 0:
                self.wechsel_sonne = 1
                self.wechsel_wolken = 0
                self.last_change = now

            if (self.wechsel_sonne == 1 and diff > self.cfg[CONF_TIME_SONNE]) or self.zustand == 0:
                self.zustand = 2
                self.wechsel_sonne = 0
                self.wechsel_wolken = 0

        if self.zustand == 0:
            self._state = "Nacht"
        elif self.zustand == 1:
            self._state = "Wolkig"
        elif self.zustand == 2:
            self._state = "Sonnig"
        else:
            self._state = "Unbekannt"
            self.zustand = -1
        
        _LOGGER.debug(f"State aktualisiert: {self._state}")
