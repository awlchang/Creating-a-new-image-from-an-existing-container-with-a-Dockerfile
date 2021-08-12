from mqtt import MqttMessage
from workers.base import BaseWorker

from contextlib import contextmanager

import logger

REQUIREMENTS = ['bluepy']
_LOGGER = logger.get(__name__)

STATE_ON = "on"
STATE_OFF = "off"

class BlunoledWorker(BaseWorker):

    def _setup(self):
        _LOGGER.info("Adding %d %s devices", len(self.devices), repr(self))

        for name, mac in self.devices.items():
            _LOGGER.info("Adding %s device '%s' (%s)", repr(self), name, mac)
            self.devices[name] = {"led": None, "state": STATE_OFF, "mac": mac}

    def format_state_topic(self, *args):
        return "/".join([self.state_topic_prefix, *args])

    def status_update(self):
        from bluepy import btle

        ret = []
        _LOGGER.debug("Updating %d %s devices", len(self.devices), repr(self))
        for name, led in self.devices.items():
            _LOGGER.debug("Updating %s device '%s' (%s)", repr(self), name, led["mac"])
            try:
                ret += self.update_device_state(name, led["state"]) #[{'topic': 'blunoled/bathroom/greenled', 'payload': 'off'}]
            except btle.BTLEException as e:
                logger.log_exception(_LOGGER, "Error during update of %s device '%s' (%s): %s",
                    repr(self), name, led["mac"], type(e).__name__, suppress=True,)
        return ret

    def update_device_state(self, name, value):
        return [MqttMessage(topic=self.format_state_topic(name), payload=value)]

    def on_command(self, topic, value):  # subscribe topic callback, send command to bluetooth device
        from bluepy import btle
        from bluepy.btle import Peripheral
        print(topic)
        _, _, device_name, _ = topic.split("/")
        led = self.devices[device_name]
        value = value.decode("utf-8")
        # print(value)
        # It needs to be on separate if because first if can change method

        _LOGGER.debug("Setting %s on %s device '%s' (%s)", value, repr(self), device_name, led["mac"])
        try:
            # print("0")
            led["led"] = Peripheral(led["mac"])
            # print("1")
            hand_service = led["led"].getServiceByUUID(btle.UUID(0xDFB0))
            # print("2")
            hand = hand_service.getCharacteristics("0000dfb1-0000-1000-8000-00805f9b34fb")[0]
            # print("3")
            if value == STATE_ON:
                # print(value)
                hand.write(bytes(value, "utf-8"), True)
            elif value == STATE_OFF:
                # print(value)
                hand.write(bytes(value, "utf-8"), True)

            self.disconnect(led["led"])
        except btle.BTLEException as e:
            logger.log_exception( _LOGGER, "Error setting %s on %s device '%s' (%s): %s", value,
                repr(self), device_name, led["mac"], type(e).__name__,)
            self.disconnect(led["led"])
            return []

        try:
            led["state"] = value
            return self.update_device_state(device_name, value)
        except btle.BTLEException as e:
            logger.log_exception(_LOGGER, "Error during update of %s device '%s' (%s): %s", repr(self), device_name,
                led["mac"], type(e).__name__, suppress=True, )
            return []

    def disconnect(self, device):
        device._stopHelper()
        device.disconnect()