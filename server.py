# server.py

def do_some_stuffs_with_input(input_string):  
    """
    This is where all the processing happens.

    Let's just read the string backwards
    """
    if input_string == 'beacon_data':
    	print("sending beacon data!")
    	return mybeacon
    #return input_string[::-1]

def client_thread(conn, ip, port, MAX_BUFFER_SIZE = 4096):

    # the input is in bytes, so decode it
    input_from_client_bytes = conn.recv(MAX_BUFFER_SIZE)

    # MAX_BUFFER_SIZE is how big the message can be
    # this is test if it's sufficiently big
    import sys
    siz = sys.getsizeof(input_from_client_bytes)
    if  siz >= MAX_BUFFER_SIZE:
        print("The length of input is probably too long: {}".format(siz))

    # decode input and strip the end of line
    input_from_client = input_from_client_bytes.decode("utf8").rstrip()

    res = do_some_stuffs_with_input(input_from_client)
    print("Result of processing {} is: {}".format(input_from_client, res))

    vysl = res.encode("utf8")  # encode the result string
    conn.sendall(vysl)  # send it to client
    conn.close()  # close connection
    print('Connection ' + ip + ':' + port + " ended")

def start_server():
	from lib import ble_scan
	import sys
	import os
	import time
	import bluetooth._bluetooth as bluez

	import socket

	dev_id = 0

	os.system("sudo /etc/init.d/bluetooth restart")
	time.sleep(1)
	os.system("sudo hciconfig hci0 up")

	try:
		sock = bluez.hci_open_dev(dev_id)
		print ("ble thread started")

	except:
		print ("error accessing bluetooth device…")
		print ("riavvio in corso...")
		os.system("sudo /etc/init.d/bluetooth restart")
		time.sleep(1)
		os.system("sudo hciconfig hci0 up")
		#sys.exit()

	ble_scan.hci_le_set_scan_parameters(sock)
	ble_scan.hci_enable_le_scan(sock)
	mybeacon = {}


    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # this is for easy starting/killing the app
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print('Socket created')

    try:
        soc.bind(("10.50.0.55", 12345))
        print('Socket bind complete')
    except socket.error as msg:
        import sys
        print('Bind failed. Error : ' + str(sys.exc_info()))
        sys.exit()

    #Start listening on socket
    soc.listen(10)
    print('Socket now listening')

    # for handling task in separate jobs we need threading
    from threading import Thread

    # this will make an infinite loop needed for 
    # not reseting server for every client
    while True:
    	returnedList = ble_scan.parse_events(sock, 25)
    	for beacon in returnedList:
		MAC, RSSI, LASTSEEN = beacon.split(',')
		#print (MAC)
		#print (RSSI)
		#print (LASTSEEN)
		mybeacon[MAC] = [RSSI,LASTSEEN]

        conn, addr = soc.accept()
        ip, port = str(addr[0]), str(addr[1])
        print('Accepting connection from ' + ip + ':' + port)
        try:
            Thread(target=client_thread, args=(conn, ip, port)).start()
        except:
            print("Terible error!")
            import traceback
            traceback.print_exc()
    soc.close()

start_server() 