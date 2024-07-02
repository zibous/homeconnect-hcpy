#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Sourcecode from:
# url: https://github.com/hcpy2-0/hcpy
# maintainer: pmagyar, Meatballs1


# Contact Bosh-Siemens Home Connect devices
# and connect their messages to the mqtt server
import os
import json
import ssl
import sys
import time
from threading import Thread
import json
import paho.mqtt.client as mqtt

from HCDevice import HCDevice
from HCSocket import HCSocket, now


def runHc2mqtt(config_file: str = "./config/config.json"):
    """load configuration from json file and start the hc2mqtt"""
    try:
        if os.path.isfile(config_file):
            with open(config_file, "r", encoding="utf8") as f:
                param = json.load(f)
            if param:
                hc2mqtt(
                    devices_file=param.get("devices_file", "config/devices.json"),
                    mqtt_host=param.get("mqtt_host", "localhost"),
                    mqtt_port=int(param.get("mqtt_port", 1883)),
                    mqtt_prefix=param.get("mqtt_prefix", "homeconnect/"),
                    mqtt_username=param.get("mqtt_username", ""),
                    mqtt_password=param.get("mqtt_password", ""),
                    mqtt_ssl=param.get("mqtt_ssl", False),
                    mqtt_cafile=param.get("mqtt_cafile", None),
                    mqtt_certfile=param.get("mqtt_certfile", None),
                    mqtt_keyfile=param.get("mqtt_keyfile", None),
                    mqtt_clientname=param.get("mqtt_clientname", __name__),
                    domain_suffix=param.get("domain_suffix", ""),
                    debug=param.get("debug", False),
                )

    except Exception as e:
        print(now(), "runHc2mqtt", "ERROR", e, file=sys.stderr)
    return


def hc2mqtt(
    devices_file: str,
    mqtt_host: str,
    mqtt_prefix: str,
    mqtt_port: int,
    mqtt_username: str,
    mqtt_password: str,
    mqtt_ssl: bool,
    mqtt_cafile: str,
    mqtt_certfile: str,
    mqtt_keyfile: str,
    mqtt_clientname: str,
    domain_suffix: str,
    debug: bool,
):
    """home connect mqtt"""

    def on_connect(client, userdata, flags, rc):
        if rc == 5:
            print(now(), f"ERROR MQTT connection failed: unauthorized - {rc}")
        elif rc == 0:
            print(now(), f"MQTT connection established: {rc}")
            client.publish(f"{mqtt_prefix}LWT", payload="online", qos=0, retain=True)
            # Re-subscribe to all device topics on reconnection
            for device in devices:
                mqtt_set_topic = f"{mqtt_prefix}{device['name']}/set"
                print(now(), device["name"], f"set topic: {mqtt_set_topic}")
                client.subscribe(mqtt_set_topic)
                for value in device["features"]:
                    # If the device has the ActiveProgram feature it allows programs to be started
                    # and scheduled via /ro/activeProgram
                    if "BSH.Common.Root.ActiveProgram" == device["features"][value]["name"]:
                        mqtt_active_program_topic = f"{mqtt_prefix}{device['name']}/activeProgram"
                        print(now(), device["name"], f"program topic: {mqtt_active_program_topic}")
                        client.subscribe(mqtt_active_program_topic)
        else:
            print(now(), f"ERROR MQTT connection failed: {rc}")

    def on_disconnect(client, userdata, rc):
        print(now(), f"ERROR MQTT client disconnected: {rc}")

    def on_message(client, userdata, msg):
        mqtt_state = msg.payload.decode()
        mqtt_topic = msg.topic.split("/")
        print(now(), f"{msg.topic} received mqtt message {mqtt_state}")

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
            elif topic == "activeProgram":
                resource = "/ro/activeProgram"
            else:
                raise Exception(f"Payload topic {topic} is unknown.")

            if dev[device_name].connected:
                dev[device_name].get(resource, 1, "POST", msg)
            else:
                print(now(), device_name, "ERROR cant send message as websocket is not connected")
        except Exception as e:
            print(now(), device_name, "ERROR", e, file=sys.stderr)

    try:

        with open(devices_file, "r") as f:
            devices = json.load(f)

        client = mqtt.Client(mqtt_clientname)

        if mqtt_username and mqtt_password:
            client.username_pw_set(mqtt_username, mqtt_password)

        if mqtt_ssl:
            if mqtt_cafile and mqtt_certfile and mqtt_keyfile:
                client.tls_set(
                    ca_certs=mqtt_cafile,
                    certfile=mqtt_certfile,
                    keyfile=mqtt_keyfile,
                    cert_reqs=ssl.CERT_REQUIRED,
                )
            else:
                client.tls_set(cert_reqs=ssl.CERT_NONE)

        client.will_set(f"{mqtt_prefix}LWT", payload="offline", qos=0, retain=True)
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message
        client.connect(host=mqtt_host, port=mqtt_port, keepalive=70)

        """register each device as new thread, connect to the selected device"""
        for device in devices:
            mqtt_topic = mqtt_prefix + device["name"]
            thread = Thread(target=client_connect, args=(client, device, mqtt_topic, domain_suffix, debug))
            thread.start()

        client.loop_forever()

    except Exception as e:
        print(now(), __name__,".on_connect", "ERROR", e, file=sys.stderr)


global dev
dev = {}


def client_connect(client, device, mqtt_topic, domain_suffix, debug):
    """connect to the client"""

    host = device["host"]
    name = device["name"]

    # HCDevice should maintain its own state?
    state = {}

    def on_message(msg):
        if msg is not None:
            if len(msg) > 0:
                # print(now(), name, msg)

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
                    state["lastupdate"] = now()
                    msg = json.dumps(state)
                    print(now(), name, f"publish to {mqtt_topic}/state")
                    client.publish(f"{mqtt_topic}/state", msg, retain=True)
                else:
                    print(now(),name,"ERROR Unable to publish update as mqtt is not connected.",)

    def on_open(ws):
        client.publish(f"{mqtt_topic}/LWT", "online", retain=True)

    def on_close(ws, code, message):
        client.publish(f"{mqtt_topic}/LWT", "offline", retain=True)
        print(now(), device["name"], "Code=",code, "Message=", message, "websocket closed !")

    while True:
        time.sleep(3)
        try:
            print(now(), name, f"connecting to {host}")
            ws = HCSocket(host, device["key"], device.get("iv", None), domain_suffix)
            dev[name] = HCDevice(ws, device, debug)
            dev[name].run_forever(on_message=on_message, on_open=on_open, on_close=on_close)

        except Exception as e:
            print(now(), device["name"], "ERROR", e, file=sys.stderr)
            client.publish(f"{mqtt_topic}/LWT", "offline", retain=True)

        time.sleep(57)


if __name__ == "__main__":
    runHc2mqtt()
