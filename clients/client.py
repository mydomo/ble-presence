# client.py

import socket

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
soc.connect(("10.50.0.55", 12345))

clients_input = "beacon_data" 
soc.send(clients_input.encode()) # we must encode the string to bytes  
result_bytes = soc.recv(32768) # the number means how the response can be in bytes  
result_string = result_bytes.decode("utf8") # the return will be in bytes, so decode

print("Result from server is {}".format(result_string))
print(" ")
print("ora la elaboro:")
print("ELIMINO LE PARENTESI QUADRE DI INIZIO E FINE")
if result_string.startswith('[') and result_string.endswith(']'):
    result_string = result_string[1:-1]
    print (result_string)
    print ("Elimino le tonde di inizio:")
    result_string = result_string.replace("(", "")
    print (result_string)
print("ORA DIVIDO LA PRIMA VOLTA")
print(result_string.split("), "))
items = result_string.split("), ")
for item in items:
    item.replace("'", "")
    print (item)
