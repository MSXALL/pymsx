#! /usr/bin/python3

# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

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

def my_assert(r):
    if not r:
        print(cpu.reg_str())
        caller = getframeinfo(stack()[1][0])
        flags = ''
        for i in range(0, 8):
            if i == (7 - 5) or i == (7 - 3):
                flags += 'x'
            elif cpu.f & (128 >> i):
                flags += '1'
            else:
                flags += '0'
        print(flags)
        print('%s:%d' % (caller.filename, caller.lineno))
        sys.exit(1)

cpu = z80(read_mem, write_mem, read_io, write_io, debug)

# tests.in
# --------

# Each test has the format:

# <arbitrary test description>
# AF BC DE HL AF' BC' DE' HL' IX IY SP PC MEMPTR
# I R IFF1 IFF2 IM <halted> <tstates>

# <halted> specifies whether the Z80 is halted.
# <tstates> specifies the number of tstates to run the test for, in
#   decimal; the number actually executed may be higher, as the final
#   instruction is allowed to complete.

# Then followed by lines specifying the initial memory setup. Each has
# the format:

# <start address> <byte1> <byte2> ... -1

# eg

# 1234 56 78 9a -1

# says to put 0x56 at 0x1234, 0x78 at 0x1235 and 0x9a at 0x1236.

# Finally, -1 to end the test. Blank lines may follow before the next test.

fh = open('tests.in', 'r')

while True:
    cpu.reset()
    reset_mem()

    while True:
        descr = fh.readline()
        if not descr:
            break

        descr = descr.rstrip('\n').rstrip(' ')
        if descr != '':
            break
    if not descr:
        break
    print(descr)

    registers1 = fh.readline().rstrip('\n').rstrip(' ')
    parts = registers1.split()
    regs1 = [int(x, 16) for x in parts]
    (cpu.a, cpu.f) = cpu.u16(regs1[0])
    (cpu.b, cpu.c) = cpu.u16(regs1[1])
    (cpu.d, cpu.e) = cpu.u16(regs1[2])
    (cpu.h, cpu.l) = cpu.u16(regs1[3])
    (cpu.a_, cpu.f_) = cpu.u16(regs1[4])
    (cpu.b_, cpu.c_) = cpu.u16(regs1[5])
    (cpu.d_, cpu.e_) = cpu.u16(regs1[6])
    (cpu.h_, cpu.l_) = cpu.u16(regs1[7])
    cpu.ix = regs1[8]
    cpu.iy = regs1[9]
    cpu.sp = regs1[10]
    cpu.pc = regs1[11]

    registers2 = fh.readline().rstrip('\n').rstrip(' ')
    parts = registers2.split()
    # print(parts)
    regs2 = [int(x, 16) for x in parts]

    while True:
        setup = fh.readline()
        setup = setup.rstrip('\n')
        if setup == '-1':
            break

        parts = setup.split()
        if len(parts) == 0:
            break

        # print(parts)

        a = int(parts[0], 16)
        first = a

        for b in parts[1:]:
            if b == '':
                continue

            if b == '-1':
                break

            cpu.write_mem(a, int(b, 16)) 
            a += 1
            a &= 0xffff

    # print(regs2)

    for i in range(0, regs2[6]):
        cpu.step()
