## App configuration

```yaml
espresense-position:
  module: espresense-position
  class: ESPrescencePosition
  pluggins:
  - HASS
  - MQTT
  channel: room_presence
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
   - apple:1005:9-26
```

key | optional | type | default | description
-- | -- | -- | -- | --
`module` | False | string | | The module name of the app.
`class` | False | string | | The name of the Class.
`channel` | True | string | `room_presence`| The base mqtt channel for ESPresense
`ips_topic`| True | string | `ips` | suffix for ips
`location_topic`| True | string | `location` | suffix for location
`rooms`| False | complex | | names and coordinates of each room
`devices`| False | string array | | All the devices you want to attempt to locate