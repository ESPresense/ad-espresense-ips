# ESPresense - Ips Solver

Appdaemon app that attempts to solve indoor position (x,y,z) with multiple ESPresense stations using multilateralization.

This uses numpy/scipy with a "Nelder-Mead" minimize of total error.  Error is the amount of difference a guessed position has between the calced distance to a base station and the actual measured distance to the base station (via ESPresense rssi).  Various x,y,z are tried and the position with the least error is where we guess it is.

This requires at least 3 ESPresense nodes that can get a "fix" on the particular device.  The more devices the better.  To get a decently accurate position you need at least 5 or 6.  But this can find the location of something even if the particular room doesn't have a base station (You can put nodes on the perimeter of your house instead of the "center" of rooms).  We need futher work to actually determine if the item is actually in a particular room (we'll need some kind of floorplan).

## Installation

For this to work you need to add this to your appdaemon Add-On config:
```yaml
system_packages:
  - py3-numpy
  - py3-scipy
python_packages:
  - numpy
  - scipy
```

You need to have both MQTT and HASS added to `appdaemon.yaml`:

```yaml
appdaemon:
  time_zone: America/New_York
  latitude: 40.234223
  longitude: -75.23456
  elevation: 146
  plugins:
    HASS:
      type: hass
      ha_url: "http://192.168.128.8:8123"
      token: "xxxx"
      namespace: default
      app_init_delay: 30
      appdaemon_startup_conditions:
        delay: 30
    MQTT:
      type: mqtt
      client_host: 192.168.128.9
      namespace: mqtt
      birth_topic: appdaemon
      will_topic: appdaemon
```

Finally you need something like this in your `app.yaml`:
```yaml
ESPresenseIps:
  module: espresense-ips
  class: ESPresenseIps
  pluggins:
    - HASS
    - MQTT
  rooms:
    garage: [0, 8, 0.4]
    office: [5, 1.5, 0.5]
    family: [0, 0, 0]
    kitchen: [8, 6, 0.5]
    dining: [16, 0, 0.5]
  devices:
  - id: tile:xxx
    name: AirPods
    timeout: 30
    away_timeout: 120
  - id: tile:xxx
    name: Wallet
    timeout: 30
    away_timeout: 120
  - id: apple:1005:9-26
    name: Watch
    timeout: 30
    away_timeout: 120
```
