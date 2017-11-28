"""
BLE-Presence python plugin for Domoticz
Author: Marco Baglivo, some parts of the components are fork of other open source projects. Read README for more informations.

Version:    
            0.0.1: pre-alpha
            0.0.2: pre-alpha added handling of timestamp
"""
"""
<plugin key="ble-presence" name="BLE-Presence Client" author="Marco Baglivo" version="0.0.2" wikilink="" externallink="https://github.com/mydomo">
    <params>
        <param field="Address" label="BLE-Presence Server IP address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="40px" required="true" default="12345"/>
        <param field="Mode1" label="Timeout from the last beacon received to pull off the device (in seconds)" width="40px" required="true" default="300"/>
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
import time

class BasePlugin:

    def __init__(self):
        self.debug = False
        self.error = False
        self.mode = ""
        return

    def onStart(self):
        if Parameters["Mode6"] == 'ADD_DEVICE':
            self.mode = 'ADD_DEVICE'
        if Parameters["Mode6"] == 'BLE_ONLY':
            self.mode = 'BLE_ONLY'
        if Parameters["Mode6"] == 'BLE_BATT':
            self.mode = 'BLE_BATT'
        if 1 not in Devices:
            Domoticz.Device(Name="BLE PRESENCE", Unit=1, TypeName="Switch").Create()


    def onStop(self):
        Domoticz.Debug("onStop called")

    def onHeartbeat(self):
        self.error = False
        if self.mode == 'ADD_DEVICE':
            self.ADD_DEVICE_devices()
        if self.mode == 'BLE_ONLY':
            self.BLE_ONLY_devices()
        if self.mode == 'BLE_BATT':
            self.BLE_BATT_devices()
        
    #BLE-PRESENCE SPECIFIC METHODS
    def BLE_ONLY_devices(self):
        if not self.error:
            try:
                soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                SERV_ADDR = str(Parameters["Address"])
                SERV_PORT = int(Parameters["Port"])
                soc.connect((SERV_ADDR, SERV_PORT))

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
                # RECURSIVE SPLIT THE STRING TO GET THE DATA, ITEMS CONTAINS ALL THE BTLE DATA:
                items = result_string.split("), ")

                #SEARCH THE DATA INSIDE DEVICES
                for x in Devices:
                    FOUND_VALUE = False

                    #START SPLITTING ALL THE DATA INSIDE THE BTLE DATA
                    for item in items:
                        bucket = item.split("', ['")
                        BLE_MAC = bucket[0].replace("'", "")
                        ble_data = bucket[1].split("', '")
                        BLE_RSSI = ble_data[0]
                        BLE_TIME = ble_data[1].replace("']", "").replace(")", "")

                        #CALCULATE TIME DIFFERENCE
                        time_difference = (round(int(time.time())) - round(int(BLE_TIME)))

                        #CALCULATE RSSI AND STORE IN SIGNAL_LEVEL VARIABLE
                        SIGNAL_LEVEL = round(((100 - abs(int(BLE_RSSI)))*10)/74)
                        if SIGNAL_LEVEL > 10:
                            SIGNAL_LEVEL = 10
                        if SIGNAL_LEVEL < 0:
                            SIGNAL_LEVEL = 0

                        #FIND THE DEVICE
                        if ( str(Devices[x].DeviceID) == (str(BLE_MAC.replace(":", ""))) ):
                            FOUND_VALUE = True

                            #TIME DIFFERENCE IS LESS THAN THE ONE IN THE PARAMETER AND DEVICE IS OFF
                            if (  ( int(time_difference) <= int(Parameters["Mode1"]) ) and (Devices[x].nValue == 0)  ):
                                Devices[x].Update(nValue=1, sValue="On")
                                Domoticz.Log(str(Devices[x].Name) + "(" + str(BLE_MAC) + ") IS NOW ONLINE")

                            #TIME DIFFERENCE IS GREATER THAN THE ONE IN THE PARAMETER AND DEVICE IS ON
                            if (  ( int(time_difference)  > int(Parameters["Mode1"]) ) and (Devices[x].nValue == 1)  ):
                                Devices[x].Update(nValue=0, sValue="Off")
                                Domoticz.Log(str(Devices[x].Name) + "(" + str(BLE_MAC) + ") OFFLINE, LAST TIME SEEN: " + time_difference + " seconds")
                #NOT FOUND                
                if ( (FOUND_VALUE == False) and (Devices[x].nValue == 1) ):
                    Devices[x].Update(nValue=0, sValue="Off")
                    Domoticz.Log(str(Devices[x].Name) + "(" + str(BLE_MAC) + ") OFFLINE, NOT PRESENT IN SERVER LIST")

    def ADD_DEVICE_devices(self):
        if not self.error:
            try:
                soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                SERV_ADDR = str(Parameters["Address"])
                SERV_PORT = int(Parameters["Port"])
                soc.connect((SERV_ADDR, SERV_PORT))

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

                    #VARABLES FOR DEVICE ADDING
                    NAME_BLE = BLE_MAC
                    DEV_ID_BLE = str(BLE_MAC.replace(":", ""))
                    DEV_ID_BLE_PRESENT = True
                    # SIGNAL VARIABLES
                    NAME_S_DATA = "SIGNAL " + BLE_MAC
                    DEV_ID_S_DATA = str("S-" + BLE_MAC.replace(":", ""))
                    DEV_ID_S_DATA_PRESENT = True
                    SIGNAL_LEVEL = round(((100 - abs(int(BLE_RSSI)))*100)/74)
                    if SIGNAL_LEVEL > 100:
                        SIGNAL_LEVEL = 100
                    if SIGNAL_LEVEL < 0:
                        SIGNAL_LEVEL = 0

                    time_difference = (round(int(time.time())) - round(int(BLE_TIME)))

                    if int(time_difference) <= int(Parameters["Mode1"]):
                        for x in Devices:
                            if ( str(DEV_ID_BLE) == str(Devices[x].DeviceID) ):
                                DEV_ID_BLE_PRESENT = True
                                #ALREADY EXIST SO UPDATE IT
                                if ( (Devices[x].nValue != 1) ):
                                    Devices[x].Update(nValue=1, sValue="On")
                                break
                        else:
                            DEV_ID_BLE_PRESENT = False
                            UNIT_GENERATED = len(Devices) + 1
                            if not (UNIT_GENERATED in Devices):
                                Domoticz.Device(Name=NAME_BLE, Unit=UNIT_GENERATED, DeviceID=DEV_ID_BLE, TypeName="Switch").Create()
                                Domoticz.Log("BLE device ADDED: " + str(DEV_ID_BLE))

                        for y in Devices:
                            if ( str(DEV_ID_S_DATA) == str(Devices[y].DeviceID) ):
                                DEV_ID_DATA_S_PRESENT = True
                                #ALREADY EXIST SO UPDATE IT
                                if ( (Devices[y].sValue != SIGNAL_LEVEL) ):
                                    Devices[y].Update(nValue=SIGNAL_LEVEL, sValue=str(SIGNAL_LEVEL), SignalLevel=round(SIGNAL_LEVEL/10), BatteryLevel=100)
                                break
                        else:
                            DEV_ID_DATA_S_PRESENT = False
                            UNIT_GENERATED_S = len(Devices) + 1
                            if not (UNIT_GENERATED_S in Devices):
                                Domoticz.Device(Name=NAME_S_DATA, Unit=UNIT_GENERATED_S, DeviceID=DEV_ID_S_DATA, TypeName="Custom", Options={"Custom": "1;%"}).Create()
                                Domoticz.Log("DATA device ADDED: " + str(DEV_ID_S_DATA))

                    #for key, value in Devices.items():
                    #    Domoticz.Log(str(key))
                    #    Domoticz.Log(str(value))
                    #for x in Devices:
                    #    Domoticz.Log("Device:           " + str(x) + " - " + str(Devices[x]))
                    #    Domoticz.Log("External ID:     '" + str(Devices[x].DeviceID) + "'")
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