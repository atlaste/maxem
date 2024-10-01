
# MAXEM_API: 
import requests
import logging
import json
import time
import http

class MaxemCloud:
    homeLastKwh = 0;
    chargerLastKwh = 0;
    requestCount = 0;

    def __init__(self, email, password, maxemBoxID, logger):
        """Initialise of the switch."""
        self._email = email
        self._password = password
        self._maxemBoxID = maxemBoxID
        self._state = None
        self._LOGGER = logger
        self.login();

    def login(self):
        self._LOGGER.warning("Login on API");
        self._sess = requests.Session();
        init = self._sess.get('https://my.maxem.io');
        auth = self._sess.post('https://my.maxem.io/login', 
            data={"identifier": self._email, "password": self._password,"login":""},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        );

    def getData(self, url) -> list[float]:
        self.requestCount = self.requestCount + 1;
        if (self.requestCount == 13):
            self.login();
            self.requestCount = 0;
    
        try:
            responseData = self._sess.get(url);
                    
        except requests.ConnectionException:
            self.login();
            responseData = self._sess.get(url);
            
        try:
            if responseData.status_code != 200:
                self.login();
                responseData = self._sess.get(url);

                if responseData.status_code != 200:
                    self._LOGGER.warning(
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
            self._LOGGER.error("Maxem API error: " + ValueError)
            return ValueError

    def getHomeKwh(self) -> list[float]:
        startCurrentHour = int(time.time() * 1000)
        hour = 3600000
        startCurrentHour -= startCurrentHour % hour
        startPrevHour = startCurrentHour - hour

        url = 'https://my.maxem.io/energyquery?maxemId=' + self._maxemBoxID + '&collectionName=Home_energy&period=range-hours&startTime=' + str(startPrevHour) + '&endTime=' + str(startCurrentHour - 1)
        tmp = self.getData(url)
        
        if (self.chargerLastKwh == 0):
            self.chargerLastKwh = tmp[0];
        
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
        
        if (self.chargerLastKwh == 0):
            self.chargerLastKwh = tmp[0];
        
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
                    self._LOGGER.warning(
                        "Invalid status_code from Maxem: %s (%s)",
                        response.status_code,
                        self._attr_name,
                    )
                    return False

            return True

        except ValueError:
            self._LOGGER.error("Maxem API error: " + ValueError)
            return False
