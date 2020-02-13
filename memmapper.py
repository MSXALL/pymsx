# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import sys
from pagetype import PageType

class memmap:
    def __init__(self, n_pages, debug):
        assert n_pages > 0 and n_pages <= 256

        self.n_pages = n_pages
        self.debug = debug

        self.mapper = [ 0, 1, 2, 3 ]

        self.ram = [ [ 0 ] * 16384 ] * self.n_pages

    def get_signature(self):
        return (None, PageType.MEMMAP, self)

    def write_mem(self, a, v):
        page = self.mapper[a >> 14]

        if page < self.n_pages:
            self.ram[page][a & 0x3fff] = v

    def read_mem(self, a):
        page = self.mapper[a >> 14]

        if page < self.n_pages:
            return self.ram[page][a & 0x3fff]

        return 0xee

    def write_io(self, a, v):
        self.debug('memmap write %02x: %d' % (a, v), file=sys.stderr)
        self.mapper[a - 0xfc] = v

    def read_io(self, a):
        self.debug('memmap read %02x' % a, file=sys.stderr)
        return self.mapper[a - 0xfc]

