"""
BLE-Presence python plugin for Domoticz
Author: Marco Baglivo, some parts of the components are fork of other open source projects. Read README for more informations.

Version:    
            0.0.1: pre-alpha
            0.0.2: pre-alpha added handling of timestamp
            0.0.3: pre-alpha something is working
            0.1.0: beta, Domoticz Plugin working... must be fixed the server
"""
"""
<plugin key="ble-presence" name="BLE-Presence Client" author="Marco Baglivo" version="0.0.3" wikilink="" externallink="https://github.com/mydomo">
    <params>
        <param field="Address" label="BLE-Presence Server IP address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="40px" required="true" default="12345"/>
        <param field="Mode1" label="Timeout from the last beacon received to pull off the device (in seconds)" width="40px" required="true" default="300"/>
        <param field="Mode2" label="Mac addresses (coma ',' separated) for manual adding of BLE devices. (optional)" width="100px" required="true" default="XX:XX:XX:XX:XX:XX"/>
        <param field="Mode6" label="Mode" width="200px" required="true">
            <options>
                <option label="Auto add discovered BLE devices." value="AUTO_ADD_DEVICE" default="true" />
                <option label="Manual add BLE devices. (no scan)" value="MANUAL_ADD_DEVICE" />
                <option label="BLE scanner" value="BLE_SCAN" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import socket
import time

SCAN_STOPPED = False
UPDATE_BLE = False
UPDATE_SIGNAL = False

class BasePlugin:

    def __init__(self):
        self.debug = False
        self.error = False
        self.mode = ""
        return

    def onStart(self):
        if Parameters["Mode6"] == 'AUTO_ADD_DEVICE':
            self.mode = 'AUTO_ADD_DEVICE'
        if Parameters["Mode6"] == 'BLE_SCAN':
            self.mode = 'BLE_SCAN'
        if Parameters["Mode6"] == 'MANUAL_ADD_DEVICE':
            self.mode = 'MANUAL_ADD_DEVICE'
        if 1 not in Devices:
            Domoticz.Device(Name="BLE PRESENCE", Unit=1, TypeName="Switch").Create()
        return

    def onStop(self):
        Domoticz.Debug("onStop called")
        return

    def onHeartbeat(self):
        self.error = False
        if self.mode == 'AUTO_ADD_DEVICE':
            self.AUTO_ADD_DEVICE_devices()
        if self.mode == 'BLE_SCAN':
            self.BLE_SCAN_devices()
        if self.mode == 'MANUAL_ADD_DEVICE':
            self.MANUAL_ADD_DEVICE_devices()
        return

    #BLE-PRESENCE SPECIFIC METHODS
    def BLE_SCAN_devices(self):
        global SCAN_STOPPED
        global UPDATE_BLE
        global UPDATE_SIGNAL
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

                # CHECK IF THE SCANNING HAS THE EXPECTED RESULTS, THAN
                # START THE INPUT CLEANING FOR BEACONING DATA
                # REMOVE '[', ']' AND '(' FROM THE RECEIVED STRING
                if result_string.startswith('[') and result_string.endswith(']'):
                    if SCAN_STOPPED == True:
                        SCAN_STOPPED = False
                        Domoticz.Log("BLE SCANNING reasumed correctly")

                    result_string = result_string[1:-1].replace("(", "")
                    # RECURSIVE SPLIT THE STRING TO GET THE DATA:
                    items = result_string.split("), ")

                    for x in Devices:
                        DEVICE_FOUND = False

                        Domoticz.Log("Looking for: " + str(Devices[x].DeviceID) + " in BLE SCAN")
                        for item in items:
                            bucket = item.split("', ['")
                            BLE_MAC = bucket[0].replace("'", "")
                            ble_data = bucket[1].split("', '")
                            BLE_RSSI = ble_data[0]
                            BLE_TIME = ble_data[1].replace("']", "").replace(")", "")

                            # VARABLES FOR DEVICE ADDING
                            NAME_BLE = BLE_MAC
                            DEV_ID_BLE = str(BLE_MAC.replace(":", ""))
                            # SIGNAL VARIABLES
                            NAME_S_DATA = "SIGNAL " + BLE_MAC
                            DEV_ID_S_DATA = str("S-" + BLE_MAC.replace(":", ""))
                            SIGNAL_LEVEL = round(((100 - abs(int(BLE_RSSI)))*100)/74)
                            if SIGNAL_LEVEL > 100:
                                SIGNAL_LEVEL = 100
                            if SIGNAL_LEVEL < 0:
                                SIGNAL_LEVEL = 0
                            # BATTERY VARIABLES
                            NAME_B_DATA = "BATTERY " + BLE_MAC
                            DEV_ID_B_DATA = str("B-" + BLE_MAC.replace(":", ""))
                            BATTERY_LEVEL = 0


                            # CALCULATE THE TIME DIFFERENCE BETWEEN THE SCAN AND NOW
                            time_difference = (round(int(time.time())) - round(int(BLE_TIME)))

                            if int(time_difference) <= int(Parameters["Mode1"]):
                            # DEVICE HAS BEING SEEN RECENTLY, ADD OR UPDATE IT
                                if ( str(Devices[x].DeviceID) == DEV_ID_BLE ):
                                    Domoticz.Log("Asking update for: " + str(DEV_ID_BLE))
                                    UpdateDevice_by_DEV_ID(DEV_ID_BLE, 1, str("On"))
                                    DEVICE_FOUND = True

                                if ( str(Devices[x].DeviceID) == DEV_ID_S_DATA ):
                                    Domoticz.Log("Asking update for: " + str(DEV_ID_S_DATA))
                                    UpdateDevice_by_DEV_ID(DEV_ID_S_DATA, SIGNAL_LEVEL, str(SIGNAL_LEVEL))
                                    DEVICE_FOUND = True
                            else:
                            # DEVICE HAS NOT BEING SEEN RECENTLY, UPDATE THE STATUS ACCORDINGLY.

                                if ( str(Devices[x].DeviceID) == DEV_ID_BLE ):
                                    UpdateDevice_by_DEV_ID(DEV_ID_BLE, 0, str("Off"))

                                if ( str(Devices[x].DeviceID) == DEV_ID_S_DATA ):
                                    UpdateDevice_by_DEV_ID(DEV_ID_S_DATA, 0, str("0"))

                            if DEVICE_FOUND == False:

                                if ( str(Devices[x].DeviceID) == DEV_ID_BLE ):
                                    UpdateDevice_by_DEV_ID(DEV_ID_BLE, 0, str("Off"))

                                if ( str(Devices[x].DeviceID) == DEV_ID_S_DATA ):
                                    UpdateDevice_by_DEV_ID(DEV_ID_S_DATA, 0, str("0"))

                # THE DATA FROM THE SOCKET ARE NOT A REGULAR SCANNING PROCESS, IDENTIFY IT AND ACT ACCORDINGLY
                else:

                    # DATA FROM THE SOCKET IS NOT A REGULAR SCANNING PROCESS, IDENTIFY IT AND ACT ACCORDINGLY
                    # CHECK IF THE SYSTEM IS BUSY WITH OTHER THINGS:
                    if result_string == "Scanning stopped by other function":
                        #CREATE A VARIABLE TO KNOW THAT THE SCANNING HAS BEING STOPPED
                        SCAN_STOPPED = True
                        Domoticz.Log("BLE SCANNING stopped by other function, devices not updated...")
                    else:
                        Domoticz.Log("BLE SCANNING unexpected syntax in SOCKET REPLY")
                        #CREATE A VARIABLE TO KNOW THAT THE SCANNING HAS BEING STOPPED
                        SCAN_STOPPED = True
        return

    def AUTO_ADD_DEVICE_devices(self):
        global SCAN_STOPPED
        global UPDATE_BLE
        global UPDATE_SIGNAL
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

                # CHECK IF THE SCANNING HAS THE EXPECTED RESULTS, THAN
                # START THE INPUT CLEANING FOR BEACONING DATA
                # REMOVE '[', ']' AND '(' FROM THE RECEIVED STRING
                if result_string.startswith('[') and result_string.endswith(']'):
                    if SCAN_STOPPED == True:
                        SCAN_STOPPED = False
                        Domoticz.Log("BLE SCANNING reasumed correctly")

                    result_string = result_string[1:-1].replace("(", "")
                    # RECURSIVE SPLIT THE STRING TO GET THE DATA:
                    items = result_string.split("), ")
                    for item in items:
                        bucket = item.split("', ['")
                        BLE_MAC = bucket[0].replace("'", "")
                        ble_data = bucket[1].split("', '")
                        BLE_RSSI = ble_data[0]
                        BLE_TIME = ble_data[1].replace("']", "").replace(")", "")

                        # VARABLES FOR DEVICE ADDING
                        NAME_BLE = BLE_MAC
                        DEV_ID_BLE = str(BLE_MAC.replace(":", ""))
                        # SIGNAL VARIABLES
                        NAME_S_DATA = "SIGNAL " + BLE_MAC
                        DEV_ID_S_DATA = str("S-" + BLE_MAC.replace(":", ""))
                        SIGNAL_LEVEL = round(((100 - abs(int(BLE_RSSI)))*100)/74)
                        if SIGNAL_LEVEL > 100:
                            SIGNAL_LEVEL = 100
                        if SIGNAL_LEVEL < 0:
                            SIGNAL_LEVEL = 0
                        # BATTERY VARIABLES
                        NAME_B_DATA = "BATTERY " + BLE_MAC
                        DEV_ID_B_DATA = str("B-" + BLE_MAC.replace(":", ""))
                        BATTERY_LEVEL = 0


                        # CALCULATE THE TIME DIFFERENCE BETWEEN THE SCAN AND NOW
                        time_difference = (round(int(time.time())) - round(int(BLE_TIME)))

                        if int(time_difference) <= int(Parameters["Mode1"]):
                        # DEVICE HAS BEING SEEN RECENTLY, ADD OR UPDATE IT

                            if (isDEVICEIDinDB(DEV_ID_BLE) == True):
                                # DEVICE PRESENT, UPDATE IT
                                UpdateDevice_by_DEV_ID(DEV_ID_BLE, 1, str("On"))

                            if (isDEVICEIDinDB(DEV_ID_BLE) == False):
                                # DEVICE NOT PRESENT, CREATE IT
                                createSwitch(NAME_BLE, DEV_ID_BLE)

                            if (isDEVICEIDinDB(DEV_ID_S_DATA) == True):
                                # DEVICE PRESENT, UPDATE IT
                                UpdateDevice_by_DEV_ID(DEV_ID_S_DATA, SIGNAL_LEVEL, str(SIGNAL_LEVEL))

                            if (isDEVICEIDinDB(DEV_ID_S_DATA) == False):
                                # DEVICE NOT PRESENT, CREATE IT
                                createCustomSwitch(NAME_S_DATA, DEV_ID_S_DATA)

                            # BATTERY DEVICE CANNOT BE UPDATED FROM DISCOVERY MODE BUT JUST BY SCANNER MODE
                            if (isDEVICEIDinDB(DEV_ID_B_DATA) == False):
                                # DEVICE NOT PRESENT, CREATE IT
                                createCustomSwitch(NAME_B_DATA, DEV_ID_B_DATA)

                        else:
                        # DEVICE HAS NOT BEING SEEN RECENTLY, UPDATE THE STATUS ACCORDINGLY.

                            if (isDEVICEIDinDB(DEV_ID_BLE) == True):
                                UpdateDevice_by_DEV_ID(DEV_ID_BLE, 0, str("Off"))

                            if (isDEVICEIDinDB(DEV_ID_S_DATA) == True):
                                UpdateDevice_by_DEV_ID(DEV_ID_S_DATA, 0, str("0"))

                # THE DATA FROM THE SOCKET ARE NOT A REGULAR SCANNING PROCESS, IDENTIFY IT AND ACT ACCORDINGLY
                else:

                    # DATA FROM THE SOCKET IS NOT A REGULAR SCANNING PROCESS, IDENTIFY IT AND ACT ACCORDINGLY
                    # CHECK IF THE SYSTEM IS BUSY WITH OTHER THINGS:
                    if result_string == "Scanning stopped by other function":
                        #CREATE A VARIABLE TO KNOW THAT THE SCANNING HAS BEING STOPPED
                        SCAN_STOPPED = True
                        Domoticz.Log("BLE SCANNING stopped by other function, devices not updated...")
                    else:
                        Domoticz.Log("BLE SCANNING unexpected syntax in SOCKET REPLY")
                        #CREATE A VARIABLE TO KNOW THAT THE SCANNING HAS BEING STOPPED
                        SCAN_STOPPED = True
        return

    def MANUAL_ADD_DEVICE_devices(self):
        global SCAN_STOPPED
        if not self.error:

            clean_manual_items = Parameters["Mode2"].replace(" ", "")
            manual_items = clean_manual_items.split(",")
            for manual_item in manual_items:
                BLE_MAC = manual_item
                NAME_BLE = BLE_MAC
                DEV_ID_BLE = str(BLE_MAC.replace(":", ""))
                # SIGNAL VARIABLES
                NAME_S_DATA = "SIGNAL " + BLE_MAC
                DEV_ID_S_DATA = str("S-" + BLE_MAC.replace(":", ""))

                # BATTERY VARIABLES
                NAME_B_DATA = "BATTERY " + BLE_MAC
                DEV_ID_B_DATA = str("B-" + BLE_MAC.replace(":", ""))
                BATTERY_LEVEL = 0

                if (isDEVICEIDinDB(DEV_ID_BLE) == False):
                    # DEVICE NOT PRESENT, CREATE IT
                    createSwitch(NAME_BLE, DEV_ID_BLE)

                if (isDEVICEIDinDB(DEV_ID_S_DATA) == False):
                    # DEVICE NOT PRESENT, CREATE IT
                    createCustomSwitch(NAME_S_DATA, DEV_ID_S_DATA)

                # BATTERY DEVICE CANNOT BE UPDATED FROM DISCOVERY MODE BUT JUST BY SCANNER MODE
                if (isDEVICEIDinDB(DEV_ID_B_DATA) == False):
                    # DEVICE NOT PRESENT, CREATE IT
                    createCustomSwitch(NAME_B_DATA, DEV_ID_B_DATA)

                self.mode = 'BLE_SCAN'
        return

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

def UpdateDevice_by_UNIT(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
            #Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return

def UpdateDevice_by_DEV_ID(DEV_ID, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    Domoticz.Log("Requested to find "+ str(DEV_ID)) 
    for y in Devices:
        if ( str(DEV_ID) == str(Devices[y].DeviceID) ):
            Unit = Devices[y].ID
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
            Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return

def isDEVICEIDinDB(DEV_ID):
    # Check if a BLE device is already in the database
    for x in Devices:
        if ( str(DEV_ID) == str(Devices[x].DeviceID) ):
            if (Devices[x].ID in Devices):
                #ALREADY EXIST
                FOUND = True
                break
        else:
            FOUND = False
    return FOUND

def createSwitch(NAME, DEV_ID):
    # Check if a BLE device is already in the database
    UNIT_GENERATED = len(Devices) + 1
    Domoticz.Device(Name=NAME, Unit=UNIT_GENERATED, DeviceID=DEV_ID, TypeName="Switch").Create()
    Domoticz.Log("Device " + str(NAME)+ " CREATED")
    return

def createCustomSwitch(NAME, DEV_ID):
    # Check if a BLE device is already in the database
    UNIT_GENERATED = len(Devices) + 1
    Domoticz.Device(Name=NAME, Unit=UNIT_GENERATED, DeviceID=DEV_ID, TypeName="Custom", Options={"Custom": "1;%"}).Create()
    Domoticz.Log("Device " + str(NAME)+ " CREATED")
    return