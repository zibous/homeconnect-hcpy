#!/usr/bin/env python3
import os
import sys
import logging
import json
import time
from threading import Thread
import requests
from base64 import urlsafe_b64encode as base64url_encode
from Crypto.Random import get_random_bytes
from dateutil.parser import *
from datetime import datetime
import arrow

import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes

properties = Properties(PacketTypes.CONNECT)
properties.SessionExpiryInterval = 30 * 60  # in seconds

from hcpy.HCSocket import HCSocket, now
from hcpy.HCDevice import HCDevice

dirname, filename = os.path.split(os.path.abspath(__file__))

__APPLICATION_NAME__ = os.path.basename(dirname)
__author__ = "Peter Siebler"
__version__ = "1.1.1"
__license__ = "MIT"

## all for logging
from loguru import logger

logger = logger.patch(lambda record: record.update(name=record["file"].name))
logger = logger.opt(colors=False)
min_level = "INFO"


def setlogLevel(min_level: str = min_level):
    """set the log level for the current logger:
    TRACE :   5
    DEBUG :  10
    INFO:    20
    SUCCESS:  25
    WARNING:  30
    ERROR:    40
    CRITICAL: 50
    """

    def my_filter(record):
        return record["level"].no >= logger.level(min_level).no

    logger.remove()
    logger.add(sys.stderr, filter=my_filter)


class Homeconnect:
    """homeconnect applciation class"""

    # app default settings
    devices_file: str = "./config/devices.json"
    mqtt_host: str = "localhost"
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_port: int = 1883
    mqtt_prefix: str = "homeconnect/"
    mqtt_ssl: bool = False
    mqtt_cafile: None
    mqtt_certfile: None
    mqtt_keyfile: None
    mqtt_clientname: str = __APPLICATION_NAME__
    domain_suffix: str = ""
    debug: bool = False
    locale: str = "de"
    tzinfo: str = "Europe/Vaduz"
    LOGLEVEL: str = "WARNING"

    # device dict
    dev = {}
    addons = {}

    # simple state machine
    state: str = "off"
    _state: int = 0

    # power and water meter
    powermeterdisplay: float = 0.000
    waterdisplay: float = 0.000

    def __init__(self, config_file: str = "./config/config.json"):
        """home connect class
        param str config_file homeconnect application settings
        """
        self.state = "off"
        self.config_file = config_file
        self.__loadSettings__()

    def __loadSettings__(self) -> bool:
        """load all settings from the config json file
        and store the items to the class object attributes (device settings, mqttbrocker...)
        """
        try:
            if not ((sys.version_info.major == 3 and sys.version_info.minor == 11) and sys.version_info.micro == 9):
                logger.warning(f"Application needs Python 3.11.9")

            if os.path.isfile(self.config_file):
                with open(self.config_file, "r", encoding="utf8") as f:
                    param = json.load(f)
                for key, value in param.items():
                    setattr(self, key, value)
                setlogLevel(self.LOGLEVEL)
                logger.debug(f"Application config file{self.config_file} found.")
            else:
                logger.critical(f"Application config file {self.config_file} not found.")
                sys.exit(f"Missing config file {self.config_file}")
            if os.path.isfile(self.devices_file):
                logger.debug(f"Devices file {self.devices_file} found.")
            else:
                logger.critical(f"Devices file {self.devices_file} not found, run hc-login first.")
                sys.exit(f"Missing Devices File  {self.devices_file}")

            # be shure that we have a unique client
            _id = base64url_encode(get_random_bytes(4)).decode("UTF-8")
            self.mqtt_clientname = f"bosch-{_id}"
            logger.debug(f"Application ready to run")
            return True

        except Exception as e:
            raise e
        finally:
            return False

    def timeDelta(self, strDate: str = None, shortmode: bool = True, times: str = "h"):
        """get the time delta for the given date to now
        parameter times: y,q,m,w,d,h,min,s
        """
        try:
            list_times = {
                "y": ["year", "month", "day", "hour"],
                "q": ["quarter", "month", "week", "day"],
                "m": ["month", "week", "day"],
                "w": ["week", "day", "hour"],
                "d": ["day", "hour", "minute"],
                "h": ["hour", "minute"],
                "min": ["minute", "second"],
            }
            if times and times == "s":
                d1 = arrow.get(strDate, tzinfo=self.tzinfo)
                d2 = arrow.get(datetime.now(), tzinfo=self.tzinfo)
                return (d2 - d1).seconds

            _granularity = list_times.get(times, "auto")
            return arrow.get(strDate, tzinfo=self.tzinfo).humanize(only_distance=shortmode, granularity=_granularity, locale=self.locale)

        except Exception as e:
            raise e

    def __turn_on__(self):
        """turn the state on if previous state was off"""
        if self.state == "off":
            self._print_state_change("on")
            self.state = "on"
        else:
            self._state = 0

    def __turn_off__(self):
        """turn the state off if previous state was on"""
        if self.state == "on":
            self._print_state_change("off")
            self.state = "off"
        else:
            self._state = 0

    def status(self, onstate: bool = False) -> int:
        """set the state based on onstate settings"""
        if onstate:
            self.__turn_on__()
            return self._state
        else:
            self.__turn_off__()
            return self._state

    def _print_state_change(self, new_state) -> str:
        """private print stat and set the _state
        _state 1 : switched to on
        _state 2 : switched to off
        _state 0 : idle
        """
        logger.debug(f"Dishwasher switched from {self.state}-{new_state}.")
        if self.state == "off" and new_state == "on":
            self._state = 1
        elif self.state == "on" and new_state == "off":
            self._state = 2
        else:
            self._state = 0

    def onStateChanged(self, client, name: str, topic: str, states: dict) -> bool:
        """simple callback state payload from client add additional data (energy, water)"""
        try:
            if topic and states:

                logger.debug(f"Resource - Websocket Link: {states.get('wslink', 'unkown')}")

                states["lastupdate"] = now()
                states["Name"] = name

                _addOns = self.addons.get(name, None)
                if _addOns.get("installed", None):
                    states["installed"] = _addOns.get("installed", None)
                    states["operatingtime"] = self.timeDelta(strDate=states["installed"], shortmode=False, times="y")

                # get the running state from the device
                if states.__contains__("PowerState") and states.__contains__("ProgramProgress"):

                    logger.debug(f"{name} Calc the water and energy usage")
                    states["isrunning"] = False

                    if states.__contains__("RemainingProgramTime"):
                        _value = states.get("RemainingProgramTime", 0)
                        states["remainingseconds"] = "%d:%02d" % (_value / 60 / 60, (_value / 60) % 60)

                    # get the current status for the dishwasher
                    _dws = states.get("PowerState", "Off") == "On" and int(states.get("ProgramProgress", 1)) > 0
                    _dws = self.status(_dws)

                    if self.status(_dws) == 1:
                        logger.debug(f"{name} is now starting")
                        states["sessionstart"] = now()
                        states["sessiontime"] = ""
                        states["isrunning"] = True

                    if self.status(_dws) == 2:
                        logger.debug(f"{name} is now ending")
                        states["sessionsend"] = now()
                        states["isrunning"] = False
                        states["sessiontime"] = self.timeDelta(strDate=states["sessionsend"], shortmode=False, times="min")

                    _tasktext = ["idle", "started", "ending"]
                    states["taskstate"] = _tasktext[self.status(_dws)]

                    if _addOns:
                        _powermeter = _addOns.get("powermeter", None)
                        if _powermeter:
                            # ----------------------------------------------------------
                            # get the data from the powermeter (tasmota switch) payload:
                            # ----------------------------------------------------------
                            # {"StatusSNS":{"Time":"2024-06-26T16:19:59",
                            #               "ENERGY":{"TotalStartTime":"2022-09-03T13:02:25",
                            #                         "Total":167.743,
                            #                         "Yesterday":0.779,
                            #                         "Today":0.045,"Power": 3,
                            #                         "ApparentPower":30,
                            #                         "ReactivePower":30,
                            #                         "Factor":0.10,
                            #                         "Voltage":227,
                            #                         "Current":0.133
                            #                        }
                            #               }
                            # }
                            pmd = states["powermeter"] = requests.get(url=_powermeter).json()
                            if pmd:
                                _temp = pmd.get("StatusSNS", {})
                                _temp = _temp.get("ENERGY", {})
                                _temp = _temp.get("Total", 0.00)
                                if _dws == 1:
                                    logger.debug(f"{name} is now strating, save powermeter data")
                                    self.powermeterdisplay = _temp
                                elif _dws == 2:
                                    logger.debug(f"{name} is now strating, calc the used energy")
                                    if self.powermeterdisplay and _temp > self.powermeterdisplay:
                                        states["energy_used"] = _temp - self.powermeterdisplay
                                else:
                                    logger.debug(f"{name} is currently not consuming any energy")
                                    states["powerdisplay"] = _temp
                                    states["energy_used"] = float(0.00)

                        _watermeter = _addOns.get("watermeter", None)
                        if _watermeter:
                            # ----------------------------------------------------------
                            # get the data from the watermeter (esp-device) payload:
                            # ----------------------------------------------------------
                            # { "id":"sensor-wasseruhr_anzeige",
                            #   "value":7.355,
                            #   "state":"7.355 m³"
                            #  }
                            mwd = states["watermeter"] = requests.get(url=_watermeter).json()
                            if mwd:
                                _liter = float(mwd.get("value", 0)) * 1000.00
                                if _dws == 1:
                                    logger.debug(f"{name} is now strating, save watermeter data")
                                    self.waterdisplay = _liter
                                    states["watermeterdisplay"] = _liter
                                elif _dws == 2:
                                    logger.debug(f"{name} is now ending, calc the uses water consumption")
                                    if self.waterdisplay and _liter > self.waterdisplay:
                                        states["water_used"] = _liter - self.waterdisplay
                                else:
                                    logger.debug(f"{name} does not need water at the moment")
                                    states["watermeterdisplay"] = _liter
                                    states["water_used"] = float(0.00)

                    if _addOns.get("taps", None) and states.get("Started", 0):
                        _tabs = int(_addOns.get("taps", 20))
                        _tabsmin = int(_addOns.get("taps_min", 0))
                        states["ordertaps"] = (int(states.get("Started", 0)) % _tabs) < _tabsmin

                ## publish the new state
                payload = json.dumps(states, ensure_ascii=True)
                logger.info(f"{name} publish state data {states.get('wslink', 'unkown')} to {topic}")

                _result = client.publish(topic=f"{topic}", payload=payload, retain=True)
                _status = _result[0]
                if _status == 0:
                    logger.success(f"{name} ↠ {states.get('wslink', 'unkown')} publish send {topic} valid and finished")
                else:
                    logger.critical(f"{name} publish failed {topic}, {payload}")

                return True

        except Exception as e:
            logger.critical(f"{name} {str(e)}, line {sys.exc_info()[-1].tb_lineno}")

        return False

    def run(self):
        """home connect mqtt hc2mqtt"""

        def on_connect(cleint, obj, flags, reason_code, properties):
            """mqtt brocker connect callback"""
            if reason_code.is_failure:
                logger.warning(f"ERROR MQTT connection failed: unauthorized - {reason_code}")
            else:
                logger.success(f"MQTT Brocker connection established: {reason_code}, {self.mqtt_prefix}LWT=Onine ")
                client.publish(topic=f"{self.mqtt_prefix}LWT", payload="online", retain=True)
                # Re-subscribe to all device topics on reconnection
                for device in devices:
                    mqtt_set_topic = f"{self.mqtt_prefix}{device['name']}/set"
                    logger.debug(f"{device['name']}, set topic: {mqtt_set_topic}")
                    client.subscribe(mqtt_set_topic)
                    mqtt_set_topic = f"{self.mqtt_prefix}{device['name']}/refresh"
                    client.subscribe(mqtt_set_topic)
                    for value in device["features"]:
                        # If the device has the ActiveProgram feature it allows programs to be started
                        # and scheduled via /ro/activeProgram
                        if "BSH.Common.Root.ActiveProgram" == device["features"][value]["name"]:
                            mqtt_active_program_topic = f"{self.mqtt_prefix}{device['name']}/activeProgram"
                            logger.debug(f"{device['name']}, program topic: {mqtt_active_program_topic}")
                            client.subscribe(mqtt_active_program_topic)

        def on_disconnect(client, userdata, flags, reason_code, properties):
            """mqtt brocker disconnect callback"""
            if reason_code > 0:
                logger.critical(f"FATAL ERROR MQTT client disconnected: {reason_code}")

        def on_publish(client, userdata, mid, reason_code, properties):
            """mqtt brocker publish callback"""
            if reason_code.is_failure:
                logger.warning(f"ERROR MQTT publish failed: {reason_code}")

        def on_message(client, userdata, msg):
            """mqtt brocker on message callback"""

            mqtt_state = msg.payload.decode()
            mqtt_topic = msg.topic.split("/")

            logger.info(f"{msg.topic} received mqtt message {mqtt_state}")

            try:
                if len(mqtt_topic) >= 2:
                    device_name = mqtt_topic[-2]
                    topic = mqtt_topic[-1]
                else:
                    raise Exception(f"Invalid mqtt topic {msg.topic}.")
                try:
                    msg = json.loads(mqtt_state)
                except ValueError as e:
                    raise ValueError(f"Invalid JSON in message: {mqtt_state}.") from e

                if topic == "set":
                    resource = "/ro/values"

                elif topic == "refresh":
                    logger.info(f"Reconnect  {self.dev[device_name]}")
                    self.dev[device_name].reconnect()
                    return

                elif topic == "activeProgram":
                    resource = "/ro/activeProgram"
                else:
                    raise Exception(f"Payload topic {topic} is unknown.")

                if self.dev[device_name].connected:
                    if resource and msg:
                        self.dev[device_name].get(resource, 1, "POST", msg)
                else:
                    logger.critical(f"{device_name}, ERROR cant send message as websocket is not connected")

            except Exception as e:
                logger.critical(f"{device_name} FATAL ERROR", {e})

        try:

            """try to open the devices config file (created by hc login)"""
            with open(self.devices_file, "r") as f:
                devices = json.load(f)

            """register the mqtt brocker"""
            # client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2, client_id=self.mqtt_clientname, transport="tcp", reconnect_on_failure=True, protocol=mqtt.MQTTv5
            )

            if self.mqtt_username and self.mqtt_password:
                client.username_pw_set(self.mqtt_username, self.mqtt_password)
            if self.mqtt_ssl:
                if self.mqtt_cafile and self.mqtt_certfile and self.mqtt_keyfile:
                    client.tls_set(
                        ca_certs=self.mqtt_cafile,
                        certfile=self.mqtt_certfile,
                        keyfile=self.mqtt_keyfile,
                        cert_reqs=self.ssl.CERT_REQUIRED,
                    )
                else:
                    client.tls_set(cert_reqs=self.ssl.CERT_NONE)

            """last will topic for the homeconnect application"""
            client.will_set(f"{self.mqtt_prefix}LWT", payload="offline", qos=0, retain=True)

            """register all callbacks"""
            client.on_connect = on_connect
            client.on_disconnect = on_disconnect
            client.on_message = on_message
            client.on_publish = on_publish

            client.connect(host=self.mqtt_host, port=self.mqtt_port, clean_start=mqtt.MQTT_CLEAN_START_FIRST_ONLY, properties=properties, keepalive=70)

            """register each device as new thread, connect to the selected device"""
            for device in devices:

                _name = device["name"]

                if device.__contains__("addons"):
                    self.addons[_name] = device["addons"]

                _resources = device["resources"]

                mqtt_topic = self.mqtt_prefix + _name
                thread = Thread(target=self.client_connect, args=(client, device, mqtt_topic, self.domain_suffix, _resources, self.debug))
                thread.start()

            client.loop_forever()

        except Exception as e:
            logger.critical(f"MQTT FATAL ERROR {str(e)}, line {sys.exc_info()[-1].tb_lineno}")

    ## ------------------------------------------------------------------------
    ## imported from hcmqtt.py, sorry...
    ## ------------------------------------------------------------------------
    def client_connect(self, client, device, mqtt_topic, domain_suffix, resources, debug):
        """connect to the client"""

        host = device["host"]
        name = device["name"]

        # HCDevice should maintain its own state?
        state = {}

        def on_message(msg):
            if msg is not None:
                if len(msg) > 0:
                    update = False
                    for key in msg.keys():
                        val = msg.get(key, None)
                        if key in state:
                            # Override existing values with None if they have changed
                            state[key] = val
                            update = True
                        else:
                            # Dont store None values until something useful is populated?
                            if val is None:
                                continue
                            else:
                                state[key] = val
                                update = True

                    if not update:
                        return

                    if client.is_connected():
                        # build the payload and publish the state
                        self.onStateChanged(client=client, name=name, topic=f"{mqtt_topic}/state", states=msg)
                    else:
                        logger.warning(f"{name} ERROR Unable to publish update as mqtt is not connected.")

        def on_open(ws):
            """callback client connection open, publish the last will topic for the device"""
            client.publish(topic=f"{mqtt_topic}/LWT", payload="online", retain=True)
            logger.debug(f"MQTT Last Will {device['name']} Topic={mqtt_topic}/LWT Online")

        def on_close(ws, code, message):
            """callback client connection open, publish the last will topic for the device"""
            client.publish(topic=f"{mqtt_topic}/LWT", payload="offline", retain=True)
            logger.debug(f"MQTT Last Will {device['name']} Offline, Code={code}, Message={message} websocket closed !")

        while True:
            time.sleep(3)
            try:
                """connect to the device"""
                logger.debug(f"{name} connecting to {host}")
                ws = HCSocket(host=host, psk64=device["key"], iv64=device.get("iv", None), domain_suffix=domain_suffix, debug=debug)
                self.dev[name] = HCDevice(ws=ws, device=device, resources=resources, debug=self.debug)
                self.dev[name].run_forever(on_message=on_message, on_open=on_open, on_close=on_close)
            except Exception as e:
                logger.warning(f"{device['name']}, ERROR  {str(e)}, line {sys.exc_info()[-1].tb_lineno}, Offline")
                client.publish(topic=f"{mqtt_topic}/LWT", payload="offline", retain=True)

            time.sleep(57)


if __name__ == "__main__":
    """Start Main application"""
    try:
        logger.info(f"APP {__APPLICATION_NAME__}, Version {__version__} starting")
        hc = Homeconnect()
        hc.run()
    except Exception as e:
        logger.critical(f"APP {__APPLICATION_NAME__} ERROR {str(e)}, line {sys.exc_info()[-1].tb_lineno}")
