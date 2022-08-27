## App configuration

```yaml
ESPresenseIps:
  module: espresense-ips
  class: ESPresenseIps
  pluggins:
    - HASS
    - MQTT
  draw_interval: 5
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
```

key | optional | type | default | description
-- | -- | -- | -- | --
`module` | False | string | | The module name of the app.
`class` | False | string | | The name of the Class.
`rooms_topic` | True | string | `espresense/rooms`| The base mqtt channel for ESPresense
`ips_topic`| True | string | `espresense/ips` | suffix for ips
`location_topic`| True | string | `espresense/location` | suffix for location
`rooms`| False | dict | | names and coordinates of each room
`devices`| False | array dict | | All the devices you want to attempt to locate
`draw_interval`| True | int | | The time to wait between drawing the scene. If not included the drawing is disabled
