## App configuration

```yaml
espresense-position:
  module: espresense-position
  class: ESPrescencePosition
  pluggins:
  - HASS
  - MQTT
  rooms_topic: espresense/rooms
  ips_topic: ips
  location_topic: location
  rooms:
    master: [0, 6, 4]
    garage: [0, 8, 0.5]
    office: [5, 1.5, 0.5]
    family: [0, 0, 0]
    kitchen: [8, 6, 0.5]
    dining: [16, 0, 0.5]
  devices:
    - id: apple:1005:9-26
      name: Darrell Watch
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
