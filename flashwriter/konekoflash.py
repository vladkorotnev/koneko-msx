#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Koneko Flash Sequence
# 1. Load BASIC @ 1200baud
# 2. Reconnect at 9600baud, Load ASM
# 3. MSX check for Flash, if not found, send "N" and exit
# 4. MSX format Flash
# 5. MSX sends "A", PC sends address 0000 to 8000 (hex)
# 6. MSX sends "?", PC sends exactly 1000h bytes (1 sector)
# 7. MSX writes bytes to flash
# 8. MSX verifies bytes, if OK go to 6, if fail send "E" and exit
# 9. If no more bytes, PC sends "Q", MSX exits

LDRNAME="flashwr.bas"

import serial, time, pdb
from argparse import ArgumentParser

def hex_int(x):
    return int(x, 16)

parser = ArgumentParser(prog='KONEKOFLASH', description="Load asm binary to MSX over serial")
parser.add_argument('-a', '--address', dest='address', type=hex_int, help="Address for the ROM file starting", default="4000")
parser.add_argument('port')
parser.add_argument('binfile')

args = parser.parse_args()

with open(LDRNAME, 'r') as file:
    loader = file.read().replace("\n","\r\n")

with open(args.binfile, 'rb') as file:
    rom = file.read()

print("Send BAS...")
ser = serial.Serial(args.port, 1200, bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)
ser.write(bytes(loader, 'ascii'))
ser.write(b'\x1A') # EOF
ser.flush()
ser.close()

time.sleep(3)

print("Send PROG...")
file=open("prog.bin",'rb').read()
ser = serial.Serial(args.port, 9600, bytesize=8, parity='N', stopbits=1, timeout=None, xonxoff=0, rtscts=0)

def sendbin(bin):
    for byte in bin:
        ser.write(bytes(f"{byte:x}\r\n", 'ascii'))
        ser.flush()
        time.sleep(0.03)
    ser.write(b'Z\r\n') # EOF
    ser.flush()

def sendFinish():
    ser.write(bytes("Q\r\n", 'ascii'))
    ser.flush()

sendbin(file)

done = False
pos = 0
addr = args.address
sliceSize = 0x100


print("Entering COMM Loop")
while not done:
    line = ser.readline()
    # print(line)
    line = line.strip().replace(b"\x1A", b"").replace(b"\x00", b"")
    print("Receive: ", line)
    if line == b"A":
        tmp = pos + addr
        msb = ((tmp & 0xFF00) >> 8)
        lsb = tmp & 0xFF
        print("Done "+hex(pos)+" of "+hex(len(rom)))
        ser.write(bytes(f"{lsb:x}\r\n", 'ascii'))
        ser.write(bytes(f"{msb:x}\r\n", 'ascii'))
        ser.write(b'Z\r\n') # EOF
        ser.flush()
    elif line == b"?":
        if pos < len(rom):
            curSlice = rom[pos:pos + sliceSize]
            if len(curSlice) < sliceSize:
                curSlice = bytearray(curSlice)
                while len(curSlice) < sliceSize:
                    curSlice.append(0xFF)
            pos += sliceSize
            sendbin(curSlice)
        else:
            done = True
            sendFinish()
            print("Complete")
    elif line == b"N":
        done = True
        print("Flash Not Ready")
    elif line == b"E":
        done = True
        print("Writing Error: pos = ", hex(pos))