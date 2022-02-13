"""
high level support for doing this and that.
"""
import asyncio
import configparser
import logging
import re
import sys
import time

import paho.mqtt.client as mqtt
from pyaehw4a1.aehw4a1 import AehW4a1
from pyaehw4a1.commands import UpdateCommand


class Config:
    """xxx"""

    def __init__(self, config_file):
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(config_file)

        self.mqtt_broker_host = config.get("mqtt-broker", "host", fallback="localhost")
        self.mqtt_broker_port = int(config.get("mqtt-broker", "port", fallback="1883"))
        self.air_conditioners = config.options("air_conditioners")
        self.air_conditioner_ips = {}
        for __x in self.air_conditioners:
            self.air_conditioner_ips[__x] = config.get("air_conditioners", __x)
        self.ac_polling_intervall = config.get(
            "parameter", "ac_polling_interval", fallback=10
        )
        self.log_file = config.get(
            "parameter", "log_file", fallback="./config/aehw4a1_mqtt.log"
        )
        self.messages = list(config["messages"])
        self.mqtt_prefix = config.get("parameter", "mqtt_prefix", fallback="/home/ac/")
        self.mqtt_command = config.get("parameter", "mgtt_command", fallback="/command")

        self.subscribe_topic = []
        for __x in self.air_conditioners:
            self.subscribe_topic.append([self.mqtt_prefix + __x + self.mqtt_command, 0])

        # Read loglevel from config file and evalute
        loglevels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "ERROR": logging.ERROR,
            "WARNING": logging.WARNING,
            "CRITICAL": logging.CRITICAL,
        }
        __loglevel = config.get("parameter", "loglevel", fallback="INFO")
        self.loglevel = loglevels.get(__loglevel, logging.INFO)


class AirConditioners:
    """x"""

    def __init__(self, air_conditioners, air_conditioner_ips):
        """Init AC connections"""
        self.ac_aehw4a1 = {}
        self.ac_status = {}
        self.air_conditioners = air_conditioners
        self.air_conditioner_ips = air_conditioner_ips
        for __x in self.air_conditioners:
            self.ac_aehw4a1[__x] = AehW4a1(air_conditioner_ips[__x])

    def get(self):
        """Pull data from ACs"""
        for __x in self.air_conditioners:
            try:
                self.ac_status[__x] = asyncio.run(
                    self.ac_aehw4a1[__x].command("status_102_0")
                )
            except Exception as __ec:
                logger.warning(
                    "Status poll from AC %s at %s failed: %s",
                    __x,
                    self.air_conditioner_ips[__x],
                    __ec,
                )
            else:
                logger.debug(
                    "Status of AC %s at %s polled: %s",
                    __x,
                    self.air_conditioner_ips[__x],
                    self.ac_status[__x],
                )
        return self.ac_status

    def set(self, _ac, command):
        """Sends command to ACs"""
        try:
            asyncio.run(self.ac_aehw4a1[_ac].command(correct_update_command(command)))
        except Exception as __ec:
            logger.warning(
                "Send command %s to AC %s at %s failed: %s",
                command,
                _ac,
                self.air_conditioner_ips[ac],
                __ec,
            )
        else:
            logger.debug(
                "Sent command to AC %s at %s: %s",
                _ac,
                self.air_conditioner_ips[_ac],
                command,
            )


def on_connect(client, userdata, flags, rc):
    """On connected to the MQTT broker"""
    if rc == 0:
        client.connected_flag = True
        logger.info(
            "Client connected to MQTT broker %s:%s with return code %s",
            configs.mqtt_broker_host,
            str(configs.mqtt_broker_port),
            rc,
        )
        rc = client.subscribe(configs.subscribe_topic)
        if rc[0] == 0:
            logger.info("Client subscribed topics: %s", configs.subscribe_topic)
        else:
            logger.error("Subsription problem. Return code is %s", rc)


def on_publish(client, userdata, result):
    """On publishide data"""
    pass
    # logger.debug("Message %d published", result)
    # print("data published"


def on_message(client, userdata, msg):
    """Callback function on message received"""
    logger.debug("Message received for topic %s: %s", msg.topic, msg.payload.decode())
    __ac = re.findall(configs.mqtt_prefix + "(.+)/command", msg.topic)[0]
    ac.set(__ac, msg.payload.decode())


def correct_update_command(received_update_command):
    """Corrects upper and lower case in commands"""
    update_commands_lower_case = [
        each_command.lower()
        for each_command in UpdateCommand.__dict__["_member_names_"]
    ]
    return UpdateCommand.__dict__["_member_names_"][
        update_commands_lower_case.index(received_update_command.lower())
    ]


configs = Config("./config/aehw4a1_mqtt.ini")

"""Logger configuration"""
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler(configs.log_file)
file_handler.setFormatter(formatter)
file_handler.setLevel(configs.loglevel)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.info("*** HISENSE MQTT CLIENT STARTED ***")
logger.info("Loglevel set to %s", logging.getLevelName(file_handler.level))


ac = AirConditioners(configs.air_conditioners, configs.air_conditioner_ips)

mqtt.Client.connected_flag = False
mqtt_client = mqtt.Client("aehw4a1_mqtt")
mqtt_client.on_connect = on_connect
mqtt_client.on_publish = on_publish
mqtt_client.on_message = on_message
mqtt_client.enable_logger(logger=logger)
try:
    mqtt_client.connect(configs.mqtt_broker_host, configs.mqtt_broker_port, 60)
except Exception as e:
    logger.error("Connection to MQTT broker %s failed: %s", configs.mqtt_broker_host, e)
    sys.exit()
else:
    mqtt_client.loop_start()

while not mqtt_client.connected_flag:  # wait in loop
    time.sleep(0.1)

for key in configs.messages:
    logger.info("Message %s will be published to mqtt broker.", key)

while True:
    try:
        ac_status = ac.get()
        for air_conditioner, messages in ac.ac_status.items():
            if len(configs.messages) > 0:
                # If messages in config file then
                # only dedicated messages from config file will be published
                for message in configs.messages:
                    if message in messages:
                        mqtt_client.publish(
                            configs.mqtt_prefix + air_conditioner + "/" + message,
                            int(messages[message], 2),
                        )
            else:
                # else whole dictionary to be published
                mqtt_client.publish(
                    configs.mqtt_prefix + air_conditioner + "/",
                    str(messages),
                )
        time.sleep(int(configs.ac_polling_intervall))
    except KeyboardInterrupt:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logger.info("*** HISENSE MQTT CLIENT STOPPED ***")
        sys.exit()
