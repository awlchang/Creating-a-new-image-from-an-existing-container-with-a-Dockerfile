from mqtt import MqttMessage
from workers.base import BaseWorker

from contextlib import contextmanager

import logger
import time

from concurrent.futures import ThreadPoolExecutor
import os

import re

REQUIREMENTS = ['bluepy']
_LOGGER = logger.get(__name__)
_DEVICES = []
_mqtt = []

class BlunonfcWorker(BaseWorker):

    def _setup(self):
        self.autoconfCache = {}
        self._devices = []

    def config(self, availability_topic):
        ret = []

        for key, item in self.devices.items():
            dev_name = str(item["name"])
            dev_mac = item["mac"]
            payload = {
                "topic": item["tag_scanned_topic"],
                "value_template": item["discovery_value_template"]
            }

            ret.append(
                MqttMessage(topic="tag/"
                            + dev_name.lower()
                            + "/config",
                            payload=payload)
            )
            _LOGGER.info("Adding %s device '%s' (%s)", repr(self), dev_name, dev_mac)
            
            self._devices.append(pn532NfcReader(dev_mac, dev_name, item["tag_scanned_topic"]))

        return ret

    def run(self, mqtt):
        _mqtt.append(mqtt)
        
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future = executor.map(self.pn532_readAll, self._devices)
    
    def pn532_readAll(self, dev):
        dev.readAll()

class pn532NfcReader:

    def __init__(self, mac, dev_name, tag_scanned_topic, timeout=5):
        self.mac = mac
        self.dev_name = dev_name
        self.tag_scanned_topic = tag_scanned_topic
        # self.device_info = {}

    @contextmanager
    def connected(self):
        from bluepy import btle

        _LOGGER.info("%s - connected ", self.mac)
        device = btle.Peripheral()
        _DEVICES.append(device)
        # _LOGGER.info("conn= "+str(device.mac))
        # self.device_info.update({device: self.mac})  # use to reconnect device
        device.connect(self.mac)
        yield device

    def readAll(self):
        with self.connected() as device:
            self.getData(device)

    # check device connection and wait for notification
    def getData(self, device):
        self.subscribe(device)
        while True:
            try:
                if device.waitForNotifications(1):
                    # handleNotification() was called
                    continue
            except Exception as e:
                try:
                    device.connect(self.mac)
                    _LOGGER.info("%s - reconnect "+ self.mac)
                    self.getData(device)                    
                    break
                except:
                    # if the bluetooth device is not turn on, and will go here
                    time.sleep(1)
                    _LOGGER.info("Something is wrong.")
                    continue

    def subscribe(self, device):
        device.withDelegate(self)
    
    def handleNotification(self, handle, data):
        data = data.decode('utf-8')
        _LOGGER.info(data)

        if "NDEF" not in data and "Failed" not in data and "failed" not in data and "Error" not in data and "lock" not in data:
            data_decoded = data.replace(" ", ":").strip("atted.").strip()
            _LOGGER.info(data_decoded)

            tag_scanned_payload = {
                self.dev_name: {"UID": data_decoded}
            }

            # _LOGGER.info(self.tag_scanned_topic +" ===== "+ str(tag_scanned_payload))
            _mqtt[0].publish([MqttMessage(topic=self.tag_scanned_topic, payload=tag_scanned_payload)])