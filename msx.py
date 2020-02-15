#! /usr/bin/python3

# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import sys
import threading
import time
from disk import disk
from gen_rom import gen_rom
from pagetype import PageType
from scc import scc
from z80 import z80
from screen_kb import screen_kb
from sound import sound
from memmapper import memmap
from rom import rom

abort_time = None # 60

debug_log = 'debug.log' # None to disable

io_values = [ 0 ] * 256
io_read = [ None ] * 256
io_write = [ None ] * 256

subpage = 0x00

def debug(x):
    global subpage
    dk.debug('%s <%02x/%02x>' % (x, io_values[0xa8], subpage))

    if debug_log:
        fh = open(debug_log, 'a+')
        fh.write('%s <%02x/%02x>\n' % (x, io_values[0xa8], subpage))
        fh.close()

snd = sound(debug)

# bb == bios/basic
bb = rom('msxbiosbasic.rom', debug, 0x0000)
bb_sig = bb.get_signature()

scc_sig = None
#scc_rom_file = 'NEMESIS2.ROM'
#scc_rom_file = 'md1.rom'
#scc_obj = scc(scc_rom_file, snd, debug) if scc_rom_file else None
#scc_sig = scc_obj.get_signature() if scc_obj else None

disk_sig = None
#disk_rom_file = 'FSFD1.ROM'
#disk_image_file = 'nondos.dsk'
#disk_obj = disk(disk_rom_file, debug, disk_image_file) if disk_rom_file else None
#disk_sig = disk_obj.get_signature() if disk_obj else None

gen_sig = None
#gen_rom_file = 'athletic.rom'
#gen_rom_file = 'yamaha_msx1_diag.rom'
#gen_rom_file = '../../msx/trunk/docs/testram.rom'
#gen_obj = gen_rom(gen_rom_file, debug) if gen_rom_file else None
#gen_sig = gen_obj.get_signature() if gen_obj else None

subpage = 0x00

mm = memmap(256, debug)
mm_sig = mm.get_signature()

slots = [ ] # slots
slots.append(( bb_sig, None, None, mm_sig ))
slots.append(( bb_sig, disk_sig if disk_sig else gen_sig, scc_sig, mm_sig ))
slots.append(( None, None, scc_sig, mm_sig ))
slots.append(( None, None, None, mm_sig ))

pages = [ 0, 0, 0, 0 ]

def read_mem(a):
    global subpage

    if a == 0xffff:
        return subpage

    page = a >> 14

    slot = slots[page][pages[page]]
    if slot == None:
        return 0xee

    if len(slot) != 3:
        print(len(slot), a)

    return slot[2].read_mem(a)

def write_mem(a, v):
    global subpage

    if not (v >= 0 and v <= 255):
        print(v, file=sys.stderr)
    assert v >= 0 and v <= 255

    if a == 0xffff:
        subpage = v
        return

    page = a >> 14

    slot = slots[page][pages[page]]
    if slot == None:
        debug('Writing %02x to %04x which is not backed by anything' % (v, a))
        return
    
    slot[2].write_mem(a, v)

def read_page_layout(a):
    return (pages[3] << 6) | (pages[2] << 4) | (pages[1] << 2) | pages[0]

def write_page_layout(a, v):
    for i in range(0, 4):
        pages[i] = (v >> (i * 2)) & 3

def printer_out(a, v):
    # FIXME handle strobe
    print('%c' % v, END='')

def init_io():
    global dk
    global mm
    global snd

    if dk:
        print('set screen')
        for i in (0x98, 0x99, 0x9a, 0x9b):
            io_read[i] = dk.read_io
            io_write[i] = dk.write_io

        io_read[0xa9] = dk.read_io

        io_write[0xaa] = dk.write_io

    if snd:
        print('set sound')
        io_write[0xa0] = snd.write_io
        io_write[0xa1] = snd.write_io
        io_read[0xa2] = snd.read_io

    print('set mm')
    for i in range(0xfc, 0x100):
        io_read[i] = mm.read_io
        io_write[i] = mm.write_io

    print('set mm')
    io_read[0xa8] = read_page_layout
    io_write[0xa8] = write_page_layout

    print('set printer')
    io_write[0x91] = printer_out

def read_io(a):
    global io_read

    if io_read[a]:
        return io_read[a](a)

    return io_values[a]
 
def write_io(a, v):
    global io_write

    io_values[a] = v

    if io_write[a]:
        io_write[a](a, v)

stop_flag = False

def cpu_thread():
    #t = time.time()
    #while time.time() - t < 5:
    while not stop_flag:
        cpu.step()

dk = screen_kb(io_values)

cpu = z80(read_mem, write_mem, read_io, write_io, debug, dk)

init_io()

t = threading.Thread(target=cpu_thread)
t.start()

if abort_time:
    time.sleep(abort_time)
    stop_flag = True

try:
    t.join()

except KeyboardInterrupt:
    stop_flag = True
    t.join()

dk.stop()

#for i in range(0, 256):
#    if cpu.counts[i]:
#        print('instr %02x: %d' % (i, cpu.counts[i]), file=sys.stderr)
