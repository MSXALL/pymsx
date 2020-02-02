import sys
from pagetype import PageType

class scc:
    def __init__(self, scc_rom_file, debug):
        print('Loading SCC rom %s...' % scc_rom_file, file=sys.stderr)

        fh = open(scc_rom_file, 'rb')
        self.scc_rom = [ int(b) for b in fh.read() ]
        fh.close()

        self.n_pages = (len(self.scc_rom) + 0x1fff) // 0x2000

        self.scc_pages = [ 0, 1, 2, 3 ]

        self.debug = debug

    def get_signature(self):
        return (self.scc_rom, PageType.SCC, self)

    def write_mem(self, a, v):
        bank = (a >> 13) - 2
        offset = a & 0x1fff
        p = self.scc_pages[bank] * 0x2000 + offset

        if (offset & 0x1000) == 0x1000: # 0x5000, 0x7000 and so on
            if v < 255:
                self.debug('Set bank %d to %d' % (bank, v))
                assert v < self.n_pages
                self.scc_pages[bank] = v

        else:
            self.debug('SCC write to %04x not understood' % a)

    def read_mem(self, a):
        bank = (a >> 13) - 2
        print('%04x, SCC bank %d, p: %d' % (a, bank, self.scc_pages[bank]), file=sys.stderr)
        offset = a & 0x1fff
        p = self.scc_pages[bank] * 0x2000 + offset

        return self.scc_rom[p]
