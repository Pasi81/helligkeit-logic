from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from datetime import datetime
from .const import (
    CONF_SENSOR1,
    CONF_SENSOR2,
    CONF_ELEVATION,
    CONF_SONNE1,
    CONF_WOLKE1,
    CONF_SONNE2,
    CONF_WOLKE2,
    CONF_TIME_SONNE,
    CONF_TIME_WOLKE,
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities):
    """Setup über ConfigFlow."""
    add_entities([HelligkeitLogicSensor(hass, entry.data)], True)


class HelligkeitLogicSensor(SensorEntity):
    _attr_name = "Helligkeit Logik"
    _attr_unique_id = "helligkeit_logic_main"

    def __init__(self, hass, cfg):
        self.hass = hass
        self.cfg = cfg

        self._state = "Unbekannt"
        self.last_change = datetime.now()
        self.zustand = 0
        self.wechsel_sonne = 0
        self.wechsel_wolken = 0

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {
            "zustand": self.zustand,
            "wechsel_zu_sonne": self.wechsel_sonne,
            "wechsel_zu_wolken": self.wechsel_wolken,
            "last_change": self.last_change.isoformat(),
        }

    async def async_update(self):
        h1 = float(self.hass.states.get(self.cfg[CONF_SENSOR1]).state or 0)
        h2 = float(self.hass.states.get(self.cfg[CONF_SENSOR2]).state or 0)
        elev = float(self.hass.states.get(self.cfg[CONF_ELEVATION]).state or 0)

        sonne1 = self.cfg[CONF_SONNE1]
        wolke1 = self.cfg[CONF_WOLKE1]
        sonne2 = self.cfg[CONF_SONNE2]
        wolke2 = self.cfg[CONF_WOLKE2]

        elev_max = 65

        if elev >= 2:
            sonne1_b = sonne1 * elev / elev_max
            sonne2_b = sonne2 * elev / elev_max
            wolke1_b = wolke1 * elev / elev_max
            wolke2_b = wolke2 * elev / elev_max
        else:
            sonne1_b = sonne1
            sonne2_b = sonne2
            wolke1_b = wolke1
            wolke2_b = wolke2

        if h1 < 10 and h2 < 5:
            status = 0
        elif h1 > 100 and h2 > 50 and elev >= 2:
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
