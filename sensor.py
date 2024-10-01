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
    homeLastKwh = 0;
    chargerLastKwh = 0;

    def __init__(self, email, password, maxemBoxID):
        """Initialise of the switch."""
        self._email = email
        self._password = password
        self._maxemBoxID = maxemBoxID
        self._state = None
        self._sess = requests.Session()

    def login(self):
        _LOGGER.info("Login on API")
        init = self._sess.get('https://my.maxem.io')
        auth = self._sess.post('https://my.maxem.io/login', 
            data={"identifier": self._email, "password": self._password,"login":""},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
    def getData(self, url) -> list[float]:
        try:
            responseData = self._sess.get(url);
                    
        except http.client.RemoteDisconnected:
            self.login();
            responseData = self._sess.get(url);
            
        try:
            if responseData.status_code != 200:
                self.login();
                responseData = self._sess.get(url);

                if responseData.status_code != 200:
                    _LOGGER.warning(
                        "Invalid status_code from Maxem: %s (%s)",
                        response.status_code,
                        self._attr_name,
                    )
                    return

            responseJson = responseData.json();

            # [{"start":{"time":1727197200000},"delta":{"value":0.45665764799999997}}]
            # 
            curKwh = 0;
            prevKwh = 0;
            for x in responseJson:
                prevKwh = curKwh;
                curKwh = float(x['delta']['value']);
                
            return [prevKwh, curKwh];
            
        except ValueError:
            _LOGGER.error("Maxem API error: " + ValueError)
            return ValueError

    def getHomeKwh(self) -> list[float]:
        startCurrentHour = int(time.time() * 1000)
        hour = 3600000
        startCurrentHour -= startCurrentHour % hour
        startPrevHour = startCurrentHour - hour

        url = 'https://my.maxem.io/energyquery?maxemId=' + self._maxemBoxID + '&collectionName=Home_energy&period=range-hours&startTime=' + str(startPrevHour) + '&endTime=' + str(startCurrentHour - 1)
        tmp = self.getData(url)
        
        if (self.homeLastKwh == tmp[0]):
            return [tmp[1]];
        else:
            self.homeLastKwh = tmp[0];
            return tmp;
            
    def getChargerKwh(self) -> float:
        startCurrentHour = int(time.time() * 1000)
        hour = 3600000
        startCurrentHour = startCurrentHour - (startCurrentHour % hour) + hour
        startPrevHour = startCurrentHour - hour * 2

        url = 'https://my.maxem.io/energyquery?maxemId=' + self._maxemBoxID + '&collectionName=sessions&period=range-hours&startTime=' + str(startPrevHour) + '&endTime=' + str(startCurrentHour - 1)
        tmp = self.getData(url)
        
        if (self.chargerLastKwh == tmp[0]):
            return [tmp[1]];
        else:
            self.chargerLastKwh = tmp[0];
            return tmp;

    def setChargerSwitch(self, isOn) -> bool:
        try:
            urlPause = 'https://my.maxem.io/remotechargepoint/pauseAllChargePoints?maxemId=' + self._maxemBoxID
            urlStart = 'https://my.maxem.io/remotechargepoint/unPauseAllChargePoints?maxemId=' + self._maxemBoxID
            
            url = urlPause;
            if isOn:
                url = urlStart;

            try:
                response = self._sess.get(url);
                        
            except http.client.RemoteDisconnected:
                self.login();
                response = self._sess.get(url);
                
                
            if response.status_code != 200:
                self.login();
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
        # TODO: Device class etc.
        self._cloud = cloud
        self._state = None
        self._attr_unique_id = "switches.maxem.charger"
        self._attr_name = "Maxem car charger switch"

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
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_unique_id = "sensors.maxem.home"
    _attr_name = "Maxem home sensor"

    def __init__(self, cloud):
        self._cloud = cloud

    def update(self) -> None:
        value = self._cloud.getHomeKwh()
        self._attr_native_value = value[0] * 1000

class MaxemChargerSensor(SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL
    _attr_unique_id = "sensors.maxem.charger"
    _attr_name = "Maxem car charger sensor"

    def __init__(self, cloud):
        self._cloud = cloud

    def update(self) -> None:
        value = self._cloud.getChargerKwh()
        self._attr_native_value = value[0] * 1000

