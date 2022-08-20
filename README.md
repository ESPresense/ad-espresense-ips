# ESPresense - Ips Solver

Appdaemon app that attempts to solve indoor position (x,y,z) with multiple ESPresense stations using multilateralization.

This uses numpy/scipy with a "Nelder-Mead" minimize of total error.  Error is the amount of difference a guessed position has between the calced distance to a base station and the actual measured distance to the base station (via ESPresense rssi).  Various x,y,z are tried and the position with the least error is where we guess it is.

This requires at least 3 ESPresense nodes that can get a "fix" on the particular device.  The more devices the better.  To get a decently accurate position you need at least 5 or 6.  But this can find the location of something even if the particular room doesn't have a base station (You can put nodes on the perimeter of your house instead of the "center" of rooms).  To actually determine if an item is in a particular room, you have to write down two opposite coordinates of a room to check if the items coordinates are within these boundaries.

## Installation

For this to work you need to add this to your appdaemon Add-On config:
```yaml
init_commands:
  - apk add --update python3 python3-dev py3-numpy py3-scipy
python_packages: []
system_packages: []
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
    office: [0, 0, 0]
    living_room: [9.44, 0, 0]
    bedroom: [9.44, 6.98, 0]
    kitchen: [3.17, 6.98, 0]
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
  roomplans:
  - name: office
    points:
    - x: 0.0
      y: 0.0
    - x: 0.0
      y: 3.17
    - x: 2.56
      y: 3.17
    - x: 2.56
      y: 0.0
  - name: living_room
    points:
    - x: 3.17
      y: 0.0
    - x: 3.17
      y: 3.33
    - x: 9.44
      y: 3.33
    - x: 9.44
      y: 0.0
  - name: bedroom
    points:
    - x: 6.24
      y: 4.19
    - x: 6.24
      y: 6.98
    - x: 9.44
      y: 6.98
    - x: 9.44
      y: 4.19
  - name: kitchen
    points:
    - x: 5.41
      y: 3.32
    - x: 5.41
      y: 9.5
    - x: 3.0
      y: 9.5
    - x: 0.0
      y: 3.32
```

## [FloorPlan creator](https://github.com/stan69b/ESPresenseIPS-Floorplan-Creator)

This application allows one to :

* Create a floorplan/Rooms easily
* Name each room
* Add your ESP32 devices inside each room
* Add z values for ESP32's, coverage radius and coverage circle color
* Show coverage of each ESP32 devices to see the exact coverage in each rooms
* Show coverage of ESP32 while you place them so you can find what are the best places.
* Export your floorplan to yaml format with room coordinates and esp32 devices coordinates (just copy past inside app.js)


