"""
BLE-Presence python plugin for Domoticz
Author: Marco Baglivo, some parts of the components are fork of other open source projects. Read README for more informations.

Version:    
            0.0.1: pre-alpha
"""
"""
<plugin key="ble-presence" name="BLE-Presence Client" author="MArco Baglivo" version="0.0.1" wikilink="" externallink="https://github.com/mydomo">
    <params>
        <param field="Address" label="BLE-Presence Server IP address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="40px" required="true" default="12345"/>
        <param field="Mode1" label="BLE-Presence Server name (used as prefix of the device discovered, keep it short.)" width="200px" required="true" default="BLE_1"/>
        <param field="Mode6" label="Mode" width="200px" required="true">
            <options>
                <option label="Discover and Add BLE devices." value="ADD_DEVICE" default="true" />
                <option label="BLE scanner only" value="BLE_ONLY" />
                <option label="BLE scanner + Battery" value="BLE_BATT" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import socket
from datetime import datetime, timedelta

class BasePlugin:

    def __init__(self):
        self.debug = False
        self.error = False
        self.mode = ""
        return

    def onStart(self):
        Domoticz.Log("CIAO!")
        Domoticz.Debug("onStart called")
#        if Parameters["Mode6"] == 'ADD_DEVICE':
#            self.mode = 'ADD_DEVICE'
        if Parameters["Mode6"] == 'BLE_ONLY':
            self.mode = 'BLE_ONLY'
#        if Parameters["Mode6"] == 'BLE_BATT':
#            self.mode = 'BLE_BATT'
        Domoticz.Log("CIAO!")


    def onStop(self):
        Domoticz.Debug("onStop called")

    def onHeartbeat(self):
        Domoticz.Log("CIAO!")
 #       if self.mode == 'ADD_DEVICE':
 #           self.ADD_DEVICE_devices()
        if self.mode == 'BLE_ONLY':
            self.BLE_ONLY_devices()
 #       if self.mode == 'BLE_BATT':
 #           self.BLE_BATT_devices()
        
    #BLE-PRESENCE SPECIFIC METHODS
    def BLE_ONLY_devices(self):
        if not self.error:
            try:
                Domoticz.Log("provo a connettermi")
                soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
                soc.connect((Parameters["Address"], Parameters["Port"]))

                clients_input = "beacon_data" 
                soc.send(clients_input.encode()) # we must encode the string to bytes  
                result_bytes = soc.recv(32768) # the number means how the response can be in bytes  
                result_string = result_bytes.decode("utf8") # the return will be in bytes, so decode


            except:
                self.error = True
                Domoticz.Error("Error connecting to BLE-Server: " + Parameters["Address"] + " on port: " + Parameters["Port"])
            else:
                # START THE INPUT CLEANING FOR BEACONING DATA:
                # REMOVE '[', ']' AND '(' FROM THE RECEIVED STRING
                if result_string.startswith('[') and result_string.endswith(']'):
                    result_string = result_string[1:-1].replace("(", "")
                # RECURSIVE SPLIT THE STRING TO GET THE DATA:
                items = result_string.split("), ")
                for item in items:
                    bucket = item.split("', ['")
                    BLE_MAC = bucket[0].replace("'", "")
                    ble_data = bucket[1].split("', '")
                    BLE_RSSI = ble_data[0]
                    BLE_TIME = ble_data[1].replace("']", "").replace(")", "")
                    Domoticz.Log(BLE_MAC)

                    if (len(Devices) == 0):
                        UNIT_GENERATED = len(Devices) + 1
                        Domoticz.Device(Name=BLE_MAC, Unit=UNIT_GENERATED, TypeName="Switch").Create()
                        Domoticz.Log("Devices created.")


                    #TO BE CONTINUED
global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()