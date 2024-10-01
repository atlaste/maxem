# What it is

Implementation of the Maxem energy cloud solutions for Home Assistant.

# How to install

1. Set "advanced modes" in your user settings.
2. Create a 'custom_integrations' folder
3. Create a 'maxem' folder inside 'custom_integrations'
4. Throw these files in there
4. Edit the configuration.yaml

```yaml

sensor:
  - platform: Maxem
    email: "your@email.com"
    password: "your_password"
    maxemBoxID: "MX5-X-X-123456"
```
5. Restart the system

# Maxem support

This is very unofficial, very much a Work In Progress. Take it at your own risk. 

Ideally, I'd like Maxem to just support this. They know their API, and can ensure stability. I cannot do either.

I reached out to Maxem, who were of course more than willing to help out...

> Good afternoon,
>
> Thank you for your question. Unfortunately, we do not have an API that can connect to the Home Assistant. Also, unfortunately there are no plans to implement this in the future.
> Hopefully I have informed you sufficiently with this. Should you have any further questions, please let me know.
>
> Kind regards,

The code here is not following all the rules that HA has spelled out. I'm not good with Python, nor do I strive to be, so *please* if you plan to fix things, let me know, and I'll happily take on PR's.
