#!/usr/bin/env python

from gi.repository import GLib  # pyright: ignore[reportMissingImports]
import platform
import logging
import sys
import os
from time import sleep, time
import json
import paho.mqtt.client as mqtt
import configparser  # for config/ini file
import _thread

# import Victron Energy packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), "ext", "velib_python"))
from vedbus import VeDbusService


# get values from config.ini file
try:
    config_file = (os.path.dirname(os.path.realpath(__file__))) + "/config.ini"
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        if config["MQTT"]["broker_address"] == "IP_ADDR_OR_FQDN":
            print(
                'ERROR:The "config.ini" is using invalid default values like IP_ADDR_OR_FQDN. The driver restarts in 60 seconds.'
            )
            sleep(60)
            sys.exit()
    else:
        print(
            'ERROR:The "'
            + config_file
            + '" is not found. Did you copy or rename the "config.sample.ini" to "config.ini"? The driver restarts in 60 seconds.'
        )
        sleep(60)
        sys.exit()

except Exception:
    exception_type, exception_object, exception_traceback = sys.exc_info()
    file = exception_traceback.tb_frame.f_code.co_filename
    line = exception_traceback.tb_lineno
    print(
        f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}"
    )
    print("ERROR:The driver restarts in 60 seconds.")
    sleep(60)
    sys.exit()


# Get logging level from config.ini
# ERROR = shows errors only
# WARNING = shows ERROR and warnings
# INFO = shows WARNING and running functions
# DEBUG = shows INFO and data/values
if "DEFAULT" in config and "logging" in config["DEFAULT"]:
    if config["DEFAULT"]["logging"] == "DEBUG":
        logging.basicConfig(level=logging.DEBUG)
    elif config["DEFAULT"]["logging"] == "INFO":
        logging.basicConfig(level=logging.INFO)
    elif config["DEFAULT"]["logging"] == "ERROR":
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.WARNING)


# get timeout
if "DEFAULT" in config and "timeout" in config["DEFAULT"]:
    timeout = int(config["DEFAULT"]["timeout"])
else:
    timeout = 60


# set variables
connected = 0
last_changed = 0
last_updated = 0

dc_in_voltage = -1
dc_in_current = 0
dc_in_power = 0
dc_out_voltage = 0
dc_out_current = 0
dc_out_power = 0

device_off_reason = 0
error_code = 0
mode = 0
device_function = 0
state = 0


# MQTT requests
def on_disconnect(client, userdata, rc):
    global connected
    logging.warning("MQTT client: Got disconnected")
    if rc != 0:
        logging.warning(
            "MQTT client: Unexpected MQTT disconnection. Will auto-reconnect"
        )
    else:
        logging.warning("MQTT client: rc value:" + str(rc))

    while connected == 0:
        try:
            logging.warning("MQTT client: Trying to reconnect")
            client.connect(config["MQTT"]["broker_address"])
            connected = 1
        except Exception as err:
            logging.error(
                f"MQTT client: Error in retrying to connect with broker ({config['MQTT']['broker_address']}:{config['MQTT']['broker_port']}): {err}"
            )
            logging.error("MQTT client: Retrying in 15 seconds")
            connected = 0
            sleep(15)


def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        logging.info("MQTT client: Connected to MQTT broker!")
        connected = 1
        client.subscribe(config["MQTT"]["topic"])
    else:
        logging.error("MQTT client: Failed to connect, return code %d\n", rc)


def on_message(client, userdata, msg):
    try:
        global last_changed, dc_in_voltage, dc_in_current, dc_in_power, dc_out_voltage, dc_out_current, dc_out_power, device_off_reason, error_code, mode, device_function, state

        # get JSON from topic
        if msg.topic == config["MQTT"]["topic"]:
            if msg.payload != "" and msg.payload != b"":
                jsonpayload = json.loads(msg.payload)

                last_changed = int(time())

                if "dcdc_charger" in jsonpayload:
                    if (
                        type(jsonpayload["dcdc_charger"]) == dict
                        and "dc_in_voltage" in jsonpayload["dcdc_charger"]
                    ):
                        dc_in_voltage = float(jsonpayload["dcdc_charger"]["dc_in_voltage"])
                        dc_in_power = (
                            float(jsonpayload["dcdc_charger"]["dc_in_power"])
                            if "dc_in_power" in jsonpayload["dcdc_charger"]
                            else dc_in_current * float(config["DEFAULT"]["voltage"])
                        )
                        dc_in_current = (
                            float(jsonpayload["dcdc_charger"]["dc_in_current"])
                            if "dc_in_current" in jsonpayload["dcdc_charger"]
                            else None
                        ) 
                        dc_out_voltage = (
                            float(jsonpayload["dcdc_charger"]["dc_out_voltage"])
                            if "dc_out_voltage" in jsonpayload["dcdc_charger"]
                            else None
                        ) 
                        dc_out_power = (
                            float(jsonpayload["dcdc_charger"]["dc_out_power"])
                            if "dc_out_power" in jsonpayload["dcdc_charger"]
                            else dc_out_current * float(config["DEFAULT"]["voltage"])
                        )
                        dc_out_current = (
                            float(jsonpayload["dcdc_charger"]["dc_out_current"])
                            if "dc_out_current" in jsonpayload["dcdc_charger"]
                            else None
                        ) 
                        device_off_reason = (
                            (jsonpayload["dcdc_charger"]["device_off_reason"])
                            if "device_off_reason" in jsonpayload["dcdc_charger"]
                            else None
                        )
                        error_code = (
                            float(jsonpayload["dcdc_charger"]["error_code"])
                            if "error_code" in jsonpayload["dcdc_charger"]
                            else (config["DEFAULT"]["error"])
                        )
                        mode = (
                            float(jsonpayload["dcdc_charger"]["mode"])
                            if "mode" in jsonpayload["dcdc_charger"]
                            else (config["DEFAULT"]["mode"])
                        )
                        device_function = (
                            float(jsonpayload["dcdc_charger"]["device_function"])
                            if "device_function" in jsonpayload["dcdc_charger"]
                            else (config["DEFAULT"]["function"])
                        )
                        state = (
                            float(jsonpayload["dcdc_charger"]["state"])
                            if "state" in jsonpayload["dcdc_charger"]
                            else (config["DEFAULT"]["state"])
                        )
                        logging.debug("MQTT payload: " + str(msg.payload)[1:])
                      
                    else:
                        logging.error(
                            'Received JSON MQTT message does not include an dc_in_voltage object in the dcdc_charger object. Expected at least: {"dcdc_charger": {"dc_in_voltage": 0.0}"}'
                        )
                        logging.debug("MQTT payload: " + str(msg.payload)[1:])
                else:
                    logging.error(
                        'Received JSON MQTT message does not include a dcdc_charger object. Expected at least: {"dcdc_charger": {"dc_in_voltage": 0.0}"}'
                    )
                    logging.debug("MQTT payload: " + str(msg.payload)[1:])

            else:
                logging.warning(
                    "Received JSON MQTT message was empty and therefore it was ignored"
                )
                logging.debug("MQTT payload: " + str(msg.payload)[1:])

    except ValueError as e:
        logging.error("Received message is not a valid JSON. %s" % e)
        logging.debug("MQTT payload: " + str(msg.payload)[1:])

    except Exception as e:
        logging.error("Exception occurred: %s" % e)
        logging.debug("MQTT payload: " + str(msg.payload)[1:])


class DbusMqttDCDCChargerService:
    def __init__(
        self,
        servicename,
        deviceinstance,
        paths,
        productname="MQTT DCDC Charger",
        customname="MQTT DCDC Charger",
        connection="MQTT DCDC Charger service",
    ):
        self._dbusservice = VeDbusService(servicename)
        self._paths = paths

        logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path("/Mgmt/ProcessName", __file__)
        self._dbusservice.add_path(
            "/Mgmt/ProcessVersion",
            "Unkown version, and running on Python " + platform.python_version(),
        )
        self._dbusservice.add_path("/Mgmt/Connection", connection)

        # Create the mandatory objects
        self._dbusservice.add_path("/DeviceInstance", deviceinstance)
        self._dbusservice.add_path("/ProductId", 0xFFFF)
        self._dbusservice.add_path("/ProductName", productname)
        self._dbusservice.add_path("/CustomName", customname)
        self._dbusservice.add_path("/FirmwareVersion", "0.1.0 (20250215)")
        # self._dbusservice.add_path('/HardwareVersion', '')
        self._dbusservice.add_path("/Connected", 1)
        self._dbusservice.add_path("/UpdateIndex",0)

        self._dbusservice.add_path("/Latency", None)

        for path, settings in self._paths.items():
            self._dbusservice.add_path(
                path,
                settings["initial"],
                gettextcallback=settings["textformat"],
                writeable=True,
                onchangecallback=self._handlechangedvalue,
            )

        GLib.timeout_add(1000, self._update)  # pause 1000ms before the next request

    def _update(self):
        global last_changed, last_updated

        now = int(time())

        if last_changed != last_updated:
            self._dbusservice["/Dc/In/V"] = (
                round(dc_in_voltage, 2) if dc_in_voltage is not None else None
            )
            self._dbusservice["/Dc/In/P"] = (
                round(dc_in_power, 2) if dc_in_power is not None else None
            )
            self._dbusservice["/Dc/In/I"] = (
                round(dc_in_current, 2) if dc_in_current is not None else None
            )
            self._dbusservice["/Dc/0/Voltage"] = (
                round(dc_out_voltage, 2) if dc_out_voltage is not None else None
            )
            self._dbusservice["/Dc/0/Power"] = (
                round(dc_out_power, 2) if dc_out_power is not None else None
            )
            self._dbusservice["/Dc/0/Current"] = (
                round(dc_out_current, 2) if dc_out_current is not None else None
            )
            self._dbusservice["/DeviceOffReason"] = (
                device_off_reason if device_off_reason is not None else None
            )
            self._dbusservice["/ErrorCode"] = (
                round(error_code, 0) if error_code is not None else None
            )
            self._dbusservice["/Mode"] = (
                round(mode, 0) if mode is not None else None
            )
            self._dbusservice["/Settings/DeviceFunction"] = (
                round(device_function, 0) if device_function is not None else None
            )
            self._dbusservice["/State"] = (
                round(state, 0) if state is not None else None
            )

            logging.debug(
                "|- DC Input: {:.1f} V - {:.1f} A- {:.1f} W".format(
                    dc_in_voltage, dc_in_current, dc_in_power
                )
            )
            
            logging.debug(
                "|- DC Output: {:.1f} V - {:.1f} A- {:.1f} W".format(
                    dc_out_voltage, dc_out_current, dc_out_power
                )
            )

            last_updated = last_changed

        # quit driver if timeout is exceeded
        if timeout != 0 and (now - last_changed) > timeout:
            logging.error(
                "Driver stopped. Timeout of %i seconds exceeded, since no new MQTT message was received in this time."
                % timeout
            )
            sys.exit()

        # increment UpdateIndex - to show that new data is available
        index = self._dbusservice["/UpdateIndex"] + 1  # increment index
        if index > 255:  # maximum value of the index
            index = 0  # overflow from 255 to 0
        self._dbusservice["/UpdateIndex"] = index
        return True

    def _handlechangedvalue(self, path, value):
        logging.debug("someone else updated %s to %s" % (path, value))
        return True  # accept the change


def main():
    _thread.daemon = True  # allow the program to quit

    from dbus.mainloop.glib import (
        DBusGMainLoop,
    )  # pyright: ignore[reportMissingImports]

    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)

    # MQTT setup
    client = mqtt.Client("MqttDCDCcharger_" + str(config["MQTT"]["device_instance"]))
    client.on_disconnect = on_disconnect
    client.on_connect = on_connect
    client.on_message = on_message

    # check tls and use settings, if provided
    if "tls_enabled" in config["MQTT"] and config["MQTT"]["tls_enabled"] == "1":
        logging.info("MQTT client: TLS is enabled")

        if (
            "tls_path_to_ca" in config["MQTT"]
            and config["MQTT"]["tls_path_to_ca"] != ""
        ):
            logging.info(
                'MQTT client: TLS: custom ca "%s" used'
                % config["MQTT"]["tls_path_to_ca"]
            )
            client.tls_set(config["MQTT"]["tls_path_to_ca"], tls_version=2)
        else:
            client.tls_set(tls_version=2)

        if "tls_insecure" in config["MQTT"] and config["MQTT"]["tls_insecure"] != "":
            logging.info(
                "MQTT client: TLS certificate server hostname verification disabled"
            )
            client.tls_insecure_set(True)

    # check if username and password are set
    if (
        "username" in config["MQTT"]
        and "password" in config["MQTT"]
        and config["MQTT"]["username"] != ""
        and config["MQTT"]["password"] != ""
    ):
        logging.info(
            'MQTT client: Using username "%s" and password to connect'
            % config["MQTT"]["username"]
        )
        client.username_pw_set(
            username=config["MQTT"]["username"], password=config["MQTT"]["password"]
        )

    # connect to broker
    logging.info(
        f"MQTT client: Connecting to broker {config['MQTT']['broker_address']} on port {config['MQTT']['broker_port']}"
    )
    client.connect(
        host=config["MQTT"]["broker_address"], port=int(config["MQTT"]["broker_port"])
    )
    client.loop_start()

    # wait to receive first data, else the JSON is empty and phase setup won't work
    i = 0
    while dc_in_voltage == -1:
        if i % 12 != 0 or i == 0:
            logging.info("Waiting 5 seconds for receiving first data...")
        else:
            logging.warning(
                "Waiting since %s seconds for receiving first data..." % str(i * 5)
            )
        sleep(5)
        i += 1

    # formatting
  
    def _a(p, v):
        return str("%.1f" % v) + "A"

    def _w(p, v):
        return str("%i" % v) + "W"

    def _v(p, v):
        return str("%.2f" % v) + "V"

    def _deg(p, v):
        return str("%.1f" % v) + "°C"

    def _n(p, v):
        return str("%i" % v)

    def _x(p, v):
        return int(v,0)

    paths_dbus = {
        "/Dc/In/V": {"initial": 0, "textformat": _v},
        "/Dc/In/P": {"initial": 0, "textformat": _w},
        "/Dc/In/I": {"initial": 0, "textformat": _a},
        "/Dc/0/Voltage": {"initial": 0, "textformat": _v},
        "/Dc/0/Power": {"initial": 0, "textformat": _w},
        "/Dc/0/Current": {"initial": 0, "textformat": _a},
        "/ErrorCode": {"initial": 0, "textformat": _n},
        "/DeviceOffReason": {"initial": 0, "textformat": _x},
        "/Mode": {"initial": 0, "textformat": _n},
        "/Settings/DeviceFunction": {"initial": 0, "textformat": _n},       
        "/State": {"initial": 0, "textformat": _n},
    }


    DbusMqttDCDCChargerService(
        servicename="com.victronenergy.dcdc.mqtt_dcdc"
        + str(config["MQTT"]["device_instance"]),
        deviceinstance=int(config["MQTT"]["device_instance"]),
        customname=config["MQTT"]["device_name"],
        paths=paths_dbus,
    )

    logging.info(
        "Connected to dbus and switching over to GLib.MainLoop() (= event based)"
    )
    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()
