#! /usr/bin/env python3

"""
Copyright (c) 2016 Juha Kuikka
This file is part of pyble which is released under Modified BSD license
See LICENSE.txt for full license details
"""

import pyble
import struct
#import paho.mqtt.client as mqtt
from gi.repository import GLib
from gi.repository import GObject

#MQTT_SERVER = 'quickstart.messaging.internetofthings.ibmcloud.com'
MQTT_SERVER = 'localhost'
MQTT_CLIENT = None

#def publish(topic, key, value):
#    payload = '{"%s": %s}' % (str(key),str(value))
#    MQTT_CLIENT.publish( topic=topic, payload=payload )

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
#    client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


SRV_IR_TEMP_DATA = 'F000AA01-0451-4000-B000-000000000000'.casefold()
SRV_IR_TEMP_CFG  = 'F000AA02-0451-4000-B000-000000000000'.casefold()
SRV_HUM_DATA     = 'F000AA21-0451-4000-B000-000000000000'.casefold()
SRV_HUM_CFG      = 'F000AA22-0451-4000-B000-000000000000'.casefold()
SRV_BARO_DATA    = 'F000AA41-0451-4000-B000-000000000000'.casefold()
SRV_BARO_CFG     = 'F000AA42-0451-4000-B000-000000000000'.casefold()
SRV_BARO_CAL     = 'F000AA43-0451-4000-B000-000000000000'.casefold()

def get_object_temp(raw, ambient):
    Vobj2 = float(raw) * 0.00000015625
    Tdie = float(ambient) + 273.15;
    S0 = 5.593E-14  # // Calibration factor
    a1 = 1.75E-3
    a2 = -1.678E-5
    b0 = -2.94E-5
    b1 = -5.7E-7
    b2 = 4.63E-9
    c2 = 13.4
    Tref = 298.15
    S = S0*(1+a1*(Tdie - Tref)+a2*pow((Tdie - Tref),2))
    Vos = b0 + b1*(Tdie - Tref) + b2*pow((Tdie - Tref),2)
    fObj = (Vobj2 - Vos) + c2*pow((Vobj2 - Vos),2)
    tObj = pow(pow(Tdie,4) + (fObj/S),.25)

    return tObj - 273.15;

def get_humidity(humidity):
    humidity = humidity & 0xFFFC
    return float(-6) + float(125) * (float(humidity) / float(65535))

def get_hum_temp(temp):
     return float(-46.85) + float(175.72)/float(65536) * temp

def sensortag_humidity_value(char, prop, val):
    temp = get_hum_temp(float(val[0] + 255 * val[1]))
    humidity = get_humidity(val[2] + 255 * val[3])
    #print( 'Sensortag humidity:{}, temp:{}'.format(humidity, temp) )
    #client.publish( topic='iot-2/evt/helloworld/fmt/json', payload=payload )
    publish( topic='sensortag', key='temperature', value=temp )
    publish( topic='sensortag', key='humidity', value=humidity )


def sensortag_ir_value(char, prop, val):
#    print( 'Sensortag IR {}: {}'.format(prop, val))
    ambient = float( val[2] + 255 * val[3] )
    ambient = ambient / 128.0
    object_tmp = get_object_temp(val[0] + 255 * val[1], ambient)
    #print( 'Sensortag IR object:{} ambient:{}'.format(object_tmp, ambient))

def sensortag_baro_cal(char, prop, val):
    print( 'BAROMETER CAL: {}'.format(val))
    cfg = pyble.get_characteristic( SRV_BARO_CFG )
    cfg.WriteValue( 1 )

def sensortag_barometer_value(char, prop, val):
    pass
    #print( 'Sensortag barometer {}: {}'.format(prop, val))


def sensortag_connected(dev, prop, val):
    print( 'Sensortag {}: {}'.format(prop, val))
    if dev.Connected and dev.ServicesResolved:
        sensortag_configure(dev)

def sensortag_configure(dev):
    for s in dev.services():
        for c in s.characteristics():
            uuid = c.UUID.casefold()
            if uuid == SRV_IR_TEMP_CFG or uuid == SRV_HUM_CFG:
                print( c )
                c.WriteValue( [ 1 ] )
            elif uuid == SRV_BARO_CFG:
                print( 'Baro CFG found: {}'.format(c) )
                c.WriteValue( [ 2 ] )
            elif uuid == SRV_BARO_CAL:
                print( 'Baro CAL found: {}'.format(c) )
                c.RegisterForPropertyChanged( 'Value', sensortag_baro_cal )
            elif uuid == SRV_IR_TEMP_DATA:
                print( c )
                c.StartNotify()
                c.RegisterForPropertyChanged( 'Value', sensortag_ir_value )
            elif uuid == SRV_HUM_DATA:
                print( c )
                c.StartNotify()
                c.RegisterForPropertyChanged( 'Value', sensortag_humidity_value )
            elif uuid == SRV_BARO_DATA:
                print( c )
                c.StartNotify()
                c.RegisterForPropertyChanged( 'Value', sensortag_barometer_value )

def on_message_received(a, b):
    if b & GObject.IO_IN:
        MQTT_CLIENT.loop_read()
    elif b & GObject.IO_OUT:
        MQTT_CLIENT.loop_write()

def init_mqtt():
    global MQTT_CLIENT
    MQTT_CLIENT = mqtt.Client( client_id='d:quickstart:mosquitto:019283hb' )
    MQTT_CLIENT.connect( MQTT_SERVER )

    MQTT_CLIENT.on_connect = on_connect
    MQTT_CLIENT.on_message = on_message

    GObject.io_add_watch(MQTT_CLIENT.socket().makefile(), GObject.IO_IN | GObject.IO_OUT, on_message_received)

def on_device_added(d):
    print( 'Device added: {}'.format(d))
    on_new_device(d)

def on_new_device(d):
    print( 'found {}'.format(d))
    if d.Name == 'TI BLE Sensor Tag':
        print( 'found sensortag' )
        d.RegisterForPropertyChanged( 'Connected', sensortag_connected )
        d.RegisterForPropertyChanged( 'ServicesResolved', sensortag_connected )
        d.RegisterForPropertyChanged( 'GattServices', sensortag_connected )
        if d.Connected:
            print( 'already connected!' )
            sensortag_configure(d)
        else:
            d.Connect()

def main():
#    init_mqtt()
    pyble.set_on_device_added_listener(on_device_added)

    for d in pyble.devices():
        on_new_device(d)

    print( 'Discovery starting' )
    for a in pyble.adapters():
        a.StartDiscovery()

    print( 'Run mainloop!' )
    loop = GLib.MainLoop()
    loop.run()

main()