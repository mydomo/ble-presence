#!/usr/bin/env python3
# client.py

import socket

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
soc.connect(("10.50.0.55", 12345))

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
result_string = result_bytes.decode("utf8") # the return will be in bytes, so decode

print (result_string)
print ("----------")
