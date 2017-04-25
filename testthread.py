#!/usr/bin/python3
from threading import Thread

def uno(self):
    print ('Starting ')
    while(True):
        print ('1')

def due(self):
    print ('starting second')
    while(True):
        print ('2')

if __name__=='__main__':
    Thread(target=uno).start()
    Thread(target=due).start()