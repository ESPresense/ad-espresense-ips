# ESPresense - Ips Solver

Appdaemon app that attempts to solve indoor position (x,y,z) with multiple ESPresense stations using trilateralization

For this to work you need to add this to your appdaemon Add-On config:
```yaml
system_packages:
  - py3-numpy
  - py3-scipy
python_packages:
  - numpy
  - scipy
```

You need to have both MQTT and HASS added to appdaemon as well:

```yaml
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

Finally you need something like this in your apps:
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
