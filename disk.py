import sys
from pagetype import PageType

class disk:
    T1_BUSY = 0x01
    T1_INDEX = 0x02
    T1_TRACK0 = 0x04
    T1_CRCERR = 0x08
    T1_SEEKERR = 0x10
    T1_HEADLOAD = 0x20
    T1_PROT = 0x40
    T1_NOTREADY = 0x80

    T2_BUSY = 0x01
    T2_DRQ = 0x02
    T2_NOTREADY = 0x80

    def __init__(self, disk_rom_file, debug):
        print('Loading disk rom %s...' % disk_rom_file, file=sys.stderr)

        fh = open(disk_rom_file, 'rb')
        self.disk_rom = [ int(b) for b in fh.read() ]
        fh.close()

        self.regs = [ 0 ] * 16

        self.buffer = [ 0 ] * 512
        self.bufp = 0
        self.need_flush = False

        self.tc = None
        self.flags = 0

        self.step_dir = 1

        self.debug = debug

    def get_signature(self):
        return (self.disk_rom, PageType.DISK, self)

    def write_mem(self, a, v):
        offset = a - 0x4000

        if offset >= 0x3ff0: # HW registers
            reg = offset - 0x3ff0

            self.debug('Write DISK register %02x: %02x' % (reg, v))

            if reg == 0x08:
                command= v >> 4
                T      = (v >> 4) & 1;
                h      = (v >> 3) & 1;
                V      = (v >> 2) & 1;
                r1     = (v >> 1) & 1;
                r0     = (v     ) & 1;
                m      = (v >> 4) & 1;
                S      = (v >> 3) & 1;
                E      = (v >> 2) & 1;
                C      = (v >> 1) & 1;
                A0     = (v     ) & 1;
                i      = (v & 15);

                if v == 0:  # restore
                    self.regs[0x09] = 0
                    self.tc = 1

                    self.flags = self.T1_INDEX | self.T1_TRACK0
                    if h:
                        self.flags |= self.T1_HEADLOAD

                elif v == 1:  # seek
                    self.regs[0x09] = self.regs[0x0b]
                    self.tc = 1

                    self.flags = self.T1_INDEX | self.T1_TRACK0
                    if h:
                        self.flags |= self.T1_HEADLOAD

                elif v == 2 or v == 3:  # step
                    self.regs[0x09] += self.step_dir

                    if self.regs[0x09] < 0:
                        self.regs[0x09] = 0
                    elif self.regs[0x09] > 79:
                        self.regs[0x09] = 79

                    self.tc = 1

                    self.flags = self.T1_INDEX
                    if self.regs[0x09] == 0:
                        self.flags |= self.T1_TRACK0

                elif v == 4 or v == 5:  # step-in
                    self.regs[0x09] += 1

                    if self.regs[0x09] > 79:
                        self.regs[0x09] = 79

                    self.step_dir = 1

                    self.tc = 1

                    self.flags = self.T1_INDEX

                    if self.regs[0x09] == 0:
                        self.flags |= self.T1_TRACK0;

                elif v == 6 or v == 7:  # step-out
                    self.regs[0x09] -= 1

                    if self.regs[0x09] < 0:
                        self.regs[0x09] = 0

                    self.step_dir = -1

                    self.tc = 1

                    self.flags = self.T1_INDEX
                    if self.regs[0x09] == 0:
                        self.flags |= self.T1_TRACK0;

                elif v == 8 or v == 9:  # read sector
                    self.bufp = 0
                    self.need_flush = False
                    # FIXME load to self.buffer

                    self.tc = 2

                    self.flags |= self.T2_BUSY | self.T2_DRQ

                elif v == 10 or v == 11:  # write sector
                    self.bufp = 0
                    self.need_flush = True

                    self.tc = 2

                    self.flags |= self.T2_BUSY | self.T2_DRQ

                elif v == 12:
                    self.tc = 3

                    self.flags |= self.T2_BUSY | self.T2_DRQ

                elif v == 13:
                    self.bufp = 0

                    self.tc = 4

                elif v == 14:
                    self.tc = 3

                    self.flags |= self.T2_BUSY | self.T2_DRQ

                elif v == 15:
                    self.tc = 3

                    self.flags |= self.T2_BUSY | self.T2_DRQ

            elif reg == 0x0b:  # data register
                if self.bufp < 512:
                    self.buffer[self.bufp] = v
                    self.bufp += 1

                    if self.bufp == 512 and self.need_flush:
                        # FIXME write to disk

                        self.flags &= ~(self.T2_DRQ | self.T2_BUSY)

                    else:
                        self.flags |= self.T2_DRQ

            elif reg == 0x0c:  # side
                if (v & 0x04) == 0x04:  # reset
                    self.regs[0x09] = 0

            else:
                self.regs[reg] = v

    def read_mem(self, a):
        offset = a - 0x4000

        if offset >= 0x3ff0: # HW registers
            reg = offset - 0x3ff0

            #self.debug('Read DISK register %02x' % reg)

            if reg == 0x08:
                if self.tc == 1 or self.tc == 4:
                    v = self.flags
                    self.flags &= self.T1_NOTREADY
                    self.flags &= self.T1_BUSY
                    return v

                elif self.tc == 2 or self.tc == 3:
                    return self.flags

            elif reg == 0x0b:
                if self.bufp < 512:
                    v = self.buffer[self.bufp]
                    self.bufp += 1
                    self.flags |= self.T2_DRQ
                    return v

                else:
                    self.flags &= ~(self.T2_DRQ | self.T2_BUSY | 32)

            elif reg == 0x0f:
                v = 0

                if self.flags & self.T2_DRQ:
                        v |= 128
                        self.flags &= ~self.T2_DRQ

                if self.flags & self.T2_BUSY:
                        v |= 64

                return v

            return self.regs[reg]

        return self.disk_rom[offset]
