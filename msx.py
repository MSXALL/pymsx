#! /usr/bin/python3

import sys
import threading
import time
from disk import disk
from gen_rom import gen_rom
from pagetype import PageType
from scc import scc
from z80 import z80
from screen_kb import screen_kb

io = [ 0 ] * 256

subpage = 0x00

fh = open('msxbiosbasic.rom', 'rb')
rom0 = [ int(b) for b in fh.read(16384) ]
rom1 = [ int(b) for b in fh.read(16384) ]
fh.close()

def debug(x):
    global subpage
    dk.debug('%s <%02x/%02x>' % (x, io[0xa8], subpage))
    print('%s <%02x/%02x>' % (x, io[0xa8], subpage), file=sys.stderr)

scc_sig = None
#scc_rom_file = 'md1.rom'
#scc_obj = scc(scc_rom_file, debug) if scc_rom_file else None
#scc_sig = scc_obj.get_signature() if scc_obj else None

disk_sig = None
disk_rom_file = 'FSFD1.ROM'
disk_image_file = 'nondos.dsk'
disk_obj = disk(disk_rom_file, debug, disk_image_file) if disk_rom_file else None
disk_sig = disk_obj.get_signature() if disk_obj else None

gen_sig = None
#gen_rom_file = None
#gen_obj = gen_rom(gen_rom_file, debug) if gen_rom_file else None
#gen_sig = gen_obj.get_signature() if gen_obj else None

subpage = 0x00

ram0 = [ 0 ] * 16384
ram1 = [ 0 ] * 16384
ram2 = [ 0 ] * 16384
ram3 = [ 0 ] * 16384

slots = [ ] # slots
slots.append(( (rom0, PageType.ROM), None, None, (ram0, PageType.RAM) ))
slots.append(( (rom1, PageType.ROM), disk_sig if disk_sig else gen_sig, scc_sig, (ram1, PageType.RAM) ))
slots.append(( None, None, scc_sig, (ram2, PageType.RAM) ))
slots.append(( None, None, None, (ram3, PageType.RAM) ))

pages = [ 0, 0, 0, 0]

def read_mem(a):
    global subpage

    if a == 0xffff:
        return subpage

    page = a >> 14

    if slots[page][pages[page]] == None:
        return 0xee

    if slots[page][pages[page]][1] == PageType.SCC:
        obj = slots[page][pages[page]][2]
        return obj.read_mem(a)

    if slots[page][pages[page]][1] == PageType.DISK:
        obj = slots[page][pages[page]][2]
        return obj.read_mem(a)

    return slots[page][pages[page]][0][a & 0x3fff]

def write_mem(a, v):
    global subpage

    assert v >= 0 and v <= 255

    if a == 0xffff:
        subpage = v
        return

    page = a >> 14

    if slots[page][pages[page]] == None:
        debug('Writing %02x to %04x which is not backed by anything' % (v, a))
        return
    
    if slots[page][pages[page]][1] == PageType.ROM:
        debug('Writing %02x to %04x which is ROM' % (v, a))
        return
    
    if slots[page][pages[page]][1] == PageType.SCC:
        obj = slots[page][pages[page]][2]
        obj.write_mem(a, v)
        return
    
    if slots[page][pages[page]][1] == PageType.DISK:
        obj = slots[page][pages[page]][2]
        obj.write_mem(a, v)
        return

    slots[page][pages[page]][0][a & 0x3fff] = v

def read_io(a):
    debug('Get I/O register %02x' % a)

    if (a >= 0x98 and a <= 0x9b) or a == 0xa9:
        return dk.read_io(a)

    if a == 0xa8:
        return (pages[3] << 6) | (pages[2] << 4) | (pages[1] << 2) | pages[0]

    return io[a]
 
def write_io(a, v):
    assert v >= 0 and v <= 255

    debug('Set I/O register %02x to %02x' % (a, v))

    if a >= 0x98 and a <= 0x9b:
        dk.write_io(a, v)
        return

    if a == 0xa8:
        for i in range(0, 4):
            pages[i] = (v >> (i * 2)) & 3

    io[a] = v

stop_flag = False

def cpu_thread():
    #t = time.time()
    #while time.time() - t < 5:
    while not stop_flag:
        cpu.step()

cpu = z80(read_mem, write_mem, read_io, write_io, debug)

dk = screen_kb(cpu, io)
dk.start()

t = threading.Thread(target=cpu_thread)
t.start()

try:
    t.join()

except KeyboardInterrupt:
    stop_flag = True
    t.join()

dk.stop()
