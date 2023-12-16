#!/usr/bin/env python
#-*- coding: utf-8 -*-

LDRNAME="konekoldr.bas"

import serial, time
from argparse import ArgumentParser

def hex_int(x):
    return int(x, 16)

parser = ArgumentParser(prog='KONEKO', description="Load asm binary to MSX over serial")
parser.add_argument('-lb', '--baud', dest='ldrbaud', type=int, help="Baud to use in loader", default=9600)
parser.add_argument('-db', '--default-baud', dest='defbaud', type=int, help="Baud to use to bootstrap", default=1200)
parser.add_argument('-a', '--address', dest='address', type=hex_int, help="Address for the program", default="b000")
parser.add_argument('-m', '--manual', dest='step', type=bool, help="Press enter before each step", default=False)
parser.add_argument('port')
parser.add_argument('binfile')
args = parser.parse_args()

with open(LDRNAME, 'r') as file:
    loader = file.read().format(ldrbaud=args.ldrbaud, dstaddr=args.address).replace("\n","\r\n")

if args.step:
    print("On MSX, start COMINI:LOAD\"com:\",R and press enter")
    raw_input()

ser = serial.Serial(args.port, args.defbaud, bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
ser.write(bytes(loader, 'ascii'))
ser.write(b'\x1A') # EOF
ser.flush()
ser.close()

if args.step:
    print("On MSX, make sure KonekoLoader is seen and press enter")
    raw_input()
else:
    time.sleep(3)

file=open(args.binfile,'rb').read()
ser = serial.Serial(args.port, args.ldrbaud, bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
for byte in file:
    ser.write(bytes(f"{byte:x}\r\n", 'ascii'))
    ser.flush()
    time.sleep(0.05)
ser.write(b'\x1A') # EOF
ser.flush()
ser.close()
