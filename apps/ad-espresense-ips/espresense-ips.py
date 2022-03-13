"""

Credits to:

https://github.com/glucee/Multilateration/blob/master/Python/example.py

Uses:

https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
https://docs.scipy.org/doc/scipy/reference/optimize.minimize-neldermead.html#optimize-minimize-neldermead

"""

import appdaemon.plugins.hass.hassapi as hass
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize
import numpy as np
import json
import re
import datetime
import io

class ESPresenseIps(hass.Hass):
    def gen_image(self, kwargs):

        devs = [{'x0':x.get("x0",None),"name":x.get("name", "none")} for x in self.devices.values() if ('x0' in x and 'name' in x)]
        print(devs)

        x = np.asarray([d.get('x0', None)[0] for d in devs])
        y = np.asarray([d.get('x0', None)[1] for d in devs])
        s = np.asarray([d.get('x0', None)[2] for d in devs])

        for d in self.devices:
            name = self.devices[d].get("name", "")
            # self.log(f"{d} {name}")

        self.log(f"Plotting")
        fix, ax = plt.subplots()
        prop_cycle = plt.rcParams['axes.prop_cycle']
        colors = prop_cycle.by_key()['color']

        for d, color in zip(devs, colors):
            ax.scatter(x=d.get('x0', None)[0], y=d.get('x0', None)[1],s=d.get('x0', None)[1], label=d.get('name', None), color=color)

        plt.title('ESPresense Locations')
        plt.legend(loc=2)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        self.mqtt.mqtt_publish(f"{self.args.get('images_topic', 'espresense/images')}/map", buf.getvalue());
        buf.close()
        self.log(f"Plotted")

    def initialize(self):
        self.devices = {}
        for device in self.args["devices"]:
          self.devices.setdefault(device["id"],{})["name"]=device["name"]
        self.mqtt = self.get_plugin_api("MQTT")
        self.mqtt.mqtt_publish(f"{self.args.get('hass_topic', 'homeassistant')}/camera/espresense_map/config", json.dumps({"~":f"{self.args.get('images_topic', 'espresense/images')}/map", "topic":"~", "icon":"mdi:map-marker-down", "json_attributes_topic":"~/attributes", "name":"Map", "unique_id": f"espresense_map"}), retain = True)
        self.run_every(self.gen_image, "now+1", 15)
        for room, pos in self.args["rooms"].items():
            t = f"{self.args.get('rooms_topic', 'espresense/rooms')}/{room}"
            self.log(f"Subscribing to topic {t}")
            self.mqtt.mqtt_unsubscribe(t)
            self.mqtt.mqtt_subscribe(t)
            self.mqtt.listen_event(self.mqtt_message, "MQTT_MESSAGE", topic=t)

    def mqtt_message(self, event_name, data, *args, **kwargs):
        """Process a message sent on the MQTT Topic."""
        topic = data.get("topic")
        payload = data.get("payload")

        topic_path = topic.split("/")
        room = topic_path[-1].lower()

        payload_json = {}
        try:
            payload_json = json.loads(payload)
        except ValueError:
            pass

        id = payload_json.get("id")
        name = payload_json.get("name")
        distance = payload_json.get("distance")
        self.log(f"{id} {room} {distance}", level="DEBUG")

        device = self.devices.setdefault(id,{id:id})
        device["measures"] = device.get("measures", 0) + 1

        if (room in self.args["rooms"]):
            dr = device.setdefault("rooms",{}).setdefault(room,{"pos":self.args["rooms"][room]})
            dr["distance"] = distance

            distance_to_stations=[]
            stations_coordinates=[]
            for r in device["rooms"]:
                if "distance" in device["rooms"][r]:
                    distance_to_stations.append(device["rooms"][r]["distance"])
                    stations_coordinates.append(device["rooms"][r]["pos"])

            name = device.get("name", name)
            if (name) and len(distance_to_stations)>2 and device.get("last_calc", datetime.datetime.min)+datetime.timedelta(seconds=15)<datetime.datetime.now():
                device["last_calc"]=datetime.datetime.now()

                if not device.get("ips_dis", False):
                    slug = re.sub(r'[\W_]+', '_', id)
                    self.mqtt.mqtt_publish(f"{self.args.get('hass_topic', 'homeassistant')}/device_tracker/espresense_{slug}/config", json.dumps({"~":f"{self.args.get('ips_topic', 'espresense/ips')}/{id}", "state_topic":"~/state", "icon":"mdi:map-marker-down", "json_attributes_topic":"~", "name":name, "unique_id": f"espresense_{slug}"}), retain = True)
                    device["ips_dis"] = True

                device["x0"] = self.position_solve(distance_to_stations, np.array(stations_coordinates), device.get("x0", None))
                pos = device["x0"].tolist()
                #self.call_service("device_tracker/see", dev_id = id + "_see", gps = [self.config["latitude"]+(pos[1]/111111), self.config["longitude"]+(pos[0]/111111)], location_name="home")
                #self.log(f"{room} {id}: {pos}")

                self.mqtt.mqtt_publish(f"{self.args.get('ips_topic', 'espresense/ips')}/{id}", json.dumps({"name":name, "source_type":"gps", "gps_accuracy":0, "longitude":(self.config["longitude"]+(pos[0]/111111)),"latitude":(self.config["latitude"]+(pos[1]/111111)),"elevation":(self.config.get("elevation","0")+pos[2]),"x":round(pos[0],2),"y":round(pos[1],2),"height":round(pos[2],2), "fixes":len(distance_to_stations),"measures":device["measures"]}));
                self.mqtt.mqtt_publish(f"{self.args.get('ips_topic', 'espresense/ips')}/{id}/state", "home");

    def position_solve(self, distances_to_station, stations_coordinates, last):
        def error(x, c, r):
            return sum([(np.linalg.norm(x - c[i]) - r[i]) ** 2 for i in range(len(c))])

        l = len(stations_coordinates)
        S = sum(distances_to_station)
        # compute weight vector for initial guess
        W = [((l - 1) * S) / (S - w) for w in distances_to_station]
        # get initial guess of point location
        x0 = last if last is not None else sum([W[i] * stations_coordinates[i] for i in range(l)])
        # optimize distance from signal origin to border of spheres
        res = minimize(
            error,
            x0,
            args=(stations_coordinates, distances_to_station),
            method="SLSQP",
            options={}
        )
        self.log(res.message)
        if (res.success): return res.x

