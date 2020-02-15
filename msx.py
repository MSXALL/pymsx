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
from optparse import OptionParser

abort_time = None # 60

debug_log = None

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

mm = memmap(256, debug)
mm_sig = mm.get_signature()

slot_0 = [ None, None, None, mm_sig ]
slot_1 = [ None, None, None, mm_sig ]
slot_2 = [ None, None, None, mm_sig ]
slot_3 = [ None, None, None, mm_sig ]

bb_file = None

parser = OptionParser()
parser.add_option('-b', '--biosbasic', dest='bb_file', help='select BIOS/BASIC ROM')
parser.add_option('-l', '--debug-log', dest='debug_log', help='logfile to write to (optional)')
parser.add_option('-R', '--rom', dest='rom', help='select a simple ROM to use, format: slot:rom-filename')
parser.add_option('-S', '--scc-rom', dest='scc_rom', help='select an SCC ROM to use, format: slot:rom-filename')
parser.add_option('-D', '--disk-rom', dest='disk_rom', help='select a disk ROM to use, format: slot:rom-filename:disk-image.dsk')
(options, args) = parser.parse_args()

debug_log = options.debug_log

if not options.bb_file:
    print('No BIOS/BASIC ROM selected (e.g. msxbiosbasic.rom)')
    sys.exit(1)

# bb == bios/basic
bb = rom(options.bb_file, debug, 0x0000)
bb_sig = bb.get_signature()
slot_0[0] = bb_sig
slot_1[0] = bb_sig

snd = sound(debug)

if options.scc_rom:
    parts = options.scc_rom.split(':')
    scc_obj = scc(parts[1], snd, debug)
    scc_sig = scc_obj.get_signature()
    scc_slot = int(parts[0])
    slot_1[scc_slot] = scc_sig
    slot_2[scc_slot] = scc_sig

if options.disk_rom:
    parts = options.disk_rom.split(':')
    disk_slot = int(parts[0])
    disk_obj = disk(parts[1], debug, parts[2])
    slot_1[disk_slot] = disk_obj.get_signature()

if options.rom:
    parts = options.rom.split(':')
    rom_slot = int(parts[0])
    rom_obj = gen_rom(parts[1], debug)
    rom_sig = rom_obj.get_signature()
    slot_1[rom_slot] = rom_sig
    if len(rom_sig[0]) >= 32768:
        slot_2[rom_slot] = rom_sig

subpage = 0x00

slots = ( slot_0, slot_1, slot_2, slot_3 )

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
