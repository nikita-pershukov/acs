#!/usr/bin/python
__version__ = "0.6.0"

import json
import hashlib
import logging
from logging.handlers import RotatingFileHandler
import os
import re
import signal
import subprocess
import sys
import time
from datetime import date

import RPi.GPIO as GPIO

from pirc522 import RFID
from urllib import urlencode
from urllib2 import urlopen, URLError

from threading import Thread, RLock
import sched

class Scheduler(object):
    def __init__(self):
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.eventID = 0

    def setup(self, interval, action, action_args=()):
        self.eventID = self.scheduler.enter(interval, 1, action, action_args)

    def run(self):
        self.thread = Thread(target=self.scheduler.run)
        self.thread.start()

    def stop(self):
        if not self.scheduler.empty():
            self.scheduler.cancel(self.eventID)
class Opener(object):

    def __init__(self, pin, unlock_time):
        self.pin = pin
        self.unlock_time = unlock_time

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.IN)
        
        self.active = True
        self.listening = True

        self.chk_loop = Thread(target=self.__check_pin_loop)

        self.sched = Scheduler()

        self.lock = RLock()

    def start(self):
        self.chk_loop.start()

    def stop(self):
        self.active = False
        self.sched.stop()
        GPIO.cleanup()

    def unlock(self):
        self.lock.acquire()

        self.listening = False

        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.HIGH)

        self.sched.stop()
        self.sched.setup(self.unlock_time, self.__lock)
        self.sched.run()

        self.lock.release()

    def __lock(self):
        self.lock.acquire()

        self.listening = True
        GPIO.setup(self.pin, GPIO.IN)

        self.lock.release()

    def __check_pin_loop(self):
        while self.active:
            self.lock.acquire()
            if self.listening:
                if GPIO.input(self.pin):
                    print("Button pressed")
                    self.unlock()
                    blink_led(env['python_blinks_butt'],env['python_unlock_time'],env['python_pin_led_b'])
            self.lock.release()
            time.sleep(0.1)

printer = None

if len(sys.argv) > 1:
    if sys.argv[1] == 'stdout':
        pass
    else:
        printer = open('stdout.log', 'a')

def write(what):
    if printer is None:
        print what
    else:
        print >>printer, what

def write(x):
    print(x)
env = dict()

def get_params(filename="config",invert=False):
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

    settings = open(filename)
    data = settings.readlines()
    out = dict()

    for i in data:
        try:
            temp = i.split()
            key = temp[0]
            value = "".join(temp[1:]).strip()
            if invert: key, value = value, key
            out[key] = value
        except Exception as e:
            write(e)

    settings.close()
    return out

def get_masters():
    resp = get_params("{}/{}".format(env["local_dir"],env["acs_masters"]), invert=True)
    # resp = resp.values()
    return resp

env['python_pin_lock'] = 40
env['python_pin_led'] = 18

env['total_lock_duration'] = 30 * 60
env['total_unlock_duration'] = 60

for i, j in get_params().items():
    env[i] = j

appLog = logging.getLogger('root')
appLog.setLevel(logging.INFO)

def update_logs_path():
    date_str = "python_{}.log".format(date.today())
    env['log_file'] = "{}/{}".format(env['local_logs_dir'],date_str)
    log_handler = RotatingFileHandler(env['log_file'], mode='a',
                                 maxBytes=50*1024*1024, backupCount=5, encoding=None, delay=0)
    
    log_formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
    log_handler.setFormatter(log_formatter)

    log_handler.setLevel(logging.INFO)
    log = logging.getLogger('root')

    for hdlr in log.handlers[:]:
        log.removeHandler(hdlr)
    log.addHandler(log_handler)

update_logs_path()

env['url'] = env['srv_web_addr'] + ':' + env['srv_web_port'] + '/rooms/check_access/' + env['device_name'][9:]+ '/{}'
env['python_pin_lock'] = int(env['python_pin_lock'])
env['python_pin_led_r'] = int(env['python_pin_led_r'])
env['python_pin_led_g'] = int(env['python_pin_led_g'])
env['python_pin_led_b'] = int(env['python_pin_led_b'])
env['python_blinks_good'] = int(env['python_blinks_good'])
env['python_blinks_bad'] = int(env['python_blinks_bad'])
env['python_blinks_butt'] = int(env['python_blinks_butt'])
env['python_unlock_time'] = int(env['python_unlock_time'])

env['total_lock_duration'] = int(env['total_lock_duration'])
env['total_unlock_duration'] = int(env['total_unlock_duration'])

opener = Opener(env['python_pin_lock'], env['python_unlock_time'])

masters = get_masters()

def hashed(pass_id):
    pass_id = pass_id.lower()
    pass_id += env['python_salt']
    for i in range(3):
        pass_id = hashlib.sha256(pass_id.encode()).hexdigest()
    return pass_id

def signal_handler(signal, frame):
    write("Closing RFID Door Lock Script")
    appLog.info("====== Closing RFID Door Lock Script ======")
    opener.stop()
    sys.exit(0)

def unlock_door():
    duration = env['python_unlock_time'] 
    write("Unlocking door for %d seconds" % duration)
    appLog.info("Unlocking door for %d seconds" % duration)
    opener.unlock()    

    write("Locking the door")
    appLog.info("Locking the door")

def unlock_global(signal, frame):
    appLog.info("Got total unlock signal, unlocking for %d seconds" % env['total_unlock_duration'])

    opener.unlock()

    write("Locking the door")
    appLog.info("Locking the door.")
    appLog.info("====== RESTART RFID Door Lock Script ======")
    exit(0)

def lock_global(signal, frame):
    appLog.info("Got total lock signal, locking for %d seconds" % env['total_lock_duration'])

    opener.unlock()

    appLog.info("Total lock ended, switching to a normal mode")
    appLog.info("====== RESTART RFID Door Lock Script ======")
    exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGUSR1, unlock_global)
signal.signal(signal.SIGUSR2, lock_global)


class Allowed:
    def __init__(self, url, token, masters=None):
        self.url = url
        self.token = urlencode({'token': token})
        self.masters = masters or {}

    def check(self, uid):
        return self.__check_access(uid)

    def __check_access(self, uid):
        try:
            if uid in self.masters.keys():
                r = "GRANTED"
                appLog.info("Master key for {}. UID:{}".format(self.masters[uid], uid))
            else:
                res = urlopen(self.url.format(hashed(uid)), self.token)
                r =  res.read()
            if r == 'INVALID':
                appLog.warn("Unknown UID")
            if r == 'DENIED':
                appLog.info("Access denied")
            if r == 'GRANTED':
                appLog.info("OK")
            return r == 'GRANTED'
        except URLError as e:
            appLog.critical(e)
            return False

class Reader:
    def __init__(self):
        self.reader = RFID()
    
    def reset(self):
        self.reader = RFID()

    def get(self):
        error, data = self.reader.request()
        if error:
            return None

        error, uid = self.reader.anticoll()
        if error:
            return None

        return ''.join('{:02x}'.format(byte) for byte in uid[:4])

def blink_led_fun(blinks, duration, led):
    GPIO.setup(led, GPIO.OUT)
    blink_duration = float(duration) / float(blinks)
    for i in range(blinks):
        GPIO.output(led, GPIO.HIGH)
        time.sleep(blink_duration/2)
        GPIO.output(led, GPIO.LOW)
        time.sleep(blink_duration/2)

def blink_led(blinks, duration, led):
    thread = Thread(target=blink_led_fun,args=(blinks, duration, led))
    thread.start()

def main():
    global masters
    global env

    reader = Reader()
    opener.start()
    
    allowed_ = Allowed(env['url'], env['python_token'], masters)
    continue_reading = True

    try:
        while continue_reading:
            reader.reader.wait_for_tag()
            uid = reader.get()
            update_logs_path()
            if uid:
                appLog.info('RFID card scanned: ' + uid)
                if allowed_.check(uid):
                    unlock_door()
                    blink_led(env['python_blinks_good'],env['python_unlock_time'],env['python_pin_led_g']) 
                    time.sleep(env['python_unlock_time'])
                else:
                    write('bad uid')
                    write(uid)
                    blink_led(env['python_blinks_bad'],env['python_unlock_time'],env['python_pin_led_r'])
                    time.sleep(env['python_unlock_time'])
            time.sleep(0.5)

    except Exception as e:
        write(e)
        appLog.critical(e)

    GPIO.cleanup()

if __name__ == '__main__':
    appLog.info("====== Starting RFID Lock Script ======")
    main()
