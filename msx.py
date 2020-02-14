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
#from sound import sound
from memmapper import memmap

abort_time = None # 60

debug_log = 'debug.log' # None to disable

io = [ 0 ] * 256

subpage = 0x00

fh = open('msxbiosbasic.rom', 'rb')
rom0 = [ int(b) for b in fh.read(16384) ]
rom1 = [ int(b) for b in fh.read(16384) ]
fh.close()

def debug(x):
    global subpage
    dk.debug('%s <%02x/%02x>' % (x, io[0xa8], subpage))

    if debug_log:
        fh = open(debug_log, 'a+')
        fh.write('%s <%02x/%02x>\n' % (x, io[0xa8], subpage))
        fh.close()

snd = None  # sound(debug)

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
slots.append(( (rom0, PageType.ROM), None, None, mm_sig ))
slots.append(( (rom1, PageType.ROM), disk_sig if disk_sig else gen_sig, scc_sig, mm_sig ))
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

    slot_type = slot[1]

    if slot_type in (PageType.SCC, PageType.DISK, PageType.MEMMAP):
        obj = slot[2]
        return obj.read_mem(a)

    return slot[0][a & 0x3fff]

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
    
    slot_type = slot[1]

    if slot_type == PageType.ROM:
        debug('Writing %02x to %04x which is ROM' % (v, a))
        return
    
    if slot_type in (PageType.SCC, PageType.DISK, PageType.MEMMAP):
        obj = slot[2]
        obj.write_mem(a, v)
        return

    slot[0][a & 0x3fff] = v

def read_io(a):
    debug('Get I/O register %02x' % a)

    if (a >= 0x98 and a <= 0x9b) or a == 0xa9:
        return dk.read_io(a)

    if a == 0xa8:
        return (pages[3] << 6) | (pages[2] << 4) | (pages[1] << 2) | pages[0]

    if a == 0xa2:
        if snd:
            return snd.read_io(a)

    if a >= 0xfc:
        return mm.read_io(a)

    return io[a]
 
def write_io(a, v):
    assert v >= 0 and v <= 255

    debug('Set I/O register %02x to %02x' % (a, v))

    io[a] = v

    if a == 0x91:  # printer out
        # FIXME handle strobe
        print('%c' % v, END='')

    if (a >= 0x98 and a <= 0x9b) or a == 0xaa:
        dk.write_io(a, v)
        return

    if a == 0xa0 or a == 0xa1:
        if snd:
            snd.write_io(a, v)
            return

    if a >= 0xfc:
        mm.write_io(a, v)
        return

    if a == 0xa8:
        for i in range(0, 4):
            pages[i] = (v >> (i * 2)) & 3

stop_flag = False

def cpu_thread():
    #t = time.time()
    #while time.time() - t < 5:
    while not stop_flag:
        cpu.step()

dk = screen_kb(io)

cpu = z80(read_mem, write_mem, read_io, write_io, debug, dk)

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
