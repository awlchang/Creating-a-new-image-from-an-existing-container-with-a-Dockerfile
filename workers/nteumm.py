import json

from mqtt import MqttMessage

from workers.base import BaseWorker
import logger

from evdev import InputDevice, ecodes, list_devices, categorize
import signal, sys

from concurrent.futures import ThreadPoolExecutor
import os

# REQUIREMENTS = ["pyserial"]

# barCodeDeviceString = "BARCODE SCANNER BARCODE SCANNER" # barcode device name
# barCodeDeviceString2 = "BLM103Virtual COM Port" # barcode device name
# barCodeDeviceString3 = "Netum"
# scancodes = {
#     # Scancode: ASCIICode
#     0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
#     10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R',
#     20: u'T', 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
#     30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u';',
#     40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
#     50: u'M', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 100: u'RALT'
# }
lowscodes = {
    # Scancode: ASCIICode
    0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
    10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'q', 17: u'w', 18: u'e', 19: u'r',
    20: u't', 21: u'y', 22: u'u', 23: u'i', 24: u'o', 25: u'p', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
    30: u'a', 31: u's', 32: u'd', 33: u'f', 34: u'g', 35: u'h', 36: u'j', 37: u'k', 38: u'l', 39: u';',
    40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'z', 45: u'x', 46: u'c', 47: u'v', 48: u'b', 49: u'n',
    50: u'm', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 57: u' ', 100: u'RALT'
}

capscodes = {
    0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
    10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R',
    20: u'T', 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
    30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u':',
    40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
    50: u'M', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT',  57: u' ', 100: u'RALT'
}

_device = []
_LOGGER = logger.get(__name__)

class NteummWorker(BaseWorker):

    def _setup(self):
        self.autoconfCache = {}
        self._mqtt=""
        self.reader = {}
        self.reader_mqtt_info = {}
        # self._device = []

    def get_autoconf_data(self, key, name):
        if key in self.autoconfCache:
            print("false")
            return False
        else:
            self.autoconfCache[key] = True
            
            # return {
            #     "platform": "mqtt",
            #     "name": name,
            #     "state_topic": self.topic_prefix + "/" + key + "/state",
            #     "availability_topic": self.topic_prefix + "/" + key + "/presence",
            #     "json_attributes_topic": self.topic_prefix + "/" + key + "/attributes",
            #     "icon": "mdi:tooth-outline",
            # }

    def run(self, mqtt):
        self._mqtt = mqtt

        index = 0

        for key, item in self.devices.items():
            payload = {
                "topic": item["discovery_topic"],
                "value_template": item["discovery_value_template"]
            }

            autoconf_data = self.get_autoconf_data(key, item["name"])
            if autoconf_data != False:
                mqtt.publish([MqttMessage(topic=self.autodiscovery_prefix
                        + "/tag/"
                        + str(item["name"]).lower()
                        + "/config",
                        payload=payload)])
            
            self.reader_mqtt_info[index] = (item["name"], item["discovery_topic"])
            index += 1

        index = 0
        # find usb hid device
        devices = map(InputDevice, list_devices())
        for device in devices:
            _LOGGER.info("Device Name: " + device.name)
            # print(device.name, device.fn)
            # if barCodeDeviceString in device.name or barCodeDeviceString2 in device.name or barCodeDeviceString3 in device.name:                   
            dev = InputDevice(device.path)
            _device.append(dev)
            self.reader[dev.path] = self.reader_mqtt_info[index]
            index += 1
            # else:
            #     print('No barcode device found')
            #     sys.exit()

        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future = executor.map(self.read_barcode, _device)

    def read_barcode(self, dev):
        dev.grab()
        # process usb hid events and format barcode data
        barcode = ""
        caps = False
     
        try:
            for event in dev.read_loop():
                if event.type == ecodes.EV_KEY:
                    data = categorize(event)
                    
                    if data.scancode == 42 or data.scancode == 54:
                        if data.keystate == 1:
                            caps = True
                        if data.keystate == 0:
                            caps = False

                    if data.keystate == 1 and data.scancode != 42 and data.scancode != 54: # Catch only keydown, and not Enter
                        if caps:
                            key_lookup = capscodes.get(data.scancode) or u'UNKNOWN:{}'.format(data.scancode)  # lookup corresponding ascii value or return UNKNOWN:XX
                        else:
                            key_lookup = lowscodes.get(data.scancode) or u'UNKNOWN:{}'.format(data.scancode)  # lookup corresponding ascii value or return UNKNOWN:XX
                            # key_lookup = scancodes.get(data.scancode) or u'UNKNOWN:{}'.format(data.scancode) # lookup corresponding ascii value
                        if data.scancode == 28: # if enter detected print barcode value and then clear it
                            _LOGGER.info("barcode= "+barcode)
                            tag_scanned_payload = {
                                self.reader[dev.path][0]: {"UID":barcode}
                            }
                            # print(self.reader[dev.path][1])
                            self._mqtt.publish([MqttMessage(topic=self.reader[dev.path][1], payload=tag_scanned_payload)])
                            barcode = ""
                        else:
                            barcode += key_lookup # append ch
        except KeyboardInterrupt:
            dev.close()

    def device_ungrab(self):
        for index in range(len(_device)):
            _device[index].ungrab()
            _device.pop(0)
            break