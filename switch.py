"""Platform for sensor integration."""
from __future__ import annotations

from .maxem import MaxemCloud
import logging
import voluptuous as vol 
from datetime import timedelta

from homeassistant.components.switch import (PLATFORM_SCHEMA)
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.helpers.entity import Entity

from homeassistant.components.switch import (
    SwitchEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

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
    
    add_entities([ MaxemSwitch(cloud)])

class MaxemSwitch(SwitchEntity):
    """Representation of a Maxem chargerpoll switch."""
    _attr_unique_id = "switches.maxem.charger"
    _attr_name = "Maxem car charger switch"
    _attr_device_class: SwitchDeviceClass.OUTLET

    def __init__(self, cloud):
        """Initialise of the switch."""
        # TODO: Device class etc.
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
        