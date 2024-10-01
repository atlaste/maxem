"""Platform for sensor integration."""
from __future__ import annotations

from .maxem import MaxemCloud
import logging
import voluptuous as vol 
from datetime import timedelta

from homeassistant.components.switch import (PLATFORM_SCHEMA)
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.helpers.entity import Entity

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfElectricCurrent, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=60)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required('email'): cv.string, 
    vol.Required('password'): cv.string, 
    vol.Required('maxemBoxID'): cv.string,
})

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    # Assign configuration variables.
    # The configuration check takes care they are present.
    _LOGGER.info("Maxem ====> Setup_platform started")

    email = config.get('email')
    password  = config.get('password')
    maxemBoxID = config.get('maxemBoxID')
    
    cloud = MaxemCloud(email, password, maxemBoxID, _LOGGER);
    
    add_entities([ MaxemHomeSensor(cloud), MaxemChargerSensor(cloud) ], update_before_add=True)

class MaxemHomeSensor(SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_unique_id = "sensors.maxem.home"
    _attr_name = "Maxem home sensor"

    def __init__(self, cloud):
        self._cloud = cloud

    def update(self) -> None:
        value = self._cloud.getHomeKwh()
        self._attr_native_value = value[0]
        if len(value)==2:
            self._attr_last_reset = dt_util.utcnow()

class MaxemChargerSensor(SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_unique_id = "sensors.maxem.charger"
    _attr_name = "Maxem car charger sensor"

    def __init__(self, cloud):
        self._cloud = cloud

    def update(self) -> None:
        value = self._cloud.getChargerKwh()
        self._attr_native_value = value[0]

