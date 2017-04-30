#!/usr/bin/python3

#################################################################################
#  BLE PRESENCE FOR DOMOTICZ                                                    #
#                                                                               #
#  AUTHOR: MARCO BAGLIVO (ITALY) (https://github.com/mydomo)                    #
#                                                                               #
#################################################################################
# BLE_SCAN LIBRARY IS A FORK OF https://github.com/flyinactor91/RasPi-iBeacons  #
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

##########- CONFIGURE TRANSLATIONS -##########
lang_SCAN_STOPPED = 'Scanning stopped by other function'
lang_READING_LOCK = 'Reading in progress...'
lang_READING_START = 'Reading started'


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
            return str(beacons_detected)
            #return str(OrderedDict(sorted(beacons_detected.items(), key=lambda t: t[0])))


    ###- TRANSMIT BATTERY LEVEL -###
    # check if the request start with battery_level:
    if input_string.startswith('battery_level:'):
        # trim "battery_level:" from the request
        string_devices_to_analize = input_string.replace("battery_level: ", "")
        # split each MAC address in a list in order to be processed
        devices_to_analize = string_devices_to_analize.split(',')
        # set operative mode to battery_level
        mode = 'battery_level'
        
        # if the reading has already requested and there is no result ask to wait
        if not batt_lev_detected and read_value_lock == True:
            return str(lang_READING_LOCK)

        # if the reading is requested for the first time start say that will start
        elif not batt_lev_detected and read_value_lock == False:
            return str(lang_READING_START)

        # if is present a battery data send it
        else:
            return str(batt_lev_detected)

    ###- STOP RUNNING SERVICES -###
    if input_string == 'stop':
        killer.kill_now = True
        return str('Service stopping')
##########- END FUNCTION THAT HANDLE CLIENT INPUT -##########

##########- START FUNCTION THAT HANDLE SOCKET'S TRANSMISSION -##########
def client_thread(conn, ip, port, MAX_BUFFER_SIZE = 32768):

    # the input is in bytes, so decode it
    input_from_client_bytes = conn.recv(MAX_BUFFER_SIZE)

    # MAX_BUFFER_SIZE is how big the message can be
    # this is test if it's too big
    siz = sys.getsizeof(input_from_client_bytes)
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

def ble_scanner():
    global beacons_detected
    dev_id = 0
    os.system("sudo /etc/init.d/bluetooth restart")
    time.sleep(1)
    os.system("sudo hciconfig hci0 up")

    try:
        sock = bluez.hci_open_dev(dev_id)
        #print ("ble thread started")
    except:
        print ("error accessing bluetooth device…")
        print ("riavvio in corso...")
        os.system("sudo /etc/init.d/bluetooth restart")
        time.sleep(1)
        os.system("sudo hciconfig hci0 up")
    ble_scan.hci_le_set_scan_parameters(sock)
    ble_scan.hci_enable_le_scan(sock)
    beacons_detected = {}
    while scan_beacon_data == True:
        if killer.kill_now:
            break
        try:
            returnedList = ble_scan.parse_events(sock, 25)
            for beacon in returnedList:
                MAC, RSSI, LASTSEEN = beacon.split(',')
                beacons_detected[MAC] = [RSSI,LASTSEEN]
            time.sleep(1)
        except:
            print ("failed restarting device…")
            os.system("sudo hciconfig hci0 down")
            os.system("sudo hciconfig hci0 reset")
            print (ble_value)
            print (mode)
            print (scan_beacon_data)
            dev_id = 0
            os.system("sudo /etc/init.d/bluetooth restart")
            time.sleep(1)
            os.system("sudo hciconfig hci0 up")
            sock = bluez.hci_open_dev(dev_id)
            ble_scan.hci_le_set_scan_parameters(sock)
            ble_scan.hci_enable_le_scan(sock)
            time.sleep(2)

def read_battery_level():
    global scan_beacon_data
    global mode
    global batt_lev_detected
    global read_value_lock
    while True:
        if mode == 'battery_level' and read_value_lock == False:
            read_value_lock = True
            print (devices_to_analize)
            for device in devices_to_analize:
                device_to_connect = device
                print ("Dispositivi da analizzare: " + str(devices_to_analize))
                print ("Analizzo dispositivo: " + str(device))
                uuid_to_check = '0x2a19'
                scan_beacon_data = False
                os.system("sudo hciconfig hci0 down")
                time.sleep(1)
                os.system("sudo hciconfig hci0 reset")
                os.system("sudo /etc/init.d/bluetooth restart")
                time.sleep(1)
                os.system("sudo hciconfig hci0 up")
                #PUT HERE THE CODE TO READ THE BATTERY LEVEL
                try:
                    handle_ble = os.popen("sudo hcitool lecc --random " + device_to_connect + " | awk '{print $3}'").read()
                    handle_ble_connect = os.popen("sudo hcitool ledc " + handle_ble).read()
                    #ble_value = int(os.popen("sudo gatttool -t random --char-read --uuid " + uuid_to_check + " -b " + device_to_connect + " | awk '{print $4}'").read() ,16)
                    ble_value = os.popen("sudo gatttool -t random --char-read --uuid " + uuid_to_check + " -b " + device_to_connect + " | awk '{print $4}'").read()
                except:
                    ble_value = 'nd'

                if ble_value != '':
                    ble_value = int(ble_value ,16)

                if ble_value == '':
                    ble_value = '255'    
                time_checked = str(int(time.time()))
                batt_lev_detected[device] = [ble_value,time_checked]
                read_value_lock = False
                print (batt_lev_detected)
                
            #AS SOON AS IT FINISH RESTART THE scan_beacon_data PROCESS
            scan_beacon_data = True
            mode = 'beacon_data'
            Thread(target=ble_scanner).start()
        time.sleep(1)


def start_server():
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # this is for easy starting/killing the app
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #print('Socket created')
    try:
        soc.bind(('0.0.0.0', 12345))
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
    while True:
        if killer.kill_now:
            break
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

### MAIN PROGRAM ###
class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True

if __name__ == '__main__':
    killer = GracefulKiller()
    Thread(target=start_server).start()
    Thread(target=ble_scanner).start()
    Thread(target=read_battery_level).start()
#  print ("End of the program. I was killed gracefully :)")