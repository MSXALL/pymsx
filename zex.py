#! /usr/bin/python3

# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import sys
import time
from inspect import getframeinfo, stack
from z80 import z80
from screen_kb_dummy import screen_kb_dummy

io = [ 0 ] * 256

ram0 = [ 0 ] * 16384
ram1 = [ 0 ] * 16384
ram2 = [ 0 ] * 16384
ram3 = [ 0 ] * 16384

slots = [ ] # slots
slots.append(( ram0, None, None, None ))
slots.append(( ram1, None, None, None ))
slots.append(( ram2, None, None, None ))
slots.append(( ram3, None, None, None ))

pages = [ 0, 0, 0, 0]

def reset_mem():
    ram0 = [ 0 ] * 16384

def read_mem(a):
    page = a >> 14

    slot = slots[page][pages[page]]

    if slot == None:
        return 0xee

    return slot[a & 0x3fff]

def write_mem(a, v):
    global subpage

    page = a >> 14

    slot = slots[page][pages[page]]

    if slot == None:
        return

    slot[a & 0x3fff] = v

def read_io(a):
    return io[a]
 
def write_io(a, v):
    io[a] = v

def debug(x):
    pass

dk = screen_kb_dummy(io)
dk.start()

cpu = z80(read_mem, write_mem, read_io, write_io, debug, dk)

fh = open('zexall.com', 'rb')
zex = [ int(b) for b in fh.read() ]
fh.close()

p = 0x0100
for b in zex:
    write_mem(p, b)
    p += 1

cpu.sp = 0xf000
cpu.pc = 0x0100

while True:
    if cpu.pc == 0x0005:
        if cpu.c == 2:
            print('%c' % cpu.e, end='', flush=True)

        elif cpu.c == 9:
            a = cpu.m16(cpu.d, cpu.e)

            while True:
                c = cpu.read_mem(a)
                if c == ord('$'):
                    break

                print('%c' % c, end='', flush=True)

                a += 1

        cpu._ret(True, 'bla')

        continue

    cpu.step()
