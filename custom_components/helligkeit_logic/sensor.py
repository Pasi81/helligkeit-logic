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


def _safe_float(entity):
    if entity is None:
        return 0.0
    try:
        return float(entity.state)
    except (ValueError, TypeError):
        return 0.0


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add_entities):
    """Setup über ConfigFlow."""
    status_sensor = HelligkeitLogicSensor(hass, entry)
    add_entities(
        [
            status_sensor,
            HelligkeitLogicBrightnessSensor(hass, entry, status_sensor),
            HelligkeitLogicComputedValueSensor(hass, entry, status_sensor, "sonne1_b", "Sonne 1 berechnet"),
            HelligkeitLogicComputedValueSensor(hass, entry, status_sensor, "sonne2_b", "Sonne 2 berechnet"),
            HelligkeitLogicComputedValueSensor(hass, entry, status_sensor, "wolke1_b", "Wolke 1 berechnet"),
            HelligkeitLogicComputedValueSensor(hass, entry, status_sensor, "wolke2_b", "Wolke 2 berechnet"),
            HelligkeitLogicStatusFlagSensor(hass, entry, status_sensor, "wechsel_sonne", "Wechsel zu Sonne"),
            HelligkeitLogicStatusFlagSensor(hass, entry, status_sensor, "wechsel_wolken", "Wechsel zu Wolken"),
            HelligkeitLogicStatusValueSensor(hass, entry, status_sensor, "zustand", "Zustand"),
            HelligkeitLogicStatusValueSensor(hass, entry, status_sensor, "status", "Status"),
            HelligkeitLogicStateSensor(hass, entry, status_sensor, 0, "Nacht"),
            HelligkeitLogicStateSensor(hass, entry, status_sensor, 1, "Wolkig"),
            HelligkeitLogicStateSensor(hass, entry, status_sensor, 2, "Sonnig"),
        ],
        True,
    )


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
        self.calculated_brightness = 0.0
        self.status = 99
        self.sonne1_b = 0.0
        self.sonne2_b = 0.0
        self.wolke1_b = 0.0
        self.wolke2_b = 0.0
        self.last_change = datetime.now()
        self.zustand = 0
        self.wechsel_sonne = 0
        self.wechsel_wolken = 0

    def _get_delay_minutes(self, key, default):
        value = self.cfg.get(key, default)
        try:
            return max(float(value), 0.0)
        except (TypeError, ValueError):
            return float(default)

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
            "berechnete_helligkeit": self.calculated_brightness,
            "status": self.status,
            "zustand": self.zustand,
            "sonne1_b": self.sonne1_b,
            "sonne2_b": self.sonne2_b,
            "wolke1_b": self.wolke1_b,
            "wolke2_b": self.wolke2_b,
            "wechsel_zu_sonne": self.wechsel_sonne,
            "wechsel_zu_wolken": self.wechsel_wolken,
            "last_change": self.last_change.isoformat(),
        }

    async def async_update(self):
        h1_state = self.hass.states.get(self.cfg[CONF_SENSOR1])
        h2_state = self.hass.states.get(self.cfg[CONF_SENSOR2])
        elev_state = self.hass.states.get(self.cfg[CONF_ELEVATION])

        h1 = _safe_float(h1_state)
        h2 = _safe_float(h2_state)
        elev = _safe_float(elev_state)
        self.calculated_brightness = round((h1 + h2) / 2.0, 2)

        _LOGGER.debug(f"Sensoren: h1={h1}, h2={h2}, elev={elev}, berechnete_helligkeit={self.calculated_brightness}")

        sonne1 = float(self.cfg[CONF_SONNE1])
        wolke1 = float(self.cfg[CONF_WOLKE1])
        sonne2 = float(self.cfg[CONF_SONNE2])
        wolke2 = float(self.cfg[CONF_WOLKE2])

        _LOGGER.debug(f"Konfiguration: sonne1={sonne1}, wolke1={wolke1}, sonne2={sonne2}, wolke2={wolke2}")

        elev_max = 65.0
        elevmin = 1.0

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

        self.status = status
        self.sonne1_b = sonne1_b
        self.sonne2_b = sonne2_b
        self.wolke1_b = wolke1_b
        self.wolke2_b = wolke2_b

        now = datetime.now()
        diff = (now - self.last_change).total_seconds() / 60.0
        delay_sonne = self._get_delay_minutes(CONF_TIME_SONNE, 3)
        delay_wolke = self._get_delay_minutes(CONF_TIME_WOLKE, 40)

        _LOGGER.debug(
            "Status: %s, zustand: %s, diff_min: %.2f, delay_sonne: %.2f, delay_wolke: %.2f",
            status,
            self.zustand,
            diff,
            delay_sonne,
            delay_wolke,
        )

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

            if self.wechsel_wolken == 1 and diff >= delay_wolke:
                self.zustand = 1
                self.wechsel_wolken = 0
                self.wechsel_sonne = 0

            if self.zustand == 0:
                self.zustand = 1
                self.wechsel_wolken = 0
                self.wechsel_sonne = 0

        elif status == 2:
            if self.zustand == 1 and self.wechsel_sonne == 0:
                self.wechsel_sonne = 1
                self.wechsel_wolken = 0
                self.last_change = now

            if (self.wechsel_sonne == 1 and diff >= delay_sonne) or self.zustand == 0:
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


class HelligkeitLogicBrightnessSensor(SensorEntity):
    def __init__(self, hass, entry: ConfigEntry, status_sensor: HelligkeitLogicSensor):
        self.hass = hass
        self.entry = entry
        self.cfg = {**entry.data, **entry.options}
        self._status_sensor = status_sensor

        integration_name = self.cfg.get(CONF_NAME, DEFAULT_NAME)
        self._attr_name = f"{integration_name} Berechnete Helligkeit"
        self._attr_unique_id = f"{entry.entry_id}_brightness"
        self._attr_icon = "mdi:brightness-5"
        self._attr_native_unit_of_measurement = "lx"

    @property
    def native_value(self):
        return self._status_sensor.calculated_brightness

    async def async_update(self):
        await self._status_sensor.async_update()


class HelligkeitLogicComputedValueSensor(SensorEntity):
    def __init__(self, hass, entry: ConfigEntry, status_sensor: HelligkeitLogicSensor, attr_name, display_name):
        self.hass = hass
        self.entry = entry
        self.cfg = {**entry.data, **entry.options}
        self._status_sensor = status_sensor
        self._attr_name = display_name
        self._attr_unique_id = f"{entry.entry_id}_{attr_name}"
        self._attr_entity_id = f"sensor.{display_name.lower().replace(' ', '_').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')}"
        self._attr_icon = "mdi:calculator-variant"
        self._attr_native_unit_of_measurement = "lx"
        self._attr_name_for_entity = display_name
        self._attr_attr_name = attr_name

    @property
    def native_value(self):
        return getattr(self._status_sensor, self._attr_attr_name, 0.0)

    @property
    def extra_state_attributes(self):
        return {
            "zustand_text": self._status_sensor._state,
            "status": self._status_sensor.status,
            "zustand": self._status_sensor.zustand,
        }

    async def async_update(self):
        await self._status_sensor.async_update()


class HelligkeitLogicStatusFlagSensor(SensorEntity):
    def __init__(self, hass, entry: ConfigEntry, status_sensor: HelligkeitLogicSensor, attr_name, display_name):
        self.hass = hass
        self.entry = entry
        self.cfg = {**entry.data, **entry.options}
        self._status_sensor = status_sensor
        self._attr_name = f"{self.cfg.get(CONF_NAME, DEFAULT_NAME)} {display_name}"
        self._attr_unique_id = f"{entry.entry_id}_{attr_name}"
        self._attr_icon = "mdi:toggle-switch"
        self._attr_attr_name = attr_name

    @property
    def native_value(self):
        return getattr(self._status_sensor, self._attr_attr_name, 0)

    @property
    def extra_state_attributes(self):
        return {
            "zustand_text": self._status_sensor._state,
            "status": self._status_sensor.status,
            "zustand": self._status_sensor.zustand,
        }

    async def async_update(self):
        await self._status_sensor.async_update()


class HelligkeitLogicStatusValueSensor(SensorEntity):
    def __init__(self, hass, entry: ConfigEntry, status_sensor: HelligkeitLogicSensor, attr_name, display_name):
        self.hass = hass
        self.entry = entry
        self.cfg = {**entry.data, **entry.options}
        self._status_sensor = status_sensor
        self._attr_name = f"{self.cfg.get(CONF_NAME, DEFAULT_NAME)} {display_name}"
        self._attr_unique_id = f"{entry.entry_id}_{attr_name}"
        self._attr_icon = "mdi:information-outline"
        self._attr_attr_name = attr_name

    @property
    def native_value(self):
        return getattr(self._status_sensor, self._attr_attr_name, 0)

    @property
    def extra_state_attributes(self):
        return {
            "zustand_text": self._status_sensor._state,
            "status": self._status_sensor.status,
            "zustand": self._status_sensor.zustand,
        }

    async def async_update(self):
        await self._status_sensor.async_update()


class HelligkeitLogicStateSensor(SensorEntity):
    def __init__(self, hass, entry: ConfigEntry, status_sensor: HelligkeitLogicSensor, state_value, state_name):
        self.hass = hass
        self.entry = entry
        self.cfg = {**entry.data, **entry.options}
        self._status_sensor = status_sensor
        self._state_value = state_value
        self._state_name = state_name

        integration_name = self.cfg.get(CONF_NAME, DEFAULT_NAME)
        self._attr_name = f"{integration_name} {state_name}"
        self._attr_unique_id = f"{entry.entry_id}_{state_name.lower()}"
        if state_value == 0:
            self._attr_icon = "mdi:weather-night"
        elif state_value == 1:
            self._attr_icon = "mdi:weather-cloudy"
        else:
            self._attr_icon = "mdi:weather-sunny"

    @property
    def native_value(self):
        return 1 if self._status_sensor.zustand == self._state_value else 0

    @property
    def extra_state_attributes(self):
        return {
            "zustand_text": self._status_sensor._state,
            "status": self._status_sensor.zustand,
        }

    async def async_update(self):
        await self._status_sensor.async_update()
