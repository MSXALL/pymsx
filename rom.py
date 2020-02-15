# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import sys
from pagetype import PageType

class rom:
    def __init__(self, rom_file, debug, base_address):
        print('Loading ROM %s...' % rom_file, file=sys.stderr)

        fh = open(rom_file, 'rb')
        self.rom = [ int(b) for b in fh.read() ]
        fh.close()

        self.base_address = base_address

        self.debug = debug

    def get_signature(self):
        return (self.rom, PageType.ROM, self)

    def write_mem(self, a, v):
        pass

    def read_mem(self, a):
        return self.rom[a - self.base_address]
