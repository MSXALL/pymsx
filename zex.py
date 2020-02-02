#! /usr/bin/python3

import sys
from inspect import getframeinfo, stack
from z80 import z80

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

    if slots[page][pages[page]] == None:
        return 0xee

    return slots[page][pages[page]][a & 0x3fff]

def write_mem(a, v):
    global subpage

    page = a >> 14

    if slots[page][pages[page]] == None:
        return

    slots[page][pages[page]][a & 0x3fff] = v

def read_io(a):
    return io[a]
 
def write_io(a, v):
    io[a] = v

def debug(x):
#    print('%s <%02x/%02x>' % (x, io[0xa8], 0), file=sys.stderr)
    pass

cpu = z80(read_mem, write_mem, read_io, write_io, debug)

fh = open('zexdoc.com', 'rb')
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

        cpu._ret(True, '')

        continue

    cpu.step()
