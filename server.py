#!/usr/bin/python3

#################################################################################
#  BLE PRESENCE FOR DOMOTICZ                                                    #
#                                                                               #
#  AUTHOR: MARCO BAGLIVO (ITALY) (https://github.com/mydomo)                    #
#                                                                               #
#################################################################################
#                    PLEASE READ THE README FILE FOR COMPLETE                   # 
#                     INSTALLATION INSTRUCTIONS AND LICENSE                     #
#################################################################################

#################################################################################
# INSTALL REQUIREMENTS ON UBUNTU SERVER 16.04:                                  #
#                                                                               #
# sudo apt-get install -y libbluetooth-dev bluez                                #
# sudo apt-get install python-dev python3-dev python3-setuptools python3-pip    #
# sudo pip3 install pybluez                                                     #
#                                                                               #
#################################################################################

import socket
from lib import ble_scan
from threading import Thread
import sys
import os
import time
import bluetooth._bluetooth as bluez
import signal
import subprocess
from collections import OrderedDict

##########- CONFIGURE SCRIPT -##########
socket_ip = '0.0.0.0'
socket_port = 12345
min_inval_between_batt_level_readings = 300

##########- CONFIGURE TRANSLATIONS -##########
lang_SCAN_STOPPED = 'Scanning stopped by other function'
lang_READING_LOCK = 'Reading in progress...'
lang_READING_START = 'Reading started'
lang_SERVICE_STOP = 'Service stopping...'


##########- START VARIABLE INITIALIZATION -##########
mode = ''
beacons_detected = ''
batt_lev_detected = ''
scan_beacon_data = True
ble_value = ''
devices_to_analize = {}
batt_lev_detected = {}
read_value_lock = False
##########- END VARIABLE INITIALIZATION -##########

##########- START FUNCTION THAT HANDLE CLIENT INPUT -##########
def socket_input_process(input_string):
    global mode
    global devices_to_analize
    global lang_SCAN_STOPPED
    global lang_READING_LOCK
    global lang_READING_START
    global lang_SERVICE_STOP
    global batt_need_update

    ###- TRANSMIT BEACON DATA -###
    # check if client requested "beacon_data"
    if input_string == 'beacon_data':
        # if beacon scanning function has being stopped in order to process one other request (ex.: battery level) warn the client
        if scan_beacon_data == False:
            return str(lang_SCAN_STOPPED)

        # if beacon scanning function is active send the data to the client
        if scan_beacon_data == True:
            # set operative mode to beacon_data
            mode = 'beacon_data'
            # return beacons detected
            return str(beacons_detected)


    ###- TRANSMIT BATTERY LEVEL -###
    # check if the request start with battery_level:
    if input_string.startswith('battery_level:'):
        # trim "battery_level:" from the request
        string_devices_to_analize = input_string.replace("battery_level: ", "").strip()
        # split each MAC address in a list in order to be processed
        devices_to_analize = string_devices_to_analize.split(',')
        # set operative mode to battery_level
        mode = 'battery_level'

        if len(devices_to_analize) >= 1:
            batt_need_update = False

            for device in devices_to_analize:

                battery_level_moderator =  str(batt_lev_detected.get(device, "Never"))
                # cleaning the value stored
                cleaned_battery_level_moderator = str(battery_level_moderator.replace("[", "").replace("]", "").replace(" ", "").replace("'", ""))
                # assign the battery level and the timestamp to different variables
                if cleaned_battery_level_moderator == "Never":
                    batt_need_update = True
                    #print("ASK: Battery of: " + device + " has not previously scanned, starting now.")

                if cleaned_battery_level_moderator != "Never":
                    # DEVICE HAS A PREVIOUS STORED BATTERY LEVEL
                    stored_batterylevel, stored_timestamp = cleaned_battery_level_moderator.split(',')
                    time_difference = int(time.time()) - int(stored_timestamp)
                    #print("ASK: Battery of: " + str(device) + " has being scanned: " + str(time_difference) + " seconds ago.")
                    if ( (int(time_difference) >= int(min_inval_between_batt_level_readings)) or (str(stored_batterylevel) == '255') ):
                        batt_need_update = True
                        #print(device + " battery level need an update! Doing now!")

            if batt_need_update == True and read_value_lock == True:
                return str(lang_READING_LOCK)

            if batt_need_update == True and read_value_lock == False:
                return str(lang_READING_START)

            if batt_need_update == False:
                return str(batt_lev_detected)
        else:
            mode = 'beacon_data'

    ###- STOP RUNNING SERVICES -###
    if input_string == 'stop':
        killer.kill_now = True
        return str(lang_SERVICE_STOP)

##########- END FUNCTION THAT HANDLE CLIENT INPUT -##########

##########- START FUNCTION THAT HANDLE SOCKET'S TRANSMISSION -##########
def client_thread(conn, ip, port, MAX_BUFFER_SIZE = 4096):
    # the input is in bytes, so decode it
    input_from_client_bytes = conn.recv(MAX_BUFFER_SIZE)

    # MAX_BUFFER_SIZE is how big the message can be
    # this is test if it's too big
    siz = len(input_from_client_bytes)
    if  siz >= MAX_BUFFER_SIZE:
        print("The length of input is probably too long: {}".format(siz))

    # decode input and strip the end of line
    input_from_client = input_from_client_bytes.decode("utf8").rstrip()

    res = socket_input_process(input_from_client)
    #print("Result of processing {} is: {}".format(input_from_client, res))

    vysl = res.encode("utf8")  # encode the result string
    conn.sendall(vysl)  # send it to client
    conn.close()  # close connection
##########- END FUNCTION THAT HANDLE SOCKET'S TRANSMISSION -##########

def usb_dongle_reset():
    process0 = subprocess.Popen("sudo hciconfig hci0 down", stdout=subprocess.PIPE, shell=True)
    process0.communicate()
    process1 = subprocess.Popen("sudo hciconfig hci0 reset", stdout=subprocess.PIPE, shell=True)
    process1.communicate()
    process2 = subprocess.Popen("sudo /etc/init.d/bluetooth restart", stdout=subprocess.PIPE, shell=True)
    process2.communicate()
    process3 = subprocess.Popen("sudo hciconfig hci0 up", stdout=subprocess.PIPE, shell=True)
    process3.communicate()

def ble_scanner():
    global beacons_detected
    dev_id = 0
    usb_dongle_reset()

    try:
        sock = bluez.hci_open_dev(dev_id)
        #print ("ble thread started")
    except:
        print ("error accessing bluetooth device... restart in progress!")
        usb_dongle_reset()

    ble_scan.hci_le_set_scan_parameters(sock)
    ble_scan.hci_enable_le_scan(sock)
    beacons_detected = {}
    beacons_detected_scanned = {}
    beacons_detected_scanned_trimmed = {}
    SCANNING_FINISHED = False
    while (scan_beacon_data == True) and (not killer.kill_now):
        try:
            if SCANNING_FINISHED == True:
                beacons_detected = beacons_detected_scanned_trimmed
                SCANNING_FINISHED = False

            elif SCANNING_FINISHED == False:
                returnedList = ble_scan.parse_events(sock, 25)
                for beacon in returnedList:
                    MAC, RSSI, LASTSEEN = beacon.split(',')
                    beacons_detected_scanned[MAC] = [RSSI,LASTSEEN]
                # return beacons_detected ordered by timestamp ASC (tnx to: JkShaw - http://stackoverflow.com/questions/43715921/python3-ordering-a-complex-dict)
                # return "just" the last 150 results to prevent the end of the socket buffer (each beacon data is about 45 bytes)
                beacons_detected_scanned_trimmed = str(sorted(beacons_detected_scanned.items(), key=lambda x: x[1][1], reverse=True)[:150])

                SCANNING_FINISHED = True
                time.sleep(1)
        except:
            print ("failed restarting device... let's try again!")
            usb_dongle_reset()
            dev_id = 0
            sock = bluez.hci_open_dev(dev_id)
            ble_scan.hci_le_set_scan_parameters(sock)
            ble_scan.hci_enable_le_scan(sock)
            SCANNING_FINISHED = False
            time.sleep(1)

def read_battery_level():
    global scan_beacon_data
    global mode
    global devices_to_analize
    global batt_lev_detected
    global read_value_lock
    global min_inval_between_batt_level_readings
    global batt_need_update
    #uuid_to_check = '0x2a19'
    uuid_to_check = '0xfffa'
    time_difference = 0
    while (not killer.kill_now):
        if mode == 'battery_level' and read_value_lock == False and batt_need_update == True:
            read_value_lock = True
            scan_beacon_data = False
            print ("Dispositivi da analizzare: " + str(devices_to_analize))
            for device in devices_to_analize:
                device_to_connect = device
                usb_dongle_reset()

                print ("ESEGUO: sudo hcitool lecc " + str(device_to_connect))
                process_get_connection_ID = subprocess.Popen("sudo hcitool lecc " + str(device_to_connect) + " | awk '{print $3}'", stdout=subprocess.PIPE, shell=True)
                handle_ble, err = process_get_connection_ID.communicate()

                print("ESEGUO sudo hcitool ledc " + str(handle_ble))
                process_connect = subprocess.Popen("sudo hcitool ledc " + str(handle_ble), stdout=subprocess.PIPE, shell=True)
                handle_ble_connect, err = process_connect.communicate()

                print("ESEGUO sudo gatttool --char-read --uuid " + str(uuid_to_check) + " -b " + str(device_to_connect) + " | awk '{print $4}'")
                process_ble_value = subprocess.Popen("sudo gatttool --char-read --uuid " + str(uuid_to_check) + " -b " + str(device_to_connect) + " | awk '{print $4}'", stdout=subprocess.PIPE, shell=True)
                ble_value, err = process_ble_value.communicate()
                #handle_ble = os.popen("sudo hcitool lecc " + device_to_connect + " | awk '{print $3}'").read()
                #print (str(handle_ble))
                #handle_ble_connect = os.popen("sudo hcitool ledc " + handle_ble).read()
                #ble_value = os.popen("sudo gatttool --char-read --uuid " + uuid_to_check + " -b " + device_to_connect + " | awk '{print $4}'").read()
                #NUT handle_ble = os.popen("sudo hcitool lecc --random " + device_to_connect + " | awk '{print $3}'").read()
                #NUT #handle_ble_connect = os.popen("sudo hcitool ledc " + handle_ble).read()
                #NUT #ble_value = os.popen("sudo gatttool -t random --char-read --uuid " + uuid_to_check + " -b " + device_to_connect + " | awk '{print $4}'").read()
                print ("Value got from device " + str(device_to_connect) + " is: " + str(ble_value))
            read_value_lock = False
            #AS SOON AS IT FINISH RESTART THE scan_beacon_data PROCESS
            scan_beacon_data = True
            mode = 'beacon_data'
            Thread(target=ble_scanner).start()
        time.sleep(1)

def start_server():
    global soc
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # this is for easy starting/killing the app
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #print('Socket created')
    try:
        soc.bind((socket_ip, socket_port))
    #    print('Socket bind complete')
    except socket.error as msg:
    #    print('Bind failed. Error : ' + str(sys.exc_info()))
        sys.exit()


    #Start listening on socket
    soc.listen(10)
    #print('Socket now listening')

    # for handling task in separate jobs we need threading
    #from threading import Thread

    # this will make an infinite loop needed for
    # not reseting server for every client
    while (not killer.kill_now):
        conn, addr = soc.accept()
        ip, port = str(addr[0]), str(addr[1])
        #print('Accepting connection from ' + ip + ':' + port)
        try:
            Thread(target=client_thread, args=(conn, ip, port)).start()
        except:
            print("Terible error!")
            import traceback
            traceback.print_exc()
    soc.close()

def kill_socket():
    global soc
    global kill_now
    kill_socket_switch = False
    while (not kill_socket_switch):
        if killer.kill_now:
            print ("KILL_SOCKET PROVA A CHIUDERE IL SOCKET")
            time.sleep(1)
            soc.shutdown(socket.SHUT_RDWR)
            soc.close()
            kill_socket_switch = True
        time.sleep(1)

### MAIN PROGRAM ###
class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    global soc
    self.kill_now = True
    print ('Program stopping...')

if __name__ == '__main__':
    killer = GracefulKiller()
    Thread(target=start_server).start()
    Thread(target=ble_scanner).start()
    Thread(target=read_battery_level).start()
    Thread(target=kill_socket).start()
#  print ("End of the program. I was killed gracefully")
