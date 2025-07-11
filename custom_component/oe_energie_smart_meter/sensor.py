import logging
from datetime import datetime, timedelta
import httpx

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

#from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=1)

# 💡 Sensor-Mapping: key → (name, unit, icon)
SENSOR_KEYS = {
    "1-0:1.8.0": ("Wirkenergie Bezug (1.8.0)", "kWh", "mdi:lightning-bolt"),
    "1-0:2.8.0": ("Wirkenergie Lieferung (2.8.0)", "kWh", "mdi:lightning-bolt"),
    "1-0:1.7.0": ("Wirkleistung Bezug (1.7.0)", "W", "mdi:flash"),
    "1-0:2.7.0": ("Wirkleistung Lieferung (2.7.0)", "W", "mdi:flash"),
#    "0-0:2.0.0": ("Softwareversion", None, "mdi:git"),
    "0-0:96.1.0": ("Zählernummer (96.1.0)", None, "mdi:counter"),
    "name": ("Gerätename", None, "mdi:form-textbox"),
    "sma_time": ("SMA-Laufzeit", None, "mdi:clock"),
    "0-0:1.0.0": ("Zählerdatum", None, "mdi:clock")
}

TIME_KEYS = ["0-0:1.0.0"]

# 🚀 Sensor-Setup
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    coordinator = SmartMeterDataCoordinator(hass)
# Kein erster Refresh hier! Der Sensor holt sich beim ersten Zugriff die Daten.
#    await coordinator.async_config_entry_first_refresh()

    entities = [
        SmartMeterSensor(coordinator, key, name, unit, icon)
        for key, (name, unit, icon) in SENSOR_KEYS.items()
    ]
    entities.append(SmartMeterNetPowerSensor(coordinator))
    async_add_entities(entities)
#    async_add_entities(entities, True)

# 🔄 Datenkoordinator
class SmartMeterDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass):
        super().__init__(
            hass,
            _LOGGER,
            name="oe_energie_smart_meter",
            update_interval=SCAN_INTERVAL
        )

    async def _async_update_data(self):
        try:
            async with httpx.AsyncClient(verify=False, timeout=5.0) as client:
                response = await client.get(
                    "https://YOUR_IP_HERE/api/v1/measurement",
                    headers={"Authorization": "TOKEN YOUR_TOKEN_HERE"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as err:
            raise UpdateFailed(f"Fehler beim Abrufen: {err}")

class SmartMeterNetPowerSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Nettoleistung"
        self._attr_unique_id = "smart_meter_net_power"
        self._attr_device_class = "power"
        self._attr_state_class = "measurement"
        self._attr_native_unit_of_measurement = "W"
        self._attr_icon = "mdi:flash"

    @property
    def native_value(self):
        data = self.coordinator.data
        bezug = None
        einspeisung = None

        if isinstance(data.get("1-0:1.7.0"), dict):
            bezug = data["1-0:1.7.0"].get("value")
        if isinstance(data.get("1-0:2.7.0"), dict):
            einspeisung = data["1-0:2.7.0"].get("value")

        try:
            b = float(bezug or 0)
            e = float(einspeisung or 0)
            return round(b - e, 2)
        except Exception:
            return None

class SmartMeterSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key, name, unit, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"smart_meter_{key.replace(':', '_')}"
        self._attr_icon = icon
        self._attr_should_poll = False

        # Einheiten & Messcharakteristik
        self._attr_native_unit_of_measurement = unit

        if key in ["1-0:1.7.0", "1-0:2.7.0"]:
            self._attr_device_class = "power"
            self._attr_state_class = "measurement"
        elif key in ["1-0:1.8.0", "1-0:2.8.0"]:
            self._attr_device_class = "energy"
            self._attr_state_class = "total_increasing"
#        elif key == "0-0:2.0.0":
#            self._attr_device_class = "voltage"
#            self._attr_state_class = "measurement"

    @property
    def native_value(self):
        raw = self.coordinator.data.get(self._key)
        if raw is None:
            return None

        # Uptime als Sonderfall: sma_time
        if self._key == "sma_time":
            try:
                total_seconds = int(float(raw))
                days = total_seconds // 86400
                hours = (total_seconds % 86400) // 3600
                minutes = (total_seconds % 3600) // 60
                return f"{days} Tage {hours} Std {minutes} Min"
            except Exception:
                return raw

        # Zeitformat für Zeitstempel-Sensoren
        if isinstance(raw, dict):
            value = raw.get("value")
            if self._key == "0-0:96.1.0":
                return value  # 🔍 Zähler-ID als String anzeigen
        
            timestamp = raw.get("time", 0)

            if self._key == "0-0:1.0.0" and isinstance(timestamp, int) and timestamp > 0:
                try:
                    from datetime import datetime
                    dt = datetime.fromtimestamp(timestamp)
                    return dt.strftime("%d.%m.%Y")  # 👈 zeigt z. B. "10.07.2025"
                except Exception:
                    return value

            if isinstance(value, (int, float)):
                if self._key in ["1-0:1.8.0", "1-0:2.8.0"]:
                    # 🔄 Umrechnung von Wh → kWh
                    return round(float(value) / 1000, 3)
                return float(value)

        if isinstance(raw, (int, float)):
            return float(raw)

        return raw
