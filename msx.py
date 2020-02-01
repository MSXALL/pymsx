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

game_rom_file = None #'/home/folkert/Projects/msx/trunk/docs/testram.rom'
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
        s[bank] = v

def read_scc(s, a):
    bank = (a >> 13) - 2
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
slots.append(( None, None, None, (ram2, PageType.RAM) ))
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

def find_char_row(c):
    chars = [ None ] * 256
    chars[ord(')')] = ( 0, (1 << 0) ^ 0xff, True )
    chars[ord('0')] = ( 0, (1 << 0) ^ 0xff, False )
    chars[ord('!')] = ( 0, (1 << 1) ^ 0xff, True )
    chars[ord('1')] = ( 0, (1 << 1) ^ 0xff, False )
    chars[ord('@')] = ( 0, (1 << 2) ^ 0xff, True )
    chars[ord('2')] = ( 0, (1 << 2) ^ 0xff, False )
    chars[ord('#')] = ( 0, (1 << 3) ^ 0xff, True )
    chars[ord('3')] = ( 0, (1 << 3) ^ 0xff, False )
    chars[ord('$')] = ( 0, (1 << 4) ^ 0xff, True )
    chars[ord('4')] = ( 0, (1 << 4) ^ 0xff, False )
    chars[ord('%')] = ( 0, (1 << 5) ^ 0xff, True )
    chars[ord('5')] = ( 0, (1 << 5) ^ 0xff, False )
    chars[ord('^')] = ( 0, (1 << 6) ^ 0xff, True )
    chars[ord('6')] = ( 0, (1 << 6) ^ 0xff, False )
    chars[ord('&')] = ( 0, (1 << 7) ^ 0xff, True )
    chars[ord('7')] = ( 0, (1 << 7) ^ 0xff, False )
    chars[ord('*')] = ( 1, (1 << 0) ^ 0xff, True )
    chars[ord('8')] = ( 1, (1 << 0) ^ 0xff, False )
    chars[ord('(')] = ( 1, (1 << 1) ^ 0xff, True )
    chars[ord('9')] = ( 1, (1 << 1) ^ 0xff, False )
    chars[ord('_')] = ( 1, (1 << 2) ^ 0xff, True )
    chars[ord('-')] = ( 1, (1 << 2) ^ 0xff, False )
    chars[ord('+')] = ( 1, (1 << 3) ^ 0xff, True )
    chars[ord('=')] = ( 1, (1 << 3) ^ 0xff, False )
    chars[ord('|')] = ( 1, (1 << 4) ^ 0xff, True )
    chars[ord('\\')] = ( 1, (1 << 4) ^ 0xff, False )
    chars[ord('{')] = ( 1, (1 << 5) ^ 0xff, True )
    chars[ord('[')] = ( 1, (1 << 5) ^ 0xff, False )
    chars[ord('}')] = ( 1, (1 << 6) ^ 0xff, True )
    chars[ord(']')] = ( 1, (1 << 6) ^ 0xff, False )
    chars[ord(':')] = ( 1, (1 << 7) ^ 0xff, True )
    chars[ord(';')] = ( 1, (1 << 7) ^ 0xff, False )
    chars[ord('"')] = ( 2, (1 << 0) ^ 0xff, True )
    chars[ord("'")] = ( 2, (1 << 0) ^ 0xff, False )
    chars[ord('~')] = ( 2, (1 << 1) ^ 0xff, True )
    chars[ord('`')] = ( 2, (1 << 1) ^ 0xff, False )
    chars[ord('<')] = ( 2, (1 << 2) ^ 0xff, True )
    chars[ord(',')] = ( 2, (1 << 2) ^ 0xff, False )
    chars[ord('>')] = ( 2, (1 << 3) ^ 0xff, True )
    chars[ord('.')] = ( 2, (1 << 3) ^ 0xff, False )
    chars[ord('?')] = ( 2, (1 << 4) ^ 0xff, True )
    chars[ord('/')] = ( 2, (1 << 4) ^ 0xff, False )
    chars[ord('A')] = ( 2, (1 << 6) ^ 0xff, True )
    chars[ord('a')] = ( 2, (1 << 6) ^ 0xff, False )
    chars[ord('B')] = ( 2, (1 << 7) ^ 0xff, True )
    chars[ord('b')] = ( 2, (1 << 7) ^ 0xff, False )
    chars[ord('C')] = ( 3, (1 << 0) ^ 0xff, True )
    chars[ord('c')] = ( 3, (1 << 0) ^ 0xff, False )
    chars[ord('D')] = ( 3, (1 << 1) ^ 0xff, True )
    chars[ord('d')] = ( 3, (1 << 1) ^ 0xff, False )
    chars[ord('E')] = ( 3, (1 << 2) ^ 0xff, True )
    chars[ord('e')] = ( 3, (1 << 2) ^ 0xff, False )
    chars[ord('F')] = ( 3, (1 << 3) ^ 0xff, True )
    chars[ord('f')] = ( 3, (1 << 3) ^ 0xff, False )
    chars[ord('G')] = ( 3, (1 << 4) ^ 0xff, True )
    chars[ord('g')] = ( 3, (1 << 4) ^ 0xff, False )
    chars[ord('H')] = ( 3, (1 << 5) ^ 0xff, True )
    chars[ord('h')] = ( 3, (1 << 5) ^ 0xff, False )
    chars[ord('I')] = ( 3, (1 << 6) ^ 0xff, True )
    chars[ord('i')] = ( 3, (1 << 6) ^ 0xff, False )
    chars[ord('J')] = ( 3, (1 << 7) ^ 0xff, True )
    chars[ord('j')] = ( 3, (1 << 7) ^ 0xff, False )
    chars[ord('K')] = ( 4, (1 << 0) ^ 0xff, True )
    chars[ord('k')] = ( 4, (1 << 0) ^ 0xff, False )
    chars[ord('L')] = ( 4, (1 << 1) ^ 0xff, True )
    chars[ord('l')] = ( 4, (1 << 1) ^ 0xff, False )
    chars[ord('M')] = ( 4, (1 << 2) ^ 0xff, True )
    chars[ord('m')] = ( 4, (1 << 2) ^ 0xff, False )
    chars[ord('N')] = ( 4, (1 << 3) ^ 0xff, True )
    chars[ord('n')] = ( 4, (1 << 3) ^ 0xff, False )
    chars[ord('O')] = ( 4, (1 << 4) ^ 0xff, True )
    chars[ord('o')] = ( 4, (1 << 4) ^ 0xff, False )
    chars[ord('P')] = ( 4, (1 << 5) ^ 0xff, True )
    chars[ord('p')] = ( 4, (1 << 5) ^ 0xff, False )
    chars[ord('Q')] = ( 4, (1 << 6) ^ 0xff, True )
    chars[ord('q')] = ( 4, (1 << 6) ^ 0xff, False )
    chars[ord('R')] = ( 4, (1 << 7) ^ 0xff, True )
    chars[ord('r')] = ( 4, (1 << 7) ^ 0xff, False )
    chars[ord('S')] = ( 5, (1 << 0) ^ 0xff, True )
    chars[ord('s')] = ( 5, (1 << 0) ^ 0xff, False )
    chars[ord('T')] = ( 5, (1 << 1) ^ 0xff, True )
    chars[ord('t')] = ( 5, (1 << 1) ^ 0xff, False )
    chars[ord('U')] = ( 5, (1 << 2) ^ 0xff, True )
    chars[ord('u')] = ( 5, (1 << 2) ^ 0xff, False )
    chars[ord('V')] = ( 5, (1 << 3) ^ 0xff, True )
    chars[ord('v')] = ( 5, (1 << 3) ^ 0xff, False )
    chars[ord('W')] = ( 5, (1 << 4) ^ 0xff, True )
    chars[ord('w')] = ( 5, (1 << 4) ^ 0xff, False )
    chars[ord('X')] = ( 5, (1 << 5) ^ 0xff, True )
    chars[ord('x')] = ( 5, (1 << 5) ^ 0xff, False )
    chars[ord('Y')] = ( 5, (1 << 6) ^ 0xff, True )
    chars[ord('y')] = ( 5, (1 << 6) ^ 0xff, False )
    chars[ord('Z')] = ( 5, (1 << 7) ^ 0xff, True )
    chars[ord('z')] = ( 5, (1 << 7) ^ 0xff, False )
    chars[8       ] = ( 7, (1 << 5) ^ 0xff, False )
    chars[127     ] = ( 7, (1 << 5) ^ 0xff, False )
    chars[10      ] = ( 7, (1 << 7) ^ 0xff, False )
    chars[13      ] = ( 7, (1 << 7) ^ 0xff, False )
    chars[ord(' ')] = ( 8, (1 << 0) ^ 0xff, False )

    return chars[c]

kb_last_c = None
kb_char_scanned = kb_shift_scanned = False
kb_row_nr = None
kb_row = None
kb_shift = False
def get_keyboard():
    global kb_last_c
    global kb_char_scanned
    global kb_shift_scanned
    global kb_row_nr
    global kb_row
    global kb_shift

    rc = 255

    if kb_last_c == None:
        kb_last_c = dk.getch(False)
        print('lastc', kb_last_c, file=sys.stderr)

        if kb_last_c == -1:
            kb_last_c = None

        else:
            lrc = find_char_row(kb_last_c)

            if lrc:
                kb_row_nr, kb_row, kb_shift = lrc
                print('keyb', lrc, file=sys.stderr)

            else:
                kb_last_c = None

            kb_shift_scanned = False
            kb_char_scanned = False

    if (io[0xaa] & 15) == kb_row_nr:
        kb_char_scanned = True
        rc = kb_row

    if (io[0xaa] & 15) == 6:
        kb_shift_scanned = True

        if kb_shift:
            rc &= ~1

    if kb_shift_scanned and kb_char_scanned:
        kb_last_c = None
        kb_row_nr = None
        kb_row = None
        kb_shift = False

    if rc != 255:
        print('rc', rc, file=sys.stderr)

    return rc

def read_io(a):
    debug('Get I/O register %02x' % a)

    if a >= 0x98 and a <= 0x9b:
        return dk.read_io(a)

    if a == 0xa8:
        return (pages[3] << 6) | (pages[2] << 4) | (pages[1] << 2) | pages[0]

    if a == 0xa9:
        return get_keyboard()

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

dk = screen_kb(cpu)
dk.start()

t = threading.Thread(target=cpu_thread)
t.start()

try:
    t.join()

except KeyboardInterrupt:
    stop_flag = True
    t.join()

dk.stop()
