# client.py

import socket

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
soc.connect(("10.50.0.55", 12345))

clients_input = "beacon_data" 
soc.send(clients_input.encode()) # we must encode the string to bytes  
result_bytes = soc.recv(32768) # the number means how the response can be in bytes  
result_string = result_bytes.decode("utf8") # the return will be in bytes, so decode

#print("Result from server is {}".format(result_string))


# START THE INPUT CLEANING FOR BEACONING DATA:
# REMOVE '[', ']' AND '(' FROM THE RECEIVED STRING
if result_string.startswith('[') and result_string.endswith(']'):
    result_string = result_string[1:-1].replace("(", "")
# RECURSIVE SPLIT THE STRING TO GET THE DATA:
items = result_string.split("), ")
for item in items:
    bucket = item.split("', ['")
    BLE_MAC = bucket[0].replace("'", "")
    OTHER_DATA = bucket[1]
    print (BLE_MAC)
    print (OTHER_DATA)
    print ("----------")
