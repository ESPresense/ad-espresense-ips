# ESPresense - Ips Solver

Appdaemon app that attempts to solve indoor position (x,y,z) with multiple ESPresense stations using multilateralization.

This uses numpy/scipy with a "Nelder-Mead" minimize of total error.  Error is the amount of difference a guessed position has between the calced distance to a base station and the actual measured distance to the base station (via ESPresense rssi).  Various x,y,z are tried and the position with the least error is where we guess it is.

This requires at least 3 ESPresense nodes that can get a "fix" on the particular device.  The more devices the better.  To get a decently accurate position you need at least 5 or 6.  But this can find the location of something even if the particular room doesn't have a base station (You can put nodes on the perimeter of your house instead of the "center" of rooms).  To actually determine if an item is in a particular room, you have to write down two opposite coordinates of a room to check if the items coordinates are within these boundaries.

## Installation

For this to work you need to add this to your appdaemon Add-On config:
![image](https://user-images.githubusercontent.com/1491145/187983602-76d77f8b-a55c-4bcb-8d8f-a001f51b3dcc.png)

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
  draw_interval: 3
  rooms:
    office: [0, 0.864, 0.965]
    living_room: [9.83, 0.584, 1.224]
    living_room_2: [3.175, 1.499, 1.727]
    bedroom: [9.398, 5.817, 1.32]
    kitchen: [3.772, 7.417, 0.838]
    kitchen_2: [1.049, 4.56, 1.930]
  devices:
  - id: iBeacon:xxxx
    name: Phone
    timeout: 30
    away_timeout: 120
  roomplans:
  - name: office
    points:
    - x: 0.0
      y: 0.0
    - x: 3.175
      y: 0
    - x: 3.175
      y: 2.225
    - x: 1.87
      y: 3.658
    - x: 0
      y: 1.956
  - name: living_room
    points:
    - x: 3.175
      y: 0
    - x: 9.449
      y: 0
    - x: 9.449
      y: 3.327
    - x: 2.171
      y: 3.327
    - x: 3.175
      y: 2.225
  - name: bedroom
    points:
    - x: 5.41
      y: 6.985
    - x: 5.41
      y: 6.121
    - x: 6.248
      y: 6.121
    - x: 6.248
      y: 4.191
    - x: 9.398
      y: 4.191
    - x: 9.398
      y: 6.985
  - name: kitchen
    points:
    - x: 1.081
      y: 2.94
    - x: 1.87
      y: 3.658
    - x: 2.171
      y: 3.327
    - x: 5.41
      y: 3.327
    - x: 5.41
      y: 6.985
    - x: 4.166
      y: 6.985
    - x: 2.917
      y: 8.356
    - x: 0.006
      y: 5.706
    - x: 1.169
      y: 4.428
    - x: 0.38
      y: 3.71

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


