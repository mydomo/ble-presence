# BLE-Presence (Server + Client version)

BLE-Presence it's Client/Server software that allow to scan all the BLE beacons/request battery level using one or more servers (a small Raspberry Pi v1 is more than enought ) and read the results thru multiple clients.
Due to the architecture the **Server part can be installed on Linux only** (tested Ubuntu & Raspian Stretch).
The Client can be installed on any OS capable of interpret Python 3 (or other languages, depending on the client)
> **Before going forward in the reading and consider installing it, please consider that this software is in a TRUE EARLY STAGE of development and it's not recommended the installation.**
> Feel free to use it, but at your own risk.

## How does it work?
### Server:
  - Constantly scan the BLE devices
  - Is able to request batery level of the devices
  - Output all those informations thru a socket that can be opened by all the clients to read the required data

### Clients:
  - Open a soket to the specified server
  - Read informations about BLE DEVICES
  - Ask to the specified server about BLE DEVICES (ex: battery level)

**Both Server and Client scripts can be installed in the same machine**

# Installation process (Server Part):
Due to the architecture the **Server part can be installed on Linux only** (tested Ubuntu & Raspian Stretch).

Clone the repository on your machine:
```sh
$ git clone https://github.com/mydomo/ble-presence.git
$ cd ble-presence
```
Install the dependencies required:
```sh
$ sudo apt-get install -y libbluetooth-dev bluez
$ sudo apt-get install python-dev python3-dev python3-setuptools python3-pip
$ sudo pip3 install pybluez
```
Create the service:
```sh
$ sudo nano /etc/systemd/system/bleserver.service
```
Copy and paste the following, **but remember to EDIT IT in order to match your current home folder**. (ExecStart=/home/**pi**/ble-presence/server.py and WorkingDirectory=/home/**pi**/ble-presence)
```sh
[Unit]
Description=BLE Python Socket Server
After=multi-user.target

[Service]
Type=simple
ExecStart=/home/pi/ble-presence/server.py
User=root
WorkingDirectory=/home/pi/ble-presence
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
**CTRL + X** to save it.

Enable the service:
```sh
$ systemctl enable bleserver.service
```
Reboot the machine and you are done!

### To manually start/stop/remove the service:
To manual start the service:
```sh
$ systemctl start bleserver.service
```
To manual stop the service:
```sh
$ systemctl stop bleserver.service
```
To remove the service:
```sh
$ systemctl disable bleserver.service
```
### References

BLE-Presence uses a number of open source projects to work properly and many fonts of inspirations:

* [RasPi-iBeacons] - Part of the cose used for the server part.
* [Reddit Community] - Spiral6 post on how to create a service.

And of course BLE-Presence itself is open source with a [public repository] on GitHub.

# Clients

BLE-Presence is currently extended with the following clients.

| Client | Location | How to install |
| ------ | ------ | ------ |
| Domoticz | /plugin.py | coming soon |
| PHP | /clients/PHP | coming soon |
| PYTHON | /clients/PYTHON | coming soon |

## Todos

 - Pythonize and clean the code
 - Create different repository for server only/client only installs.

License
----

coming soon

**Free Software, Hell Yeah!**

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)

   [RasPi-iBeacons]: <https://github.com/flyinactor91/RasPi-iBeacons>
   [Reddit Community]: <https://www.reddit.com/r/raspberry_pi/comments/4vhofs/creating_a_systemd_daemon_so_you_can_run_a_python/>
   [public repository]: <https://github.com/mydomo/ble-presence>
