"""
BLE-Presence python plugin for Domoticz
Author: Marco Baglivo, some parts of the components are fork of other open source projects. Read README for more informations.
Version:    
            0.0.1: pre-alpha
            0.0.2: pre-alpha added handling of timestamp
            0.0.3: pre-alpha something is working
            0.1.0: alpha, Domoticz Plugin working... must be fixed the server
            0.2.1  alpha, battery scan now functioning.
            0.2.2  alpha, battery scan removed to see if fix some issues
            0.2.3  alpha:
                   FIX a problem where if a BLE device is not found in the BLE and in Domoticz
                   devices panel "Signal" or "Battery" has bein deleted by the user, the emergency
                   Kill Switch may not disable the device.
            0.2.4  alpha:
                   Battery reading every 24h re-enebled, should be fixed now.
            0.2.5  alpha:
                   Started some code refactoring, moreover added a feature where the security switch act even 
                   if both the optional devices (signal and battery) are deleted by the user.
            0.2.6  alpha:
                   Battery request disabled due to a bug where the server is locked requesting the battery level.
                   99% the issue isn't in the plugin but in the server part, but i'm going to disable it here.
            0.2.7  alpha NEW BRANCH: batteryfix :
                   Restored code to read battery since problem is not here IMHO.
                   TO BUGFIX, BATTERY is asked every 15 minutes.
"""
"""
<plugin key="ble-presence" name="BLE-Presence Client" author="Marco Baglivo" version="0.2.7" wikilink="" externallink="https://github.com/mydomo">
    <params>
        <param field="Address" label="BLE-Presence Server IP address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="Port" width="40px" required="true" default="12345"/>
        <param field="Mode1" label="Timeout from the last beacon received to pull off the device (in seconds)" width="40px" required="true" default="300"/>
        <param field="Mode2" label="Mac addresses (coma ',' separated) for manual adding of BLE devices. (optional)" width="100px" required="true" default="XX:XX:XX:XX:XX:XX"/>
        <param field="Mode6" label="Mode" width="200px" required="true">
            <options>
                <option label="Auto add discovered BLE devices." value="AUTO_ADD_DEVICE" default="true" />
                <option label="Scan only manually added BLE devices" value="MANUAL_ADD_DEVICE" />
                <option label="BLE scanner" value="BLE_SCAN" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import socket
import time
import datetime

SCAN_STOPPED = False
UPDATE_BLE = False
UPDATE_SIGNAL = False
BATTERY_REQUEST = False
BATTERY_DEVICE_REQUEST = ""

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
        global BATTERY_REQUEST
        global BATTERY_DEVICE_REQUEST

        if not self.error:
            # Connect to the socket, ask and get the informations
            result_string = socket_communication()
            if result_string == "ERROR":
                self.error = True

            else:
                # CHECK IF THE SCANNING HAS THE EXPECTED RESULTS, THAN
                # START THE INPUT CLEANING FOR BEACONING DATA
                # REMOVE '[', ']' AND '(' FROM THE RECEIVED STRING
                # WHEN START IN THIS WAY MEANS THAT DATA ARE NOT CORRUPTED.
                if result_string.startswith("[('") and result_string.endswith("'])]"):
                    if SCAN_STOPPED == True:
                        SCAN_STOPPED = False
                        Domoticz.Log("BLE SCANNING reasumed correctly")

                    result_string = result_string[1:-1].replace("(", "")
                    # RECURSIVE SPLIT THE STRING TO GET THE DATA:
                    items = result_string.split("), ")
                    
                    if len(items) == 0:
                        while len(items) < 1:
                            result_string = "'xx:xx:xx:xx:xx:xx', ['-90', '1513096870']), " + result_string
                        items = result_string.split("), ")

                    for x in Devices:
                        DEVICE_FOUND = False

                        #Domoticz.Log("Looking for: " + str(Devices[x].DeviceID) + " in BLE SCAN")
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

                            if ( str(Devices[x].DeviceID) == DEV_ID_BLE ):
                                DEVICE_FOUND = True
                                #Domoticz.Log( str(Devices[x].DeviceID) + " has being found on the BLE Server output")

                                if int(time_difference) <= int(Parameters["Mode1"]):
                                    #Domoticz.Log( str(Devices[x].DeviceID) + " will be updated, last seen: " + str(time_difference) + "seconds ago")
                                    UpdateDevice_by_DEV_ID(DEV_ID_BLE, 1, str("On"))
                                else:
                                    #Domoticz.Log( str(Devices[x].DeviceID) + " will be turned OFF, last seen: " + str(time_difference) + "seconds ago")
                                    UpdateDevice_by_DEV_ID(DEV_ID_BLE, 0, str("Off"))

                            elif ( str(Devices[x].DeviceID) == DEV_ID_S_DATA ):
                                #Domoticz.Log( str(Devices[x].DeviceID) + " has being found on the BLE Server output")
                                DEVICE_FOUND = True

                                if int(time_difference) <= int(Parameters["Mode1"]):
                                    #Domoticz.Log( str(Devices[x].DeviceID) + " will be updated, last seen: " + str(time_difference) + "seconds ago")
                                    UpdateDevice_by_DEV_ID(DEV_ID_S_DATA, SIGNAL_LEVEL, str(SIGNAL_LEVEL))
                                else:
                                    #Domoticz.Log( str(Devices[x].DeviceID) + " will be turned OFF, last seen: " + str(time_difference) + "seconds ago")
                                    UpdateDevice_by_DEV_ID(DEV_ID_S_DATA, 0, str("0"))

                         #  BATTERY REQUEST.
                            elif ( str(Devices[x].DeviceID) == DEV_ID_B_DATA ):
                                #Domoticz.Log( str(Devices[x].DeviceID) + " has being found on the BLE Server output")
                                DEVICE_FOUND = True
                          
                                if int(time_difference) <= int(Parameters["Mode1"]):
                                    #Domoticz.Log( str(Devices[x].DeviceID) + " will be updated, last seen: " + str(time_difference) + "seconds ago")
                                    #Domoticz.Log(str(Devices[x].DeviceID) + " Devices[x].LastUpdate = " + str(Devices[x].LastUpdate))
                                    LASTUPDATE_BATT = time.mktime(datetime.datetime.strptime(Devices[x].LastUpdate, "%Y-%m-%d %H:%M:%S").timetuple())
                                    time_difference_BATT = (round(int(time.time())) - round(int(LASTUPDATE_BATT)))
                                    #Domoticz.Log("Time difference = " + str(time_difference_BATT) + " s")
                                    if (time_difference_BATT >= 900):
                                        Domoticz.Log("Battery level requested for device: " + str(Devices[x].DeviceID))
                                        
                                        DELETE_PREFIX_DEVICE = str(Devices[x].DeviceID).replace("B-", "").replace("S-", "")
                                        DEVICE_FOR_BATTERY = str(DELETE_PREFIX_DEVICE[0:2]) + ":" + str(DELETE_PREFIX_DEVICE[2:4]) + ":" + str(DELETE_PREFIX_DEVICE[4:6]) + ":" + str(DELETE_PREFIX_DEVICE[6:8]) + ":" + str(DELETE_PREFIX_DEVICE[8:10]) + ":" + str(DELETE_PREFIX_DEVICE[10:12])
                                        BATTERY_DEVICE_REQUEST = "battery_level: " + str(DEVICE_FOR_BATTERY)
                         
                                        BATTERY_REQUEST = True

                        if DEVICE_FOUND == False:
                            # DEVICE WAS NOT FOUND, STARTING THE SECURITY MODE
                            security_switch()

                # DATA FROM THE SOCKET IS NOT A REGULAR SCANNING PROCESS.
                # IS A BATTERY READ?
                elif result_string.startswith('{') and result_string.endswith('}'):
                    Domoticz.Log("Socket is sending battery info:" + result_string)
                    
                    # THIS IS ADDED FOR SECURITY, IF TIMEOUT HAS BEING REACHED AND NO INFORMATION FROM THE SERVER TURN OFF THAT DEVICE.
                    security_switch()

                    battery_items = result_string.split("'], '")
                    if len(battery_items) == 1:
                        #Domoticz.Log("Recognized one device")
                        # THERE IS JUST ONE DEVICE... SO SPLIT HIM
                        battery_all_data = result_string.split(" [")
                        #Domoticz.Log(str(battery_all_data[0]))
                        MAC_BATT_READING = battery_all_data[0].replace("{", "").replace("':", "").replace("'", "")
                        battery_percentage_timestamp = battery_all_data[1].split(", ")
                        BATT_BATT_READING = battery_percentage_timestamp[0].replace("'", "") 
                        TIMESTAMP_BATT_READING = battery_percentage_timestamp[1].replace("'", "").replace("]}", "")

                        DEV_ID_B_DATA_READ = str("B-" + MAC_BATT_READING.replace(":", ""))

                        if int(BATT_BATT_READING) == 255:
                            BATTERY_LEVEL_READ = 0
                        elif int(BATT_BATT_READING) < 0:
                            BATTERY_LEVEL_READ = 0
                        else:
                            BATTERY_LEVEL_READ = int(BATT_BATT_READING)

                        UpdateDevice_by_DEV_ID_NOCHECK(DEV_ID_B_DATA_READ, BATTERY_LEVEL_READ, str(BATTERY_LEVEL_READ))

                        BATTERY_REQUEST = False

                    else:
                        for b_item in battery_items:
                            battery_all_data = b_item.split(" [")
                            MAC_BATT_READING = battery_all_data[0].replace("{", "").replace("':", "").replace("'", "")
                            battery_percentage_timestamp = battery_all_data[1].split(", ")
                            BATT_BATT_READING = battery_percentage_timestamp[0].replace("'", "") 
                            TIMESTAMP_BATT_READING = battery_percentage_timestamp[1].replace("'", "").replace("]}", "")

                            DEV_ID_B_DATA_READ = str("B-" + MAC_BATT_READING.replace(":", ""))

                            if int(BATT_BATT_READING) == 255:
                                BATTERY_LEVEL_READ = 0
                            elif int(BATT_BATT_READING) < 0:
                                BATTERY_LEVEL_READ = 0
                            else:
                                BATTERY_LEVEL_READ = int(BATT_BATT_READING)

                            UpdateDevice_by_DEV_ID_NOCHECK(DEV_ID_B_DATA_READ, BATTERY_LEVEL_READ, str(BATTERY_LEVEL_READ))

                        BATTERY_REQUEST = False

                # IS NOT A SCANNING AND IS NOT A BATTERY READ, HANDLE SERVER REPLY OUT OF "MAIN SCOPE"
                else:
                    # Handle server reply out of our main scope 
                    handle_server_reply(result_string)

                    # THIS IS ADDED FOR SECURITY, IF TIMEOUT HAS BEING REACHED AND NO INFORMATION FROM THE SERVER TURN OFF THAT DEVICE.
                    security_switch()

        return

    def AUTO_ADD_DEVICE_devices(self):
        global SCAN_STOPPED
        global UPDATE_BLE
        global UPDATE_SIGNAL
        if not self.error:
            
            result_string = socket_communication()
            if result_string == "ERROR":
                self.error = True

            else:

                # CHECK IF THE SCANNING HAS THE EXPECTED RESULTS, THAN
                # START THE INPUT CLEANING FOR BEACONING DATA
                # REMOVE '[', ']' AND '(' FROM THE RECEIVED STRING
                if result_string.startswith("[('") and result_string.endswith("'])]"):
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
                    handle_server_reply(result_string)
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
            Domoticz.Log("Device: " + str(Devices[Unit].Name) + " updated. (" + str(sValue) + ")")
    return

def UpdateDevice_by_UNIT_NOCHECK(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
        Domoticz.Log("Device: " + str(Devices[Unit].Name) + " updated. (" + str(sValue) + ")")
    return

def UpdateDevice_by_DEV_ID(DEV_ID, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    #Domoticz.Log("Requested to update "+ str(DEV_ID)) 
    for y in Devices:
        if ( str(DEV_ID) == str(Devices[y].DeviceID) ):
            #Domoticz.Log("UPDATING "+ str(DEV_ID) + "with Unit: " + str(y)) 
            Unit = y
            UpdateDevice_by_UNIT(Unit, nValue, sValue)
    return

def UpdateDevice_by_DEV_ID_NOCHECK(DEV_ID, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    #Domoticz.Log("Requested to update "+ str(DEV_ID)) 
    for y in Devices:
        if ( str(DEV_ID) == str(Devices[y].DeviceID) ):
            #Domoticz.Log("UPDATING "+ str(DEV_ID) + "with Unit: " + str(y)) 
            Unit = y
            UpdateDevice_by_UNIT_NOCHECK(Unit, nValue, sValue)
    return

def isDEVICEIDinDB(DEV_ID):
    # Check if a BLE device is already in the database
    for x in Devices:
        if ( str(DEV_ID) == str(Devices[x].DeviceID) ):
            #ALREADY EXIST
            FOUND = True
            break
        else:
            FOUND = False
    return FOUND

def createSwitch(NAME, DEV_ID):
    # Check if a BLE device is already in the database
    UNIT_GENERATED = len(Devices) + 1
    if not UNIT_GENERATED in Devices:
        Domoticz.Device(Name=NAME, Unit=UNIT_GENERATED, DeviceID=DEV_ID, TypeName="Switch").Create()
        Domoticz.Log("Device " + str(NAME)+ " CREATED")
    return

def createCustomSwitch(NAME, DEV_ID):
    # Check if a BLE device is already in the database
    UNIT_GENERATED = len(Devices) + 1
    if not UNIT_GENERATED in Devices:
        Domoticz.Device(Name=NAME, Unit=UNIT_GENERATED, DeviceID=DEV_ID, TypeName="Custom", Options={"Custom": "1;%"}).Create()
        Domoticz.Log("Device " + str(NAME)+ " CREATED")
    return

def security_switch():
    # THIS IS ADDED FOR SECURITY, IF TIMEOUT HAS BEING REACHED AND NO INFORMATION FROM THE SERVER TURN OFF THAT DEVICE.
    for x in Devices:
        # FOR EACH DEVICE CHECK LAST UPDATE.
        ORIGINAL_EXPIRED = False
        BATTERY_EXPIRED = False
        SIGNAL_EXPIRED = False

        ORIGINAL_FOUND = False
        BATTERY_FOUND = False
        SIGNAL_FOUND = False

        if x > 1:
            # Check that no one of the devices has being updated
            # Search the original Device ID (no derivated)
            if not ( str(Devices[x].DeviceID).startswith("S-") or str(Devices[x].DeviceID).startswith("B-")):
                #LAST UPDATED ORGINAL:
                ORIGINAL_FOUND = True
                ORIGINAL_LAST_UPDATE = time.mktime(datetime.datetime.strptime(Devices[x].LastUpdate, "%Y-%m-%d %H:%M:%S").timetuple())
                ORIGINAL_TIME_DIFF = (round(int(time.time())) - round(int(ORIGINAL_LAST_UPDATE)))
                if (ORIGINAL_TIME_DIFF > int(Parameters["Mode1"])):
                    ORIGINAL_EXPIRED = True
                    # CHECK BATTERY
                    for b in Devices:
                        if ( str(Devices[b].DeviceID) == str("B-" + Devices[x].DeviceID)):
                            BATTERY_FOUND = True
                            BATTERY_LAST_UPDATE = time.mktime(datetime.datetime.strptime(Devices[b].LastUpdate, "%Y-%m-%d %H:%M:%S").timetuple())
                            BATTERY_TIME_DIFF = (round(int(time.time())) - round(int(BATTERY_LAST_UPDATE)))
                            if (BATTERY_TIME_DIFF > int(Parameters["Mode1"])):
                                BATTERY_EXPIRED = True
                            else:
                                BATTERY_EXPIRED = False
                    # CHECK SIGNAL
                    for s in Devices:
                        if ( str(Devices[s].DeviceID) == str("S-" + Devices[x].DeviceID)):
                            SIGNAL_FOUND = True
                            SIGNAL_LAST_UPDATE = time.mktime(datetime.datetime.strptime(Devices[s].LastUpdate, "%Y-%m-%d %H:%M:%S").timetuple())
                            SIGNAL_TIME_DIFF = (round(int(time.time())) - round(int(SIGNAL_LAST_UPDATE)))
                            if (SIGNAL_TIME_DIFF > int(Parameters["Mode1"])):
                                SIGNAL_EXPIRED = True
                            else:
                                SIGNAL_EXPIRED = False

                else:
                    ORIGINAL_EXPIRED = False

                if ORIGINAL_FOUND and (BATTERY_FOUND or SIGNAL_FOUND):
                    if ( ORIGINAL_EXPIRED and (BATTERY_EXPIRED or not BATTERY_FOUND) and (SIGNAL_EXPIRED or not SIGNAL_FOUND) ):
                        # the check of the status is formarly unnecessary but allow us to know if the Security Switch has being used.
                        if Devices[x].nValue == 1:
                            Domoticz.Log( "Security Switch: Device " + Devices[x].DeviceID + " cannot be found and reached the timeout, setting as off/no-signal")
                            UpdateDevice_by_DEV_ID(Devices[x].DeviceID, 0, str("Off"))
                        if SIGNAL_FOUND:
                            UpdateDevice_by_DEV_ID(Devices[s].DeviceID, 0, str("0"))
                elif ( (ORIGINAL_FOUND and ORIGINAL_EXPIRED) and not (BATTERY_FOUND or SIGNAL_FOUND) ):
                    # the check of the status is formarly unnecessary but allow us to know if the Security Switch has being used.
                    if Devices[x].nValue == 1:
                        Domoticz.Log( "Security Switch: Device " + Devices[x].DeviceID + " cannot be found and reached the timeout, setting as off/no-signal")
                        UpdateDevice_by_DEV_ID(Devices[x].DeviceID, 0, str("Off"))


    return

def handle_server_reply(result_string):
    global SCAN_STOPPED
    # Domoticz.Log(" ")    > insert something in the log.
    # Domoticz.Error(" ")  > insert something in the ERROR log.
    # SCAN_STOPPED = True  > warn the plugin that the scan was not performed
    if str(result_string).strip() == '':
        # No results, i guess the server is starting.
        Domoticz.Log( "Server connected but no BLE devices has being found in the scan. Hang on...")

    elif str(result_string).strip() == 'Scanning stopped by other function':
        Domoticz.Log( "BLE Server is busy, scan will be reasumed soon.")
        SCAN_STOPPED = True
        # ADDED for security
        security_switch()

    elif str(result_string).strip() == 'Reading started':
        Domoticz.Log( "BLE Server started reading the battery level for the selected device.")
        SCAN_STOPPED = True
        # ADDED for security
        security_switch()

    elif str(result_string).strip() == 'Reading in progress...':
        Domoticz.Log( "BLE Server busy reading the battery level for the selected device.")
        SCAN_STOPPED = True
        # ADDED for security
        security_switch()

    elif str(result_string).strip() == 'Service stopping...':
        Domoticz.Log( "BLE Server turning off.")
        SCAN_STOPPED = True
        # ADDED for security
        security_switch()

    else:
        Domoticz.Error("BLE Server unexpected reply: " + str(result_string) )


    return

def socket_communication():
    global BATTERY_REQUEST
    global BATTERY_DEVICE_REQUEST

    try:
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SERV_ADDR = str(Parameters["Address"])
        SERV_PORT = int(Parameters["Port"])
        soc.connect((SERV_ADDR, SERV_PORT))

        if BATTERY_REQUEST == True:
            clients_input = str(BATTERY_DEVICE_REQUEST)
            Domoticz.Log(str(clients_input))
        else:
            clients_input = "beacon_data"

        soc.send(clients_input.encode()) # we must encode the string to bytes

        data = b''  # recv() does return bytes
        while True:
            try:
                chunk = soc.recv(4096)  # some 2^n number
                if not chunk:  # chunk == ''
                    break

                data += chunk

            except socket.error:
                soc.close()
                break  

        result_bytes = data # the number means how the response can be in bytes  
        socket_read = result_bytes.decode("utf8") # the return will be in bytes, so decode

    except:
        Domoticz.Error("Error connecting to BLE-Server: " + Parameters["Address"] + " on port: " + Parameters["Port"])
        security_switch()
        # ERROR during the connection
        return "ERROR"
    
    else:
        return socket_read