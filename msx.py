#! /usr/bin/python3

import sys
import threading
import time
from z80 import z80
from screen_kb import screen_kb

from enum import Enum
class PageType(Enum):
    ROM = 1
    RAM = 2
    SCC = 3

io = [ 0 ] * 256

fh = open('msxbiosbasic.rom', 'rb')
rom0 = [ int(b) for b in fh.read(16384) ]
rom1 = [ int(b) for b in fh.read(16384) ]
fh.close()

scc_rom_file = 'md1.rom'
scc = None
if scc_rom_file:
    print('Loading SCC rom %s...' % scc_rom_file, file=sys.stderr)

    fh = open(scc_rom_file, 'rb')
    scc_rom = [ int(b) for b in fh.read() ]
    fh.close()

    scc_pages = [ 0, 1, 2, 3 ]

    scc = (scc_rom, PageType.SCC, scc_pages)

game_rom_file = None # 'STCMSX1P.ROM' # '../../msx/trunk/docs/magical.rom'
game = None
if game_rom_file:
    print('Loading SCC rom %s...' % game_rom_file, file=sys.stderr)

    fh = open(game_rom_file, 'rb')
    game_rom = [ int(b) for b in fh.read() ]
    fh.close()

    game = (game_rom, PageType.ROM)

def write_scc(s, a, v):
    bank = (a >> 13) - 2
    offset = a & 0x1fff
    p = s[bank] * 0x2000 + offset

    if (offset & 0x1000) == 0x1000: # 0x5000, 0x7000 and so on
        if v < 255:
            debug('Set bank %d to %d' % (bank, v))
            s[bank] = v

    else:
        self.debug('SCC write to %04x not understood' % a)

def read_scc(s, a):
    bank = (a >> 13) - 2
    print('%04x, SCC bank %d, p: %d' % (a, bank, s[bank]), file=sys.stderr)
    offset = a & 0x1fff
    p = s[bank] * 0x2000 + offset

    return scc_rom[p]

subpage = 0x00

ram0 = [ 0 ] * 16384
ram1 = [ 0 ] * 16384
ram2 = [ 0 ] * 16384
ram3 = [ 0 ] * 16384

slots = [ ] # slots
slots.append(( (rom0, PageType.ROM), None, None, (ram0, PageType.RAM) ))
slots.append(( (rom1, PageType.ROM), scc, game, (ram1, PageType.RAM) ))
slots.append(( None, scc, None, (ram2, PageType.RAM) ))
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
        return read_scc(slots[page][pages[page]][2], a)

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
        write_scc(slots[page][pages[page]][2], a, v)
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

def debug(x):
    dk.debug('%s <%02x>' % (x, io[0xa8]))
    print('%s <%02x>' % (x, io[0xa8]), file=sys.stderr)

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
