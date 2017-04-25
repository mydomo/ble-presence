#!/usr/bin/python3
from threading import Thread

class myClass(Thread):
    def run(self):
        print ('Starting ')
        while(True):
            print ('1')

class myClassSecond(Thread):
    def run(self):
        print ('starting second')
        while(True):
            print ('2')

if __name__=='__main__':
    a=myClass()
    b=myClassSecond()
    a.start()
    b.start()