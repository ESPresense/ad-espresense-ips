"""
Credits to:
https://github.com/glucee/Multilateration/blob/master/Python/example.py
Uses:
https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
https://docs.scipy.org/doc/scipy/reference/optimize.minimize-neldermead.html#optimize-minimize-neldermead
"""

import io
import json
import numpy as np
from matplotlib.patches import Polygon as matplotPolygon
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import appdaemon.plugins.hass.hassapi as hass
from scipy.optimize import minimize
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import matplotlib
import collections
from datetime import datetime, timedelta
from scipy.interpolate import interp1d
import math
import time
import random

matplotlib.use("agg")


def get_unix_time_milliseconds():
    return round(time.time() * 1000)

class Sensor():
    def __init__(self, name: str, position):
        self.name = name
        self.position = position
        self.status = "undefined"
        self.color = matplotlib.colors.to_rgba('y')

    def set_status(self, status):
        self.status = status

    def get_status(self):
        return self.status

    def draw_sensor(self, ax, history):
        if self.status == "online":
            self.color = matplotlib.colors.to_rgba('g')
        elif self.status == "offline":
            self.color = matplotlib.colors.to_rgba('r')
        else:
            self.color = matplotlib.colors.to_rgba('y')

        mintime = min(history, key=lambda x: x[1])[
            1].timestamp() if len(history) > 0 else 0
        maxtime = max(history, key=lambda x: x[1])[
            1].timestamp() if len(history) > 0 else 1

        ax.scatter(x=self.position[0], y=self.position[1],
                   label=self.name, color=self.color)
        alpha = interp1d([mintime, maxtime], [0.1, 1])
        for event in history:
            newcolor = (*self.color[:3], float(alpha(event[1].timestamp())))
 
class Device():
    def __init__(self, name, id, color, sensors):
        self.name = name
        self.id = id
        if color is None:
            color = random.choice(list(mcolors.CSS4_COLORS.keys()))

        self.color = matplotlib.colors.to_rgba(color)
        self.position_history = collections.deque(maxlen=5)
        self.measures = 0
        self.last_seen = get_unix_time_milliseconds()

        self.measure_history = {}
        for sensor in sensors:
            self.measure_history[sensor.name] = (
                sensor, collections.deque(maxlen=7))

    def update_last_seen(self):
        self.last_seen = get_unix_time_milliseconds()


    def get_last_seen(self):
        return self.last_seen;

    def add_position_history(self, position):
        self.position_history.appendleft((position, datetime.now()))

    def add_measure_history(self, sensor, distance):
        self.measure_history[sensor.name][1].appendleft(
            (distance, datetime.now()))

    def increment_measure(self):
        self.measures += 1

    def get_aggragate_dist(self, sensor):
        history = list(filter(lambda event: event[1] > (datetime.now(
        ) - timedelta(seconds=10)), self.measure_history[sensor.name][1]))
        if len(history) == 0:
            return None

        mintime = min(history, key=lambda x: x[1])[
            1].timestamp() if len(history) > 0 else 0
        maxtime = max(history, key=lambda x: x[1])[
            1].timestamp() if len(history) > 0 else 1
        weight = interp1d([mintime, maxtime], [0.1, 1])
        weights = list(map(lambda event: float(weight(
            event[1].timestamp())), history))
        weight_sum = sum(weights)
        weights = list(map(lambda weight: weight/weight_sum, weights))
        weighted_avg = 0
        for idx, event in enumerate(history):
            weighted_avg += weights[idx] * event[0]
        return weighted_avg

    def get_distances_and_coords(self, sensors):
        distances = []
        coords = []
        for sensor in sensors:
            sensor_hist = self.measure_history[sensor.name][1]
            if len(sensor_hist) > 0:
                dist = self.get_aggragate_dist(sensor)
                # dist = sensor_hist[0][0]
                if dist is not None:
                    distances.append(dist)
                    coords.append(sensor.position)

        return (distances, coords)

    def draw_device(self, ax):
        mintime = min(self.position_history, key=lambda x: x[1])[
            1].timestamp() if len(self.position_history) > 0 else 0
        maxtime = max(self.position_history, key=lambda x: x[1])[
            1].timestamp() if len(self.position_history) > 0 else 1
        alpha = interp1d([mintime, maxtime], [0.1, 1])

        for history in self.position_history:
            newcolor = (*self.color[:3], float(alpha(history[1].timestamp())))
            ax.scatter(x=history[0][0], y=history[0][1],
                       label=self.name, color=newcolor)

        for device, history in self.measure_history.values():
            dist = self.get_aggragate_dist(device)
            device.draw_sensor(
                ax, [(dist, datetime.now())] if dist is not None else [])


class Room():
    def __init__(self, points, name):
        self.points = points
        self.shapelyPoly = Polygon([(point[0], point[1]) for point in points])
        self.name = name

    def point_in_room(self, point):
        return self.shapelyPoly.contains(point)

    def draw_room(self, ax):
        ax.add_patch(matplotPolygon(
            [(point[0], point[1]) for point in self.points], edgecolor='grey', fill=False))


class ESPresenseIps(hass.Hass):
    def initialize(self):
        self.mqtt = self.get_plugin_api("MQTT")

        self.rooms: list[Room] = []
        for room in self.args["roomplans"]:
            points = [(point["x"], point["y"]) for point in room["points"]]
            self.rooms.append(Room(points, room["name"]))

        self.sensors = {}
        for sensor in self.args["rooms"]:
            sensor_name = self.args["rooms"][sensor]
            self.sensors[sensor] = Sensor(sensor, sensor_name)

        self.devices = {}
        for device in self.args["devices"]:
            self.devices[device["id"]] = Device(device["name"],
                                                device["id"], 
                                                device.get("color_code", None), 
                                                self.sensors.values())

        for sensor in self.args["rooms"]:
            self.subscribe_to_topic(f"{self.args.get('rooms_topic', 'espresense/rooms')}/{sensor}", self.handle_sensor_data_message)
            self.subscribe_to_topic(f"{self.args.get('rooms_topic', 'espresense/rooms')}/{sensor}/status", self.handle_sensor_status_message)
            self.subscribe_to_topic(f"{self.args.get('rooms_topic', 'espresense/rooms')}/{sensor}/telemetry", self.handle_sensor_telemetry_message)

        if "draw_interval" in self.args:
            self.run_every(self.gen_image, "now+1",
                           int(self.args["draw_interval"]))

    def subscribe_to_topic(self, topic, handler):            
        self.mqtt.mqtt_unsubscribe(topic)
        self.mqtt.mqtt_subscribe(topic)
        self.mqtt.listen_event(handler, "MQTT_MESSAGE", topic=topic)

    def handle_sensor_telemetry_message(self, event_name, data, *args, **kwargs):
        process_not_home_devices(self)

    def handle_sensor_status_message(self, event_name, data, *args, **kwargs):
        topic = data.get("topic")
        payload = data.get("payload")

        topic_path = topic.split("/")
        sensor = topic_path[-2].lower()

        if sensor not in self.sensors:
            return

        sensor = self.sensors[sensor]
        sensor.set_status(payload)

    def handle_sensor_data_message(self, event_name, data, *args, **kwargs):
        topic = data.get("topic")
        payload = data.get("payload")

        topic_path = topic.split("/")
        sensor = topic_path[-1].lower()
 
        payload_json = {}
        try:
            payload_json = json.loads(payload)
        except ValueError:
            pass

        id = payload_json.get("id")
        name = payload_json.get("name")
        distance = payload_json.get("distance")

        self.log(f"{id} {sensor} {distance}", level="DEBUG")

        if id not in self.devices:
            return
        if sensor not in self.sensors:
            return

        device = self.devices[id]
        sensor = self.sensors[sensor]

        sensor.set_status("online")

        device.increment_measure()

        device.add_measure_history(sensor, distance)

        distances, coords = device.get_distances_and_coords(self.sensors.values())

        if len(distances) <= 2:
            return

        prev = device.position_history[0][0] if len(
            device.position_history) > 0 else None
        position = position_solve(distances, np.array(coords), prev)

        device.add_position_history(position)
        device.update_last_seen()

        point = Point(position[0], position[1])
        room = min([(room.shapelyPoly.distance(point), room) 
                    for room in self.rooms], key=lambda x: x[0])[1]
        if room:
            x = round(position[0], 2)
            y = round(position[1], 2)
            z = round(position[2], 2)
            fixes = len(distances)
            self.mqtt.mqtt_publish(f"{self.args.get('ips_topic', 'espresense/ips')}/{device.id}", json.dumps({"name": device.name, "x": x, "y": y, "z": z, "fixes": fixes, "measures": device.measures, "currentroom": room.name}))
            self.mqtt.mqtt_publish(f"{self.args.get('ips_topic', 'espresense/ips')}/{device.id}/state", room.name)

    def gen_image(self, kwargs):
        fix, ax = plt.subplots()
        ax.set_aspect(1)

        for room in self.rooms:
            room.draw_room(ax)
        for device in self.devices.values():
            device.draw_device(ax)

        plt.title('ESPresense Locations')
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        self.mqtt.mqtt_publish(
            f"{self.args.get('images_topic', 'espresense/images')}/map", buf.getvalue())
        buf.close()
        plt.close()

def process_not_home_devices(esPresenseIps):
    current_time = get_unix_time_milliseconds()
    for device_entry in esPresenseIps.devices.values():
        last_seen = device_entry.get_last_seen()
        if current_time - last_seen > 5000:
            esPresenseIps.mqtt.mqtt_publish(f"{esPresenseIps.args.get('ips_topic', 'espresense/ips')}/{device_entry.id}", json.dumps({"name": device_entry.name, "x": -1, "y": -1, "z": -1, "fixes": 0, "measures": 0, "currentroom": "not_home"}))
            esPresenseIps.mqtt.mqtt_publish(f"{esPresenseIps.args.get('ips_topic', 'espresense/ips')}/{device_entry.id}/state", "not_home")


def position_solve(distances_to_station, stations_coordinates, last):

    def distance(a, b):
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2)

    def error(x, c, r):
        return sum([
            (abs(distance(x, c[i]) - r[i]) / r[i]**2)**2
            for i in range(len(c))])

    l = len(stations_coordinates)
    S = sum(distances_to_station)

    W = [((l - 1) * S) / (S - w) for w in distances_to_station]

    x0 = last if last is not None else sum(
        [W[i] * stations_coordinates[i] for i in range(l)])

    return minimize(
        error,
        x0,
        args=(stations_coordinates, distances_to_station),
        method="Nelder-Mead",
        options={'xatol': 0.001, 'fatol': 0.001, 'adaptive': True}
    ).x
