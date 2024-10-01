"""Platform for sensor integration."""
from __future__ import annotations

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
    
    cloud = MaxemCloud(email, password, maxemBoxID);
    
    add_entities([ MaxemSwitch(cloud), MaxemHomeSensor(cloud), MaxemChargerSensor(cloud) ], update_before_add=True)

# MAXEM_API: 
import requests
import logging
import json
import time

class MaxemCloud:
    def __init__(self, email, password, maxemBoxID):
        """Initialise of the switch."""
        self._email = email
        self._password = password
        self._maxemBoxID = maxemBoxID
        self._state = None

        self._sess = requests.Session()

        init = self._sess.get('https://my.maxem.io')
        auth = self._sess.post('https://my.maxem.io/login', 
            data={"identifier": self._email, "password": self._password,"login":""},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    def getHomeKwh(self) -> float:
        try:
            startCurrentHour = int(time.time() * 1000)
            minute = 60000
            startCurrentHour -= startCurrentHour % minute
            startPrevHour = startCurrentHour - minute

            urlHome = 'https://my.maxem.io/energyquery?maxemId=MX5-1-H-000237&collectionName=Home_energy&period=range-minutes&startTime=' + str(startPrevHour) + '&endTime=' + str(startCurrentHour - 1)
            # urlSess = 'https://my.maxem.io/energyquery?maxemId=' + self._maxemBoxID + '&collectionName=sessions&period=range-minutes&startTime=' + str(startPrevHour) + '&endTime=' + str(startCurrentHour - 1)

            homeData = self._sess.get(urlHome);
            # chargerData = self._sess.get(urlSess);
                
            if homeData.status_code != 200:
                self._sess = requests.Session()

                init = self._sess.get('https://my.maxem.io')
                auth = self._sess.post('https://my.maxem.io/login', 
                    data={"identifier": self._email, "password": self._password,"login":""},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                homeData = self._sess.get(urlHome);

                if homeData.status_code != 200:
                    _LOGGER.warning(
                        "Invalid status_code from Maxem: %s (%s)",
                        response.status_code,
                        self._attr_name,
                    )
                    return

            homeJson = homeData.json();
            # chargerJson = chargerData.json();

            # [{"start":{"time":1727197200000},"delta":{"value":0.45665764799999997}}]
            # 
            homeKwh = float(homeJson[0]['delta']['value']);
            # chargerKwh = float(chargerJson[0]['delta']['value']);
            
            return homeKwh

        except ValueError:
            _LOGGER.error("Maxem API error: " + ValueError)
            return ValueError

    def getChargerKwh(self) -> float:
        try:
            startCurrentHour = int(time.time() * 1000)
            minute = 60000
            startCurrentHour -= startCurrentHour % minute
            startPrevHour = startCurrentHour - minute

            # urlHome = 'https://my.maxem.io/energyquery?maxemId=MX5-1-H-000237&collectionName=Home_energy&period=range-minutes&startTime=' + str(startPrevHour) + '&endTime=' + str(startCurrentHour - 1)
            urlSess = 'https://my.maxem.io/energyquery?maxemId=' + self._maxemBoxID + '&collectionName=sessions&period=range-minutes&startTime=' + str(startPrevHour) + '&endTime=' + str(startCurrentHour - 1)

            # homeData = self._sess.get(urlHome);
            chargerData = self._sess.get(urlSess);
                
            if chargerData.status_code != 200:
                self._sess = requests.Session()

                init = self._sess.get('https://my.maxem.io')
                auth = self._sess.post('https://my.maxem.io/login', 
                    data={"identifier": self._email, "password": self._password,"login":""},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                chargerData = self._sess.get(urlSess);

                if chargerData.status_code != 200:
                    _LOGGER.warning(
                        "Invalid status_code from Maxem: %s (%s)",
                        response.status_code,
                        self._attr_name,
                    )
                    return

            # homeJson = homeData.json();
            chargerJson = chargerData.json();

            # [{"start":{"time":1727197200000},"delta":{"value":0.45665764799999997}}]
            # 
            # homeKwh = float(homeJson[0]['delta']['value']);
            chargerKwh = float(chargerJson[0]['delta']['value']);
            
            return chargerKwh

        except ValueError:
            _LOGGER.error("Maxem API error: " + ValueError)
            return ValueError

    def setChargerSwitch(self, isOn) -> bool:
        try:
            urlPause = 'https://my.maxem.io/remotechargepoint/pauseAllChargePoints?maxemId=' + self._maxemBoxID
            urlStart = 'https://my.maxem.io/remotechargepoint/unPauseAllChargePoints?maxemId=' + self._maxemBoxID
            
            url = urlPause;
            if isOn:
                url = urlStart;

            response = self._sess.get(url);
                
            if response.status_code != 200:
                self._sess = requests.Session()

                init = self._sess.get('https://my.maxem.io')
                auth = self._sess.post('https://my.maxem.io/login', 
                    data={"identifier": self._email, "password": self._password,"login":""},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response = self._sess.get(url);

                if response.status_code != 200:
                    _LOGGER.warning(
                        "Invalid status_code from Maxem: %s (%s)",
                        response.status_code,
                        self._attr_name,
                    )
                    return False

            return True

        except ValueError:
            _LOGGER.error("Maxem API error: " + ValueError)
            return False
            
class MaxemSwitch(Entity):
    """Representation of a Maxem chargerpoll switch."""

    def __init__(self, cloud):
        """Initialise of the switch."""
        self._cloud = cloud
        self._state = None

    def turn_on(self, **kwargs):
        """Send the on command."""
        self._cloud.setChargerSwitch(True);
        self._state = True
        _LOGGER.debug("Maxem ===> Enable charging for: %s", self._maxemBoxID)   

    def turn_off(self, **kwargs):
        """Send the off command."""
        self._cloud.setChargerSwitch(False);
        self._state = False
        _LOGGER.debug("Maxem ===> Disable charging for: %s", self._maxemBoxID)

    @property
    def is_on(self):
        """Get whether the switch is in on state."""
        return self._state == True # STATE_ON
        
class MaxemHomeSensor(SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(cloud):
        self._cloud = cloud

    def update(self) -> None:
        value = self._cloud.getHomeKwh()
        self._attr_native_value = value

class MaxemChargerSensor(SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(cloud):
        self._cloud = cloud

    def update(self) -> None:
        value = self._cloud.getChargerKwh()
        self._attr_native_value = value

