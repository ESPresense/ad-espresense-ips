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
import appdaemon.plugins.hass.hassapi as hass
from scipy.optimize import minimize
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import matplotlib
import collections
from datetime import datetime
from scipy.interpolate import interp1d
matplotlib.use("agg")

# state needed
# Map of sensors Map<Sensor name, Sensor>
#   Sensor Name
#   Sensor Position
#   Last N distances
#       Distance, timestamp
# Map of devices Map<Device id, Device>
#   Device name
#   Device ID
#   Last N positions
#     x, y, timestamp
# list of rooms
#   matplotPolygons of rooms
#   shapely Polygons of rooms


class Sensor():
    def __init__(self, name: str, position: tuple[int, int, int], color):
        self.name = name
        self.position = position
        self.color = matplotlib.colors.to_rgba(color)

    def draw_sensor(self, ax, history):
        mintime = min(history, key=lambda x: x[1])[
            1].timestamp() if len(history) > 0 else 0
        maxtime = max(history, key=lambda x: x[1])[
            1].timestamp() if len(history) > 0 else 1

        ax.scatter(x=self.position[0], y=self.position[1],
                   label=self.name, color=self.color)
        alpha = interp1d([mintime, maxtime], [0.1, 1])
        for event in history:
            newcolor = (*self.color[:3], float(alpha(event[1].timestamp())))
            ax.add_artist(plt.Circle(
                (self.position[0], self.position[1]), event[0], fill=False, color=newcolor))


class Device():
    def __init__(self, name, id, color, sensors: list[Sensor]):
        self.name = name
        self.id = id
        self.color = matplotlib.colors.to_rgba(color)
        self.position_history = collections.deque(maxlen=5)
        self.measures = 0
        # map from Sensor name to (Sensor, List<(distance, datetime)>)
        self.measure_history: dict[str, tuple[Sensor,
                                              collections.deque[tuple[any, datetime]]]] = {}
        for sensor in sensors:
            self.measure_history[sensor.name] = (
                sensor, collections.deque(maxlen=7))

    def add_position_history(self, position):
        self.position_history.append((position, datetime.now()))

    def add_measure_history(self, sensor: Sensor, distance):
        self.measure_history[sensor.name][1].append((distance, datetime.now()))

    def increment_measure(self):
        self.measures += 1

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
            device.draw_sensor(ax, history)

    def get_distances_and_coords(self, sensors):
        distances = []
        coords = []
        for sensor in sensors:
            sensor_hist = self.measure_history[sensor.name][1]
            if len(sensor_hist) > 0:
                distances.append(sensor_hist[0][0])
                coords.append(sensor.position)

        return (distances, coords)


class Room():
    def __init__(self, points, name):
        self.points = points
        self.shapelyPoly = Polygon([(point[0], point[1]) for point in points])
        self.name = name

    def draw_room(self, ax):
        ax.add_patch(matplotPolygon(
            [(point[0], point[1]) for point in self.points], edgecolor='grey', fill=False))

    def point_in_room(self, point):
        return self.shapelyPoly.contains(point)


class ESPresenseIps(hass.Hass):
    def initialize(self):
        self.mqtt = self.get_plugin_api("MQTT")

        self.rooms: list[Room] = []
        for room in self.args["roomplans"]:
            points = [(point["x"], point["y"]) for point in room["points"]]
            self.rooms.append(Room(points, room["name"]))

        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        color_idx = 0
        self.sensors: dict[str, Sensor] = {}
        for sensor in self.args["rooms"]:
            self.sensors[sensor] = Sensor(
                sensor, self.args["rooms"][sensor], colors[color_idx])
            color_idx += 1

            topic = f"{self.args.get('rooms_topic', 'espresense/rooms')}/{sensor}"
            self.mqtt.mqtt_unsubscribe(topic)
            self.mqtt.mqtt_subscribe(topic)
            self.mqtt.listen_event(
                self.mqtt_message, "MQTT_MESSAGE", topic=topic)

        self.devices: dict[str, Device] = {}
        for device in self.args["devices"]:
            self.devices[device["id"]] = Device(device["name"],
                                                device["id"], colors[color_idx], self.sensors.values())
            color_idx += 1

        if "draw_interval" in self.args:
            self.run_every(self.gen_image, "now+1",
                           int(self.args["draw_interval"]))

    def gen_image(self, kwargs):
        self.log("Plotting")
        fix, ax = plt.subplots()
        ax.set_aspect(1)

        for room in self.rooms:
            room.draw_room(ax)
        for device in self.devices.values():
            device.draw_device(ax)

        plt.title('ESPresense Locations')
        # plt.legend(loc=0)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        self.mqtt.mqtt_publish(
            f"{self.args.get('images_topic', 'espresense/images')}/map", buf.getvalue())
        buf.close()
        self.log(f"Plotted")

    def mqtt_message(self, event_name, data, *args, **kwargs):
        """Process a message sent on the MQTT Topic."""
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

        device.increment_measure()

        device.add_measure_history(sensor, distance)

        distances, coords = device.get_distances_and_coords(
            self.sensors.values())
        if len(distances) <= 2:
            return
        prev = device.position_history[0][0] if len(
            device.position_history) > 0 else None
        position = position_solve(distances, np.array(coords), prev)

        device.add_position_history(position)

        point = Point(position[0], position[1])
        for room in self.rooms:
            if room.point_in_room(point):
                self.mqtt.mqtt_publish(f"{self.args.get('ips_topic', 'espresense/ips')}/{device.id}", json.dumps({"name": device.name, "x": round(position[0], 2), "y": round(
                    position[1], 2), "z": round(position[2], 2), "fixes": len(distances), "measures": device.measures, "currentroom": room.name}))
                self.mqtt.mqtt_publish(
                    f"{self.args.get('ips_topic', 'espresense/ips')}/{device.id}/state", room.name)


def position_solve(distances_to_station, stations_coordinates, last):
    def error(x, c, r):
        return sum([(np.linalg.norm(x - c[i]) - r[i]) ** 2 for i in range(len(c))])
        # return sum([(np.linalg.norm(x - c[i]) - r[i]) for i in range(len(c))])

    l = len(stations_coordinates)
    S = sum(distances_to_station)
    # compute weight vector for initial guess
    W = [((l - 1) * S) / (S - w) for w in distances_to_station]
    # get initial guess of point location
    x0 = last if last is not None else sum(
        [W[i] * stations_coordinates[i] for i in range(l)])
    # optimize distance from signal origin to border of spheres
    return minimize(
        error,
        x0,
        args=(stations_coordinates, distances_to_station),
        method="Nelder-Mead",
        options={'xatol': 0.001, 'fatol': 0.001, 'adaptive': True}
    ).x
