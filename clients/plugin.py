"""
BLE-Presence python plugin for Domoticz
Author: Marco Baglivo, some parts of the components are fork of other open source projects. Read readme for more informations.

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
        #global icons
        Domoticz.Debug("onStart called")
        if Parameters["Mode6"] == 'ADD_DEVICE':
            self.mode = 'ADD_DEVICE'
        if Parameters["Mode6"] == 'BLE_ONLY':
            self.mode = 'BLE_ONLY'
        if Parameters["Mode6"] == 'BLE_BATT':
            self.mode = 'BLE_BATT'

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onHeartbeat(self):
        if self.mode == 'ADD_DEVICE':
            self.ADD_DEVICE_devices()
        if self.mode == 'BLE_ONLY':
            self.BLE_ONLY_devices()
        if self.mode == 'BLE_BATT':
            self.BLE_BATT_devices()
        
    #BLE-PRESENCE SPECIFIC METHODS




