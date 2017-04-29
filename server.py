#!/usr/bin/python3
import socket
from lib import ble_scan
from threading import Thread
import sys
import os
import time
import bluetooth._bluetooth as bluez
import signal
import subprocess

mode = ''
mybeacon = ''
mybattery = ''
beaconing = True
ble_value = ''
devices_to_analize = {}
mybattery = {}

def do_some_stuffs_with_input(input_string):
    global mode
    """
    This is where all the processing happens.
    """
    if input_string == 'beacon_data':
        #print("sending beacon data!")
        if beaconing == False:
            return str('Scanning stopped by other function')
        if beaconing == True:
            mode = 'beacon_data'
            return str(mybeacon)

    if input_string.startswith('battery_level:'):
        string_devices_to_analize = input_string.replace("battery_level: ", "")
        devices_to_analize = string_devices_to_analize.split(',')
        mode = 'battery_level'
        if ble_value == '':
            return str('evaluating')
        if ble_value != '':
            return str(mybattery)

    if input_string == 'stop':
        killer.kill_now = True
        return str('Service stopping')

def client_thread(conn, ip, port, MAX_BUFFER_SIZE = 4096):

    # the input is in bytes, so decode it
    input_from_client_bytes = conn.recv(MAX_BUFFER_SIZE)

    # MAX_BUFFER_SIZE is how big the message can be
    # this is test if it's sufficiently big
    siz = sys.getsizeof(input_from_client_bytes)
    if  siz >= MAX_BUFFER_SIZE:
        print("The length of input is probably too long: {}".format(siz))

    # decode input and strip the end of line
    input_from_client = input_from_client_bytes.decode("utf8").rstrip()

    res = do_some_stuffs_with_input(input_from_client)
    #print("Result of processing {} is: {}".format(input_from_client, res))

    vysl = res.encode("utf8")  # encode the result string
    conn.sendall(vysl)  # send it to client
    conn.close()  # close connection
    #print('Connection ' + ip + ':' + port + " ended")

def ble_scanner():
    global mybeacon
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
    mybeacon = {}
    while beaconing == True:
        if killer.kill_now:
            break
        try:
            returnedList = ble_scan.parse_events(sock, 25)
            for beacon in returnedList:
                MAC, RSSI, LASTSEEN = beacon.split(',')
                mybeacon[MAC] = [RSSI,LASTSEEN]
            time.sleep(1)
        except:
            print ("failed restarting device…")
            os.system("sudo hciconfig hci0 down")
            os.system("sudo hciconfig hci0 reset")
            print (ble_value)
            print (mode)
            print (beaconing)
            dev_id = 0
            os.system("sudo /etc/init.d/bluetooth restart")
            time.sleep(1)
            os.system("sudo hciconfig hci0 up")
            sock = bluez.hci_open_dev(dev_id)
            ble_scan.hci_le_set_scan_parameters(sock)
            ble_scan.hci_enable_le_scan(sock)
            time.sleep(2)

def read_battery_level():
    global beaconing
    global mode
    global mybattery
    while True:
        if mode == 'battery_level':
            print devices_to_analize
            for device in devices_to_analize:
                device_to_connect = device
                print (devices_to_analize)
                print (device)
                uuid_to_check = '0x2a19'
                beaconing = False
                os.system("sudo hciconfig hci0 down")
                os.system("sudo hciconfig hci0 reset")
                os.system("sudo /etc/init.d/bluetooth restart")
                time.sleep(1)
                os.system("sudo hciconfig hci0 up")
                #PUT HERE THE CODE TO READ THE BATTERY LEVEL
                handle_ble = os.popen("sudo hcitool lecc --random " + device_to_connect + " | awk '{print $3}'").read()
                handle_ble_connect = os.popen("sudo hcitool ledc " + handle_ble).read()
                ble_value = int(os.popen("sudo gatttool -t random --char-read --uuid " + uuid_to_check + " -b " + device_to_connect + " | awk '{print $4}'").read() ,16)
                time_checked = str(int(time.time()))

                mybattery[device] = [ble_value,time_checked]
                print (mybattery)
                
            #AS SOON AS IT FINISH RESTART THE BEACONING PROCESS
            beaconing = True
            mode = 'beacon_data'
            Thread(target=ble_scanner).start()
        time.sleep(1)


def start_server():
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # this is for easy starting/killing the app
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #print('Socket created')

    try:
        soc.bind(("10.50.0.55", 12345))
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