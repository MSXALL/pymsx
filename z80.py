# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import time

class z80:
    def __init__(self, read_mem, write_mem, read_io, write_io, debug):
        self.read_mem = read_mem
        self.write_mem = write_mem
        self.read_io = read_io
        self.write_io = write_io
        self.debug_out = debug

        self.init_main()
        self.init_xy()
        self.init_xy_bit()
        self.init_bits()
        self.init_parity()
        self.init_ext()

        self.reset()

        self.counts = [ 0 ] * 256

    def debug(self, x):
        self.debug_out(x)
        self.debug_out(self.reg_str())
        self.debug_out('')

    def reset(self):
        self.a = self.b = self.c = self.d = self.e = self.f = self.h = self.l = 0xff
        self.a_ = self.b_ = self.c_ = self.d_ = self.e_ = self.f_ = self.h_ = self.l_ = 0xff
        self.ix = self.iy = 0xffff
        self.interrupts = True
        self.pc = 0
        self.sp = 0xffff
        self.im = 0
        self.i = self.r = 0

        self.cycles = 0
        self.int = False

    def ui(self, which):
        raise Exception('unknown instruction %x' % which)

    def interrupt(self):
        if self.interrupts:
            self.int = True

    def in_(self, a):
        return self.read_io(a)

    def out(self, a, v):
        self.write_io(a, v)

    def incp16(self, p):
        p += 1
        return p & 0xffff

    def decp16(self, p):
        p -= 1
        return p & 0xffff

    def read_pc_inc(self):
        v = self.read_mem(self.pc)

        self.pc = self.incp16(self.pc)

        return v

    def read_pc_inc_16(self):
        low = self.read_pc_inc()
        high = self.read_pc_inc()
        return self.m16(high, low)

    def _jr_wrapper(self, instr):
        if instr == 0x18:
            self._jr(True, '')

        elif instr == 0xc3:
            self._jp(True, None)

        elif instr == 0x20:
            self._jr(not self.get_flag_z(), "nz")

        elif instr == 0x28:
            self._jr(self.get_flag_z(), 'z')

        elif instr == 0x30:
            self._jr(not self.get_flag_c(), "nc")

        elif instr == 0x38:
            self._jr(self.get_flag_c(), 'c')

        else:
            assert False

    def _ret_wrap(self, instr):
        if instr == 0xc0:
            self._ret(not self.get_flag_z(), 'NZ')

        elif instr == 0xc8:
            self._ret(self.get_flag_z(), 'Z')

        elif instr == 0xd0:
            self._ret(not self.get_flag_c(), 'NC')

        elif instr == 0xd8:
            self._ret(self.get_flag_c(), 'C')

        elif instr == 0xe0:
            self._ret(not self.get_flag_pv(), 'PO')

        elif instr == 0xe8:
            self._ret(not self.get_flag_s(), 'P')

        elif instr == 0xf0:
            self._ret(not self.get_flag_s(), 'P')

        elif instr == 0xf8:
            self._ret(self.get_flag_s(), 'M')

        else:
            assert False

    def _jp_wrap(self, instr):
        if instr == 0xc2:
            self._jp(not self.get_flag_z(), 'NZ')

        elif instr == 0xc3:
            self._jp(True, '')

        elif instr == 0xca:  # JP Z,**
            self._jp(self.get_flag_z(), 'Z')

        elif instr == 0xd2:
            self._jp(not self.get_flag_c(), 'NC')

        elif instr == 0xda:  # JP c,**
            self._jp(self.get_flag_c(), 'C')

        elif instr == 0xe2:
            self._jp(not self.get_flag_pv(), 'PO')

        elif instr == 0xea:  # JP pe,**
            self._jp(self.get_flag_pv(), 'PE')

        elif instr == 0xf2:
            self._jp(not self.get_flag_s(), 'P')

        elif instr == 0xfa:  # JP M,**
            self._jp(self.get_flag_s(), 'M')

        else:
            self.ui(instr)

    def _call_wrap(self, instr):
        if instr == 0xc4:
            self._call_flag(not self.get_flag_z(), 'NZ')

        elif instr == 0xcc:  # CALL Z,**
            self._call_flag(self.get_flag_z(), 'Z')

        elif instr == 0xd4:
            self._call_flag(not self.get_flag_c(), 'NC')

        elif instr == 0xdc:  # CALL C,**
            self._call_flag(self.get_flag_c(), 'C')

        elif instr == 0xe4:
            self._call_flag(not self.get_flag_pv(), 'PO')

        elif instr == 0xec:  # CALL PE,**
            self._call_flag(self.get_flag_pv(), 'PE')

        elif instr == 0xf4:
            self._call_flag(self.get_flag_pv(), 'P')

        elif instr == 0xfc:  # CALL M,**
            self._call_flag(self.get_flag_s(), 'M')

        else:
            self.ui(instr)

    def _nop(self, instr):
        pass

    def init_main(self):
        self.main_jumps = [ None ] * 256

        self.main_jumps[0x00] = self._nop
        self.main_jumps[0x01] = self._ld_pair

        self.main_jumps[0x10] = self._djnz
        self.main_jumps[0x11] = self._ld_pair

        self.main_jumps[0x20] = self._jr_wrapper
        self.main_jumps[0x21] = self._ld_pair

        self.main_jumps[0x30] = self._jr_wrapper
        self.main_jumps[0x31] = self._ld_pair

        self.main_jumps[0x02] = self._ld_pair_from_a
        self.main_jumps[0x12] = self._ld_pair_from_a

        self.main_jumps[0x22] = self._ld_imem_from
        self.main_jumps[0x32] = self._ld_imem_from

        self.main_jumps[0x03] = self._inc_pair
        self.main_jumps[0x13] = self._inc_pair
        self.main_jumps[0x23] = self._inc_pair
        self.main_jumps[0x33] = self._inc_pair

        self.main_jumps[0x04] = self._inc_high
        self.main_jumps[0x14] = self._inc_high
        self.main_jumps[0x24] = self._inc_high
        self.main_jumps[0x34] = self._inc_high

        self.main_jumps[0x05] = self._dec_high
        self.main_jumps[0x15] = self._dec_high
        self.main_jumps[0x25] = self._dec_high
        self.main_jumps[0x35] = self._dec_high

        self.main_jumps[0x06] = self._ld_val_high
        self.main_jumps[0x16] = self._ld_val_high
        self.main_jumps[0x26] = self._ld_val_high
        self.main_jumps[0x36] = self._ld_val_high

        self.main_jumps[0x07] = self._rlca
        self.main_jumps[0x17] = self._rla
        self.main_jumps[0x27] = self._daa
        self.main_jumps[0x37] = self._scf

        self.main_jumps[0x08] = self._ex_af
        self.main_jumps[0x18] = self._jr_wrapper
        self.main_jumps[0x28] = self._jr_wrapper
        self.main_jumps[0x38] = self._jr_wrapper

        self.main_jumps[0x09] = self._add_pair
        self.main_jumps[0x19] = self._add_pair
        self.main_jumps[0x29] = self._add_pair
        self.main_jumps[0x39] = self._add_pair

        self.main_jumps[0x0a] = self._ld_a_imem
        self.main_jumps[0x1a] = self._ld_a_imem

        self.main_jumps[0x2a] = self._ld_imem
        self.main_jumps[0x3a] = self._ld_imem

        self.main_jumps[0x0b] = self._dec_pair
        self.main_jumps[0x1b] = self._dec_pair
        self.main_jumps[0x2b] = self._dec_pair
        self.main_jumps[0x3b] = self._dec_pair

        self.main_jumps[0x0c] = self._inc_low
        self.main_jumps[0x1c] = self._inc_low
        self.main_jumps[0x2c] = self._inc_low
        self.main_jumps[0x3c] = self._inc_low

        self.main_jumps[0x0d] = self._dec_low
        self.main_jumps[0x1d] = self._dec_low
        self.main_jumps[0x2d] = self._dec_low
        self.main_jumps[0x3d] = self._dec_low

        self.main_jumps[0x0e] = self._ld_val_low
        self.main_jumps[0x1e] = self._ld_val_low
        self.main_jumps[0x2e] = self._ld_val_low
        self.main_jumps[0x3e] = self._ld_val_low

        self.main_jumps[0x0f] = self._rrca
        self.main_jumps[0x1f] = self._rr
        self.main_jumps[0x2f] = self._cpl
        self.main_jumps[0x3f] = self._ccf

        for i in range(0x40, 0x80):
            self.main_jumps[i] = self._ld

        for i in range(0x80, 0x90):
            self.main_jumps[i] = self._add

        for i in range(0x90, 0xa0):
            self.main_jumps[i] = self._sub

        for i in range(0xa0, 0xa8):
            self.main_jumps[i] = self._and

        for i in range(0xa8, 0xb0):
            self.main_jumps[i] = self._xor

        for i in range(0xb0, 0xb8):
            self.main_jumps[i] = self._or

        for i in range(0xb8, 0xc0):
            self.main_jumps[i] = self._cp

        self.main_jumps[0xc0] = self._ret_wrap
        self.main_jumps[0xd0] = self._ret_wrap
        self.main_jumps[0xe0] = self._ret_wrap
        self.main_jumps[0xf0]= self._ret_wrap

        self.main_jumps[0xc1] = self._pop
        self.main_jumps[0xd1] = self._pop
        self.main_jumps[0xe1] = self._pop
        self.main_jumps[0xf1] = self._pop

        self.main_jumps[0xc2] = self._jp_wrap
        self.main_jumps[0xd2] = self._jp_wrap
        self.main_jumps[0xe2] = self._jp_wrap
        self.main_jumps[0xf2] = self._jp_wrap

        self.main_jumps[0xc3] = self._jp_wrap
        self.main_jumps[0xd3] = self._out
        self.main_jumps[0xe3] = self._ex_sp_hl
        self.main_jumps[0xf3] = self._di

        self.main_jumps[0xc4] = self._call_wrap
        self.main_jumps[0xd4] = self._call_wrap
        self.main_jumps[0xe4] = self._call_wrap
        self.main_jumps[0xf4] = self._call_wrap

        self.main_jumps[0xc5] = self._push
        self.main_jumps[0xd5] = self._push
        self.main_jumps[0xe5] = self._push
        self.main_jumps[0xf5] = self._push

        self.main_jumps[0xc6] = self._add_a_val
        self.main_jumps[0xd6] = self._sub_val
        self.main_jumps[0xe6] = self._and_val
        self.main_jumps[0xf6] = self._or_val

        self.main_jumps[0xc7] = self._rst
        self.main_jumps[0xd7] = self._rst
        self.main_jumps[0xe7] = self._rst
        self.main_jumps[0xf7] = self._rst

        self.main_jumps[0xc8] = self._ret_wrap
        self.main_jumps[0xd8] = self._ret_wrap
        self.main_jumps[0xe8] = self._ret_wrap
        self.main_jumps[0xf8] = self._ret_wrap

        self.main_jumps[0xc9] = self._ret_always
        self.main_jumps[0xd9] = self._exx
        self.main_jumps[0xe9] = self._jp_hl
        self.main_jumps[0xf9] = self._ld_sp_hl

        self.main_jumps[0xca] = self._jp_wrap
        self.main_jumps[0xda] = self._jp_wrap
        self.main_jumps[0xea] = self._jp_wrap
        self.main_jumps[0xfa] = self._jp_wrap

        self.main_jumps[0xcb] = self.bits
        self.main_jumps[0xdb] = self._in
        self.main_jumps[0xeb] = self._ex_de_hl
        self.main_jumps[0xfb] = self._ei

        self.main_jumps[0xcc] = self._call_wrap
        self.main_jumps[0xdc] = self._call_wrap
        self.main_jumps[0xec] = self._call_wrap
        self.main_jumps[0xfc] = self._call_wrap

        self.main_jumps[0xcd] = self._call
        self.main_jumps[0xdd] = self._ix
        self.main_jumps[0xed] = self._ed
        self.main_jumps[0xfd] = self._iy

        self.main_jumps[0xce] = self._add_a_val
        self.main_jumps[0xde] = self._sub_val
        self.main_jumps[0xee] = self._xor_mem
        self.main_jumps[0xfe] = self._cp_mem

        self.main_jumps[0xcf] = self._rst
        self.main_jumps[0xdf] = self._rst
        self.main_jumps[0xef] = self._rst
        self.main_jumps[0xff] = self._rst

    def step(self):
        if self.int:
            self.int = False
            self.debug('Interrupt %f' % time.time())
            self.push(self.pc)
            self.pc = 0x38

        instr = self.read_pc_inc()

        self.counts[instr] += 1

        self.cycles += 1 # FIXME

        try:
            self.main_jumps[instr](instr)

        except TypeError as te:
            self.debug('TypeError main(%02x): %s' % (instr, te))
            assert False

    def m16(self, high, low):
        assert low >= 0 and low <= 255
        assert high >= 0 and high <= 255

        return (high << 8) | low

    def u16(self, v):
        assert v >= 0 and v <= 65535

        return (v >> 8, v & 0xff)

    def compl8(self, v):
        if v >= 128:
            return -(256 - v)

        return v

    def compl16(self, v):
        assert v >= 0 and v <= 65535

        if v >= 32768:
            return -(65536 - v)

        return v

    def get_src(self, which):
        if which == 0:
            return (self.b, 'B')
        if which == 1:
            return (self.c, 'C')
        if which == 2:
            return (self.d, 'D')
        if which == 3:
            return (self.e, 'E')
        if which == 4:
            return (self.h, 'H')
        if which == 5:
            return (self.l, 'L')
        if which == 6:
            a = self.m16(self.h, self.l)
            v = self.read_mem(a)
            return (v, '(HL)')
        if which == 7:
            return (self.a, 'A')

        assert False

    def set_dst(self, which, value):
        assert value >= 0 and value <= 255

        if which == 0:
            self.b = value
        elif which == 1:
            self.c = value
        elif which == 2:
            self.d = value
        elif which == 3:
            self.e = value
        elif which == 4:
            self.h = value
        elif which == 5:
            self.l = value
        elif which == 6:
            self.write_mem(self.m16(self.h, self.l), value)
        elif which == 7:
            self.a = value
        else:
            assert False

    def get_pair(self, which):
        if which == 0:
            return (self.m16(self.b, self.c), 'BC')
        elif which == 1:
            return (self.m16(self.d, self.e), 'DE')
        elif which == 2:
            return (self.m16(self.h, self.l), 'HL')
        elif which == 3:
            return (self.sp, 'SP')

        assert False

    def set_pair(self, which, v):
        assert v >= 0 and v <= 65535

        if which == 0:
            (self.b, self.c) = self.u16(v)
            return 'BC'
        elif which == 1:
            (self.d, self.e) = self.u16(v)
            return 'DE'
        elif which == 2:
            (self.h, self.l) = self.u16(v)
            return 'HL'
        elif which == 3:
            self.sp = v
            return 'SP'

        assert False

    def init_parity(self):
        self.parity_lookup = [ 0 ] * 256

        for v in range(0, 256):
            count = 0

            for i in range(0, 8):
                count += (v & (1 << i)) != 0

            self.parity_lookup[v] = (count & 1) == 0

    def parity(self, v):
        return self.parity_lookup[v]

    def read_mem_16(self, a):
        low = self.read_mem(a)
        high = self.read_mem((a + 1) & 0xffff)

        return self.m16(high, low)

    def write_mem_16(self, a, v):
        self.write_mem(a, v & 0xff)
        self.write_mem((a + 1) & 0xffff, v >> 8)

    def pop(self):
        low = self.read_mem(self.sp)
        self.sp += 1
        self.sp &= 0xffff

        high = self.read_mem(self.sp)
        self.sp += 1
        self.sp &= 0xffff

        return self.m16(high, low)

    def push(self, v):
        self.sp -= 1
        self.sp &= 0xffff
        self.write_mem(self.sp, v >> 8)

        self.sp -= 1
        self.sp &= 0xffff
        self.write_mem(self.sp, v & 0xff)

    def set_flag_c(self, v):
        assert v == False or v == True
        self.f &= ~(1 << 0)
        self.f |= (v << 0)

    def get_flag_c(self):
        return (self.f & (1 << 0)) != 0

    def set_flag_n(self, v):
        assert v == False or v == True
        self.f &= ~(1 << 1)
        self.f |= v << 1

    def get_flag_n(self):
        return (self.f & (1 << 1)) != 0

    def set_flag_pv(self, v):
        assert v == False or v == True
        self.f &= ~(1 << 2)
        self.f |= v << 2

    def set_flag_parity(self):
        self.set_flag_pv(self.parity(self.a))

    def get_flag_pv(self):
        return (self.f & (1 << 2)) != 0

    def set_flag_h(self, v):
        assert v == False or v == True
        self.f &= ~(1 << 4)
        self.f |= v << 4

    def get_flag_h(self):
        return (self.f & (1 << 4)) != 0

    def set_flag_z(self, v):
        assert v == False or v == True
        self.f &= ~(1 << 6)
        self.f |= v << 6

    def get_flag_z(self):
        return (self.f & (1 << 6)) != 0

    def set_flag_s(self, v):
        assert v == False or v == True
        self.f &= ~(1 << 7)
        self.f |= v << 7

    def get_flag_s(self):
        return (self.f & (1 << 7)) != 0

    def ret_flag(self, flag):
        if flag:
            self.pc = self.pop()

    def reg_str(self):
        out = '{ %02x ' % (self.f & 0xd7)

        out += 's' if self.get_flag_s() else ''
        out += 'z' if self.get_flag_z() else ''
        out += 'h' if self.get_flag_h() else ''
        out += 'v' if self.get_flag_pv() else ''
        out += 'n' if self.get_flag_n() else ''
        out += 'c' if self.get_flag_c() else ''

        out += ' AF: %02x%02x, BC: %02x%02x, DE: %02x%02x, HL: %02x%02x, PC: %04x, SP: %04x, IX: %04x, IY: %04x / %d }' % (self.a, self.f, self.b, self.c, self.d, self.e, self.h, self.l, self.pc, self.sp, self.ix, self.iy, self.cycles)

        return out

    def bits(self, dummy):
        try:
            instr = self.read_pc_inc()
            self.debug('bits: %02x' % instr)
            self.bits_jumps[instr](instr)

        except TypeError as te:
            self.debug('TypeError bits(%02x): %s' % (instr, te))
            assert False

    def init_bits(self):
        self.bits_jumps = [ None ] * 256

        for i in range(0x00, 0x08):
                self.bits_jumps[i] = self._rlc

        for i in range(0x08, 0x10):
                self.bits_jumps[i] = self._rrc

        for i in range(0x10, 0x18):
                self.bits_jumps[i] = self._rl

        for i in range(0x18, 0x20):
                self.bits_jumps[i] = self._rr

        for i in range(0x20, 0x28):
                self.bits_jumps[i] = self._sla

        for i in range(0x28, 0x30):
                self.bits_jumps[i] = self._sra

        for i in range(0x38, 0x40):
                self.bits_jumps[i] = self._srl

        for i in range(0x40, 0x80):
                self.bits_jumps[i] = self._bit

        for i in range(0x80, 0xc0):
                self.bits_jumps[i] = self._res

        for i in range(0xc0, 0x100):
                self.bits_jumps[i] = self._set

    def set_add_flags(self, before, value, after):
        self.set_flag_c((after & 0x100) != 0)

        self.set_flag_z(after == 0)

        before = self.compl8(before)
        value = self.compl8(value)
        after = self.compl8(after & 0xff)
        self.set_flag_pv((before >= 0 and value >= 0 and after < 0) or (before < 0 and value < 0 and after >= 0))

        self.set_flag_s((after & 128) == 128)

        self.set_flag_n(False)

        self.set_flag_h((((before & 0x0f) + (value & 0x0f)) & 0x10) != 0)

    def _add(self, instr):
        c = instr & 8
        src = instr & 7

        (val, name) = self.get_src(src)
        old_val = val

        to_add = val
        if c:
            to_add += self.get_flag_c()

        result = self.a + to_add

        self.set_add_flags(val, to_add, result)

        self.a = result & 0xff

        self.debug('%s %s' % ('ADC' if c else 'ADD', name))

    def or_flags(self):
        self.set_flag_c(False)
        self.set_flag_z(self.a == 0)
        self.set_flag_parity()
        self.set_flag_s(self.a >= 128)
        self.set_flag_n(False)
        self.set_flag_h(False)

    def _or(self, instr):
        src = instr & 7
        (val, name) = self.get_src(src)
        self.a |= val

        self.or_flags()

        self.debug('OR %s' % name)

    def _or_val(self, instr):
        v = self.read_pc_inc()
        self.a |= v

        self.or_flags()

        self.debug('OR 0x%02x' % v)

    def and_flags(self):
        self.set_flag_c(False)
        self.set_flag_z(self.a == 0)
        self.set_flag_parity()
        self.set_flag_s(self.a >= 128)
        self.set_flag_n(False)
        self.set_flag_h(True)

    def _and(self, instr):
        src = instr & 7
        (val, name) = self.get_src(src)
        self.a &= val

        self.and_flags()

        self.debug('AND %s' % name)

    def _and_val(self, instr):
        v = self.read_pc_inc()
        self.a &= v

        self.and_flags()

        self.debug('AND 0x%02x' % v)

    def xor_flags(self):
        self.set_flag_c(False)
        self.set_flag_z(self.a == 0)
        self.set_flag_parity()
        self.set_flag_s(self.a >= 128)
        self.set_flag_n(False)
        self.set_flag_h(False)

    def _xor(self, instr):
        src = instr & 7
        (val, name) = self.get_src(src)

        self.a ^= val

        self.xor_flags()

        self.debug('XOR %s' % name)

    def _xor_mem(self, instr):
        val = self.read_pc_inc()

        self.a ^= val

        self.xor_flags()

        self.debug('XOR %02x' % val)

    def _out(self, instr):
        a = self.read_pc_inc()
        self.out(a, self.a)
        self.debug('OUT (0x%02x), A [%02x]' % (a, self.a))

    def _sla(self, instr):
        src = instr & 7
        (val, name) = self.get_src(src)

        val <<= 1

        self.f = 0
        self.set_flag_c(val > 255)
        self.set_flag_z(val == 0)
        self.set_flag_pv(self.parity(val & 0xff))
        self.set_flag_s((val & 128) == 128)
        self.set_flag_n(False)
        self.set_flag_h(False)

        val &= 255;

        dst = src
        self.set_dst(dst, val)

        self.debug('SLA %s' % name)

    def _sra(self, instr):
        src = instr & 7
        (val, name) = self.get_src(src)

        old_7 = val & 128
        self.set_flag_c((val & 1) == 1)
        val >>= 1
        val |= old_7

        self.f = 0
        self.set_flag_z(val == 0)
        self.set_flag_pv(self.parity(val & 0xff))
        self.set_flag_s((val & 128) == 128)
        self.set_flag_n(False)
        self.set_flag_h(False)

        val &= 255;

        dst = src
        self.set_dst(dst, val)

        self.debug('SRA %s' % name)

    def _ld_val_low(self, instr):
        which = instr >> 4
        val = self.read_pc_inc()

        if which == 0:
            self.c = val
            name = 'c'
        elif which == 1:
            self.e = val
            name = 'e'
        elif which == 2:
            self.l = val
            name = 'l'
        elif which == 3:
            self.a = val
            name = 'a'
        else:
            assert False

        self.debug('LD %s, 0x%02x' % (name, val))

    def _ld_val_high(self, instr):
        which = instr >> 4
        val = self.read_pc_inc()
        assert val >= 0 and val <= 255

        if which == 0:
            self.b = val
            name = 'B'
        elif which == 1:
            self.d = val
            name = 'D'
        elif which == 2:
            self.h = val
            name = 'H'
        elif which == 3:
            self.write_mem(self.m16(self.h, self.l), val)
            name = '(HL)'
        else:
            assert False

        self.debug('LD %s, 0x%02x' % (name, val))

    def _ld(self, instr):
        (val, src_name) = self.get_src(instr & 7)

        tgt = instr & 0xf8
        if tgt == 0x40:
            self.b = val
            tgt_name = 'B'
        elif tgt == 0x48:
            self.c = val
            tgt_name = 'C'
        elif tgt == 0x50:
            self.d = val
            tgt_name = 'D'
        elif tgt == 0x58:
            self.e = val
            tgt_name = 'E'
        elif tgt == 0x60:
            self.h = val
            tgt_name = 'H'
        elif tgt == 0x68:
            self.l = val
            tgt_name = 'L'
        elif tgt == 0x70:
            self.write_mem(self.m16(self.h, self.l), val)
            tgt_name = '(HL)'
        elif tgt == 0x78:
            self.a = val
            tgt_name = 'A'
        else:
            assert False

        self.debug('LD %s, %s [%02x]' % (tgt_name, src_name, val))

    def _ld_pair(self, instr):
        which = instr >> 4
        val = self.read_pc_inc_16()
        name = self.set_pair(which, val)

        self.debug('LD %s, 0x%04x' % (name, val))

    def _jp(self, flag, flag_name):
        a = self.read_pc_inc_16()

        if flag:
            self.pc = a

        if flag_name:
            self.debug('JP %s,0x%04x' % (flag_name, a))

        else:
            self.debug('JP 0x%04x' % a)

    def _call(self, instr):
        a = self.read_pc_inc_16()
        self.push(self.pc)
        self.pc = a

        self.debug('CALL 0x%04x' % a)

    def _push(self, instr):
        which = (instr >> 4) - 0x0c

        if which == 3:
            v = self.m16(self.a, self.f)
            name = 'AF'

        else:
            (v, name) = self.get_pair(which)

        self.push(v)

        self.debug('PUSH %s' % name)

    def _pop(self, instr):
        which = (instr >> 4) - 0x0c
        v = self.pop()

        if which == 3:
            name = 'AF'
            (self.a, self.f) = self.u16(v)

        else:
            name = self.set_pair(which, v)

        self.debug('POP %s' % name)

    def _jr(self, flag, flag_name):
        offset = self.compl8(self.read_pc_inc())

        if flag:
            self.pc += offset
            self.debug('JR %s,0x%04x' % (flag_name, self.pc))

        else:
            self.debug('JR %s,0x%04x NOT TAKEN' % (flag_name, self.pc))

    def _djnz(self, instr):
        offset = self.compl8(self.read_pc_inc())

        self.b -= 1
        self.b &= 0xff

        if self.b > 0:
            self.pc += offset
            self.debug('DJNZ 0x%04x' % self.pc)

        else:
            self.debug('DJNZ 0x%04x NOT TAKEN' % self.pc)

    def _cpl(self, instr):
        self.a ^= 0xff

        self.set_flag_n(True)
        self.set_flag_h(True)

        self.debug('CPL')

    def set_sub_flags(self, before, value, after):
        self.set_flag_c((after & 0x100) != 0)

        self.set_flag_z(after == 0)

        self.set_flag_pv((before < 0 and value >= 0 and after >= 0) or (before >= 0 and value < 0 and after < 0))

        before_sign = self.a & 0x80
        value_sign = value & 0x80
        after_sign = after & 0x80
        self.set_flag_pv(before_sign != value_sign and after_sign != before_sign)

        self.set_flag_s((after & 128) == 128)

        self.set_flag_n(True)

        self.set_flag_h((((before & 0x0f) - (value & 0x0f)) & 0x10) != 0)

    def _cp(self, instr):
        src = instr & 7
        (val, name) = self.get_src(src)

        temp = self.a - val
        self.set_sub_flags(self.a, val, temp)

        self.debug('CP %s' % name)

    def sub(self, val):
        result = self.a - val

        self.set_sub_flags(self.a, val, result)

        return result & 0xff

    def _sub(self, instr):
        c = instr & 8
        src = instr & 7

        (val, name) = self.get_src(src)

        if c:
            val += self.get_flag_c()

        self.a = self.sub(val)

        self.debug('%s %s [%02x]' % ('SBC' if c else 'SUB', name, val))

    def _sub_val(self, instr):
        use_c = instr == 0xde
        v = self.read_pc_inc()
        if use_c:
            v += self.get_flag_c()
        self.a = self.sub(v)
        self.debug('SUB 0x%02x' % v)

    def _inc_pair(self, instr):
        which = instr >> 4
        (v, name) = self.get_pair(which)

        v += 1
        v &= 0xffff
       
        self.set_pair(which, v)

        self.debug('INC %s' % name)

    def inc_flags(self, before):
        before = self.compl8(before)
        after = self.compl8((before + 1) & 0xff)

        self.set_flag_z(after == 0)
        self.set_flag_pv(before >= 0 and after < 0)
        self.set_flag_s(after < 0)
        self.set_flag_n(False)
        self.set_flag_h(not (after & 0x0F))

    def _inc_high(self, instr):
        which = instr >> 4
        if which == 0:
            self.inc_flags(self.b)
            self.b = (self.b + 1) & 0xff
            name = 'B'
        elif which == 1:
            self.inc_flags(self.d)
            self.d = (self.d + 1) & 0xff
            name = 'D'
        elif which == 2:
            self.inc_flags(self.h)
            self.h = (self.h + 1) & 0xff
            name = 'H'
        elif which == 3:
            a = self.m16(self.h, self.l)
            v = self.read_mem(a)
            self.inc_flags(v)
            self.write_mem(a, (v + 1) & 0xff)
            name = '(HL)'
        else:
            assert False

        self.debug('INC %s' % name)

    def _inc_low(self, instr):
        which = instr >> 4
        if which == 0:
            self.inc_flags(self.c)
            self.c = (self.c + 1) & 0xff
            name = 'C'
        elif which == 1:
            self.inc_flags(self.e)
            self.e = (self.e + 1) & 0xff
            name = 'E'
        elif which == 2:
            self.inc_flags(self.l)
            self.l = (self.l + 1) & 0xff
            name = 'L'
        elif which == 3:
            self.inc_flags(self.a)
            self.a = (self.a + 1) & 0xff
            name = 'A'
        else:
            assert False

        self.debug('INC %s' % name)

    def _add_pair_ixy(self, instr, is_ix):
        org_val = val = self.ix if is_ix else self.iy

        (v, name) = self.get_pair(instr >> 4)
        val += v

        self.set_flag_h((((org_val & 0x0fff) + (v & 0x0fff)) & 0x1000) == 0x1000)
        self.set_flag_c((val & 0x10000) == 0x10000)
        self.set_flag_n(False);

        val &= 0xffff

        if is_ix:
            self.ix = val
            self.debug('ADD IX, %s' % name)

        else:
            self.iy = val
            self.debug('ADD IY, %s' % name)

    def _add_pair(self, instr):
        self.add_pair(instr >> 4, False)

    def _adc_pair(self, instr):
        self.add_pair((instr >> 4) - 4, True)

    def add_pair(self, which, is_adc):
        before = self.m16(self.h, self.l)

        (value, name) = self.get_pair(which)
        if is_adc:
            value += self.get_flag_c()

        after = before + value

        self.set_flag_h((((before & 0x0fff) + (value & 0x0fff)) & 0x1000) == 0x1000)
        self.set_flag_c((after & 0x10000) == 0x10000)
        self.set_flag_n(False);

        after &= 0xffff

        (self.h, self.l) = self.u16(after)

        self.debug('ADD HL, %s' % name)

    def _dec_pair(self, instr):
        which = instr >> 4
        (v, name) = self.get_pair(which)
        v -= 1
        v &= 0xffff
        self.set_pair(which, v)
        self.debug('DEC %s' % name)

    def dec_flags(self, before):
        before = self.compl8(before)
        after = self.compl8((before - 1) & 0xff)

        self.set_flag_z(after == 0)
        self.set_flag_pv(before < 0 and after >= 0)
        self.set_flag_s((after & 0x80) == 0x80)
        self.set_flag_n(True)
        self.set_flag_h((after & 0x0f) == 0x0f)

    def _dec_high(self, instr):
        which = instr >> 4

        if which == 0:
            self.dec_flags(self.b)
            self.b = (self.b - 1) & 0xff
            name = 'B'
        elif which == 1:
            self.dec_flags(self.d)
            self.d = (self.d - 1) & 0xff
            name = 'D'
        elif which == 2:
            self.dec_flags(self.h)
            self.h = (self.h - 1) & 0xff
            name = 'H'
        elif which == 3:
            a = self.m16(self.h, self.l)
            v = self.read_mem(a)
            self.dec_flags(v)
            self.write_mem(a, (v - 1) & 0xff)
            name = '(HL)'
        else:
            assert False

        self.debug('INC x')

    def _dec_low(self, instr):
        which = instr >> 4
        if which == 0:
            self.dec_flags(self.c)
            self.c = (self.c - 1) & 0xff
            name = 'C'
        elif which == 1:
            self.dec_flags(self.e)
            self.e = (self.e - 1) & 0xff
            name = 'E'
        elif which == 2:
            self.dec_flags(self.l)
            self.l = (self.l - 1) & 0xff
            name = 'L'
        elif which == 3:
            self.dec_flags(self.a)
            self.a = (self.a - 1) & 0xff
            name = 'A'
        else:
            assert False

        self.debug('DEC x')

#--- flags

    def _rst(self, instr):
        un = instr & 8
        which = (instr >> 4) - 0x0c

        self.push(self.pc)

        if un:
            self.pc = 0x08 + (which << 4)

        else:
            self.pc = which << 4

        self.debug('RST %02x' % self.pc)

    def _ex_de_hl(self, instr):
        self.d, self.h = self.h, self.d
        self.e, self.l = self.l, self.e
        self.debug('EX DE,HL')

    def _ld_a_imem(self, instr):
        which = instr >> 4
        if which == 0:
            self.a = self.read_mem(self.m16(self.b, self.c))
            self.debug('LD A,(BC)')

        elif which == 1:
            self.a = self.read_mem(self.m16(self.d, self.e))
            self.debug('LD A,(DE)')

        else:
            assert False

    def _ld_imem(self, instr):
        which = instr >> 4
        if which == 2:
            a = self.read_pc_inc_16()
            v = self.read_mem_16(a)
            (self.h, self.l) = self.u16(v)
            self.debug('LD HL,(0x%04x)' % a)

        elif which == 3:
            a = self.read_pc_inc_16()
            self.a = self.read_mem(a)
            self.debug('LD A, (0x%04x)' % a)

        else:
            assert False

    def _exx(self, instr):
        self.b, self.b_ = self.b_, self.b
        self.c, self.c_ = self.c_, self.c
        self.d, self.d_ = self.d_, self.d
        self.e, self.e_ = self.e_, self.e
        self.h, self.h_ = self.h_, self.h
        self.l, self.l_ = self.l_, self.l
        self.debug('EXX')

    def _ex_af(self, instr):
        self.a, self.a_ = self.a_, self.a
        self.f, self.f_ = self.f_, self.f
        self.debug('EX AF')

    def _push_ixy(self, instr, is_ix):
        self.push(self.ix if is_ix else self.iy)
        self.debug('PUSH I%s' % 'X' if is_ix else 'Y')

    def _pop_ixy(self, instr, is_ix):
        if is_ix:
            self.ix = self.pop()
            self.debug('POP IX')

        else:
            self.iy = self.pop()
            self.debug('POP IY')

    def _jp_ixy(self, instr, is_ix):
        self.pc = self.ix if is_ix else self.iy

        self.debug('JP (I%s)' % 'X' if is_ix else 'Y')

    def _ld_mem_from_ixy(self, instr, is_ix):
            a = self.read_pc_inc_16()
            self.write_mem_16(a, self.ix if is_ix else self.iy)
            self.debug('LD (0x%04x),I%s' % (a, 'X' if is_ix else 'Y'))

    def _ld_ixy_from_mem(self, instr, is_ix):
        a = self.read_pc_inc_16()
        v = self.read_mem_16(a)

        if is_ix:
            self.ix = v
        else:
            self.iy = v

        self.debug('LD I%s,(0x%04x)' % ('X' if is_ix else 'Y', a))

    def _add_a_ixy_h(self, instr, is_x):
        org = self.a
        v = (self.ix if is_x else self.iy) >> 8
        self.a += v
        self.set_add_flags(org, v, self.a)
        self.a &= 0xff
        self.debug('ADD A,I%sH' % 'X' if is_ix else 'Y')

    def _add_a_ixy_l(self, instr, is_x):
        org = self.a
        v = (self.ix if is_x else self.iy) & 255
        self.a += v
        self.set_add_flags(org, v, self.a)
        self.a &= 0xff
        self.debug('ADD A,I%sL' % 'X' if is_ix else 'Y')

    def _dec_ixy(self, instr, is_x):
        if is_x:
            self.ix -= 1
            self.ix &= 0xffff
            self.debug('DEC IX')

        else:
            self.iy -= 1
            self.iy &= 0xffff
            self.debug('DEC IY')

    def _ld_sp_ixy(self, instr, is_x):
        if is_x:
            self.sp = self.ix
            self.debug('LD SP,IX')

        else:
            self.sp = self.iy
            self.debug('LD SP,IY')

    def init_xy(self):
        self.ixy_jumps = [ None ] * 256

        self.ixy_jumps[0x09] = self._add_pair_ixy
        self.ixy_jumps[0x19] = self._add_pair_ixy
        self.ixy_jumps[0x21] = self._ld_ixy
        self.ixy_jumps[0x22] = self._ld_mem_from_ixy
        self.ixy_jumps[0x23] = self._inc_ixy
        self.ixy_jumps[0x29] = self._add_pair_ixy
        self.ixy_jumps[0x2a] = self._ld_ixy_from_mem
        self.ixy_jumps[0x2b] = self._dec_ixy
        self.ixy_jumps[0x39] = self._add_pair_ixy
        self.ixy_jumps[0x46] = self._ld_X_ixy_deref
        self.ixy_jumps[0x4e] = self._ld_X_ixy_deref
        self.ixy_jumps[0x56] = self._ld_X_ixy_deref
        self.ixy_jumps[0x5e] = self._ld_X_ixy_deref
        self.ixy_jumps[0x66] = self._ld_X_ixy_deref
        self.ixy_jumps[0x6e] = self._ld_X_ixy_deref
        self.ixy_jumps[0x70] = self._ld_ixy_X
        self.ixy_jumps[0x71] = self._ld_ixy_X
        self.ixy_jumps[0x72] = self._ld_ixy_X
        self.ixy_jumps[0x73] = self._ld_ixy_X
        self.ixy_jumps[0x74] = self._ld_ixy_X
        self.ixy_jumps[0x75] = self._ld_ixy_X
        self.ixy_jumps[0x77] = self._ld_ixy_X
        self.ixy_jumps[0x7e] = self._ld_X_ixy_deref
        self.ixy_jumps[0x84] = self._add_a_ixy_h
        self.ixy_jumps[0x85] = self._add_a_ixy_l
        self.ixy_jumps[0x86] = self._add_a_deref_ixy
        self.ixy_jumps[0xa6] = self._and_a_ixy_deref
        self.ixy_jumps[0xbe] = self._cp_im_ixy
        self.ixy_jumps[0xcb] = self.ixy_bit
        self.ixy_jumps[0xe1] = self._pop_ixy
        self.ixy_jumps[0xe5] = self._push_ixy
        self.ixy_jumps[0xe9] = self._jp_ixy
        self.ixy_jumps[0xf9] = self._ld_sp_ixy

    def _ix(self, dummy):
        try:
            instr = self.read_pc_inc()
            self.ixy_jumps[instr](instr, True)

        except TypeError as te:
            self.debug('TypeError IX(%02x): %s' % (instr, te))
            assert False

    def _iy(self, dummy):
        try:
            instr = self.read_pc_inc()
            self.ixy_jumps[instr](instr, False)

        except TypeError as te:
            self.debug('TypeError IY(%02x): %s' % (instr, te))
            assert False

    def init_xy_bit(self):
        self.ixy_bit_jumps = [ None ] * 256

        for i in range(0x00, 0x08):
                self.ixy_bit_jumps[i] = self._rlc_ixy

#        for i in range(0x08, 0x10):
#                self.ixy_bit_jumps[i] = self._rrc_ixy

#        for i in range(0x10, 0x18):
#                self.ixy_bit_jumps[i] = self._rl_ixy

#        for i in range(0x18, 0x20):
#                self.ixy_bit_jumps[i] = self._rr_ixy

#        for i in range(0x20, 0x28):
#                self.ixy_bit_jumps[i] = self._sla_ixy

#        for i in range(0x28, 0x30):
#                self.ixy_bit_jumps[i] = self._sra_ixy

#        for i in range(0x38, 0x40):
#                self.ixy_bit_jumps[i] = self._srl_ixy

#        for i in range(0x40, 0x80):
#                self.ixy_bit_jumps[i] = self._bit_ixy

#        for i in range(0x80, 0xc0):
#                self.ixy_bit_jumps[i] = self._res_ixy

#        for i in range(0xc0, 0x100):
#                self.ixy_bit_jumps[i] = self._set_ixy

    def ixy_bit(self, instr, which):
        try:
            instr = self.read_pc_inc()
            self.debug('I%s: %02x' % ('X' if which else 'Y', instr))
            self.ixy_bit_jumps[instr](instr, which)

        except TypeError as te:
            self.debug('TypeError IXY_BIT(%02x): %s' % (instr, te))
            assert False

    def _ed(self, dummy):
        try:
            instr = self.read_pc_inc()
            self.debug('EXT: %02x' % instr)
            self.ed_jumps[instr](instr)

        except TypeError as te:
            self.debug('TypeError EXT(%02x): %s' % (instr, te))
            assert False

    def _ld_mem_pair(self, instr):
        which = (instr >> 4) -4
        a = self.read_pc_inc_16()
        (v, name) = self.get_pair(which)
        self.write_mem_16(a, v)
        self.debug('LD (0x%04x), %s' % (a, name))

    def _ld_pair_mem(self, instr):
        a = self.read_pc_inc_16()
        v = self.read_mem_16(a)
        name = self.set_pair((instr >> 4) - 4, v)
        self.debug('LD %s,(0x%04x) [%04x]' % (name, a, v))

    def init_ext(self):
        self.ed_jumps = [ None ] * 256

        self.ed_jumps[0x40] = self._in_ed_low
        self.ed_jumps[0x41] = self._out_c_low
        self.ed_jumps[0x42] = self._sbc_pair
        self.ed_jumps[0x43] = self._ld_mem_pair
        self.ed_jumps[0x45] = self._neg
        self.ed_jumps[0x46] = self._im
        self.ed_jumps[0x47] = self._ld_i_a
        self.ed_jumps[0x48] = self._in_ed_high
        self.ed_jumps[0x49] = self._out_c_high
        self.ed_jumps[0x4a] = self._adc_pair
        self.ed_jumps[0x4b] = self._ld_pair_mem
        self.ed_jumps[0x4f] = self._ld_r_a
        self.ed_jumps[0x50] = self._in_ed_low
        self.ed_jumps[0x51] = self._out_c_low
        self.ed_jumps[0x52] = self._sbc_pair
        self.ed_jumps[0x53] = self._ld_mem_pair
        self.ed_jumps[0x55] = self._neg
        self.ed_jumps[0x56] = self._im
        self.ed_jumps[0x57] = self._ld_a_i
        self.ed_jumps[0x58] = self._in_ed_high
        self.ed_jumps[0x59] = self._out_c_high
        self.ed_jumps[0x5a] = self._adc_pair
        self.ed_jumps[0x5b] = self._ld_pair_mem
        self.ed_jumps[0x5f] = self._ld_a_r
        self.ed_jumps[0x50] = self._in_ed_low
        self.ed_jumps[0x60] = self._in_ed_low
        self.ed_jumps[0x61] = self._out_c_low
        self.ed_jumps[0x62] = self._sbc_pair
        self.ed_jumps[0x63] = self._ld_mem_pair
        self.ed_jumps[0x65] = self._neg
        self.ed_jumps[0x66] = self._im
        self.ed_jumps[0x68] = self._in_ed_high
        self.ed_jumps[0x69] = self._out_c_high
        self.ed_jumps[0x6a] = self._adc_pair
        self.ed_jumps[0x6b] = self._ld_pair_mem
        self.ed_jumps[0x71] = self._out_c_low
        self.ed_jumps[0x72] = self._sbc_pair
        self.ed_jumps[0x73] = self._ld_mem_pair
        self.ed_jumps[0x75] = self._neg
        self.ed_jumps[0x76] = self._im
        self.ed_jumps[0x78] = self._in_ed_high
        self.ed_jumps[0x79] = self._out_c_high
        self.ed_jumps[0x7a] = self._adc_pair
        self.ed_jumps[0x7b] = self._ld_pair_mem
        self.ed_jumps[0xa0] = self._ldi
        self.ed_jumps[0xa3] = self._outi
        self.ed_jumps[0xb0] = self._ldir
        self.ed_jumps[0xb1] = self._cpir
        self.ed_jumps[0xb3] = self._otir
        self.ed_jumps[0xb9] = self._cpdr

    def _ld_i_a(self, instr):
        self.i = self.a
        self.debug('LD I,A')

    def _ld_a_i(self, instr):
        self.a = self.i
        self.debug('LD A,I')

    def _ld_r_a(self, instr):
        self.r = self.a
        self.debug('LD R,A')

    def _ld_a_r(self, instr):
        self.a = self.r
        self.debug('LD A,R')

    def _in(self, instr):
        a = self.read_pc_inc()
        self.a = self.in_(a)
        self.debug('IN A, (0x%02x) [%02x]' % (a, self.a))

    def _ld_sp_hl(self, instr):
        self.sp = self.m16(self.h, self.l)
        self.debug('LD SP, HL [%04x]' % self.sp)

    def _add_a_val(self, instr):
        use_c = instr == 0xce
        v = self.read_pc_inc()
        old_val = self.a
        self.a += v

        if use_c:
            self.a += self.get_flag_c()

        self.set_add_flags(old_val, v, self.a)

        self.a &= 0xff
        self.debug('ADD A, 0x%02d [%02x]' % (v, self.a))

    def _ld_pair_from_a(self, instr):
        which = instr >> 4
        if which == 0:  # (BC) = a
            self.write_mem(self.m16(self.b, self.c), self.a)
            self.debug('LD (BC),A')
        elif which == 1:
            self.write_mem(self.m16(self.d, self.e), self.a)
            self.debug('LD (DE),A')
        else:
            assert False

    def _ld_imem_from(self, instr):
        which = instr >> 4
        if which == 2:  # LD (**), HL
            a = self.read_pc_inc_16()
            self.write_mem(a, self.l)
            self.write_mem((a + 1) & 0xffff, self.h)
            self.debug('LD (0x%04x),HL' % a)
        elif which == 3:  # LD (**), A
            a = self.read_pc_inc_16()
            self.write_mem(a, self.a)
            self.debug('LD (0x%04x),A' % a)
        else:
            assert False

    def _rlca(self, instr):
        self.set_flag_n(False)
        self.set_flag_h(False)

        self.a <<= 1

        if self.a & 0x100:
            self.set_flag_c(True)
            self.a |= 1

        else:
            self.set_flag_c(False)

        self.a &= 0xff

        self.debug('RLCA')

    def _rla(self, instr):
        self.set_flag_n(False)
        self.set_flag_h(False)

        self.a <<= 1

        if self.get_flag_c():
            self.a |= 1

        if self.a & 0x100:
            self.set_flag_c(True)

        else:
            self.set_flag_c(False)

        self.a &= 0xff

        self.debug('RLA')

    def _rlc(self, instr):
        src = instr & 0x7
        (val, name) = self.get_src(src)

        self.set_flag_n(False)
        self.set_flag_h(False)

        val <<= 1

        if val & 0x100:
            self.set_flag_c(True)
            val |= 1

        else:
            self.set_flag_c(False)

        val &= 0xff

        dst = src
        self.set_dst(dst, val)

        self.set_flag_pv(self.parity(val))
        self.set_flag_s((val & 0x80) == 0x80)

        self.debug('RLC %s' % name)

    def _rlc_ixy(self, instr, is_ix):
        offset = self.compl8(self.read_pc_inc())
        ixy = self.ix if is_ix else self.iy
        name = 'IX' if is_ix else 'IY'
        a = (ixy + offset) & 0xffff
        val = self.read_mem(a)

        self.set_flag_n(False)
        self.set_flag_h(False)

        val <<= 1

        if val & 0x100:
            self.set_flag_c(True)
            val |= 1

        else:
            self.set_flag_c(False)

        val &= 0xff

        dst = instr & 0x7
        if dst == 6:
            self.write_mem(a, val)

        else:
            dst_name = self.set_dst(dst, val)

        self.set_flag_pv(self.parity(val))
        self.set_flag_s((val & 0x80) == 0x80)

        self.debug('RLC (%s + 0x%02x), %s' % (name, offset, dst_name))

    def _cp_mem(self, instr):
        val = self.read_pc_inc()

        temp = self.a - val
        self.set_sub_flags(self.a, val, temp)

        self.debug('CP 0x%02x' % val)

    def _ldir(self, instr):
        self.set_flag_n(False)
        self.set_flag_pv(False)
        self.set_flag_h(False)

        bc = self.m16(self.b, self.c)
        de = self.m16(self.d, self.e)
        hl = self.m16(self.h, self.l)

        while True:
            v = self.read_mem(hl)
            self.write_mem(de, v)

            hl += 1
            hl &= 0xffff

            de += 1
            de &= 0xffff

            bc -= 1
            bc &= 0xffff

            if bc == 0:
                break

        (self.b, self.c) = self.u16(bc)
        (self.d, self.e) = self.u16(de)
        (self.h, self.l) = self.u16(hl)
        
        self.debug('LDIR')

    def _rr(self, instr):
        src = instr & 7
        self.set_flag_n(False)
        self.set_flag_h(False)

        (val, name) = self.get_src(src)
        old_c = self.get_flag_c()
        self.set_flag_c((val & 1) == 1)

        val >>= 1
        val |= old_c << 7

        self.set_flag_pv(self.parity(val))
        self.set_flag_z(val == 0)
        self.set_flag_s(val >= 128)

        dst = src
        self.set_dst(dst, val)

        self.debug('RR %s' % name)

    def _rl(self, instr):
        src = instr & 7
        self.set_flag_n(False)
        self.set_flag_h(False)

        (val, name) = self.get_src(src)
        val <<= 1
        val |= self.get_flag_c()
        self.set_flag_c(val > 255)
        val &= 0xff

        self.set_flag_pv(self.parity(val))
        self.set_flag_z(val == 0)
        self.set_flag_s(val >= 128)

        dst = src
        self.set_dst(dst, val)

        self.debug('RL %s' % name)

    def _rrc(self, instr):
        src = instr & 7
        self.set_flag_n(False)
        self.set_flag_h(False)

        (val, name) = self.get_src(src)
        old_0 = val & 1
        self.set_flag_c(old_0 == 1)

        val >>= 1
        val |= old_0 << 7

        self.set_flag_pv(self.parity(val))
        self.set_flag_z(val == 0)
        self.set_flag_s(val >= 128)

        dst = src
        self.set_dst(dst, val)

        self.debug('RRC %s' % name)

    def _im(self, instr):
        self.im = instr & 1

        self.debug('IM %d' % self.im)

    def _ret_always(self, instr):
        self.pc = self.pop()

        self.debug('RET')

    def _ret(self, flag, flag_name):
        if flag:
            self.pc = self.pop()

        self.debug('RET %s' % flag_name)

    def _call_flag(self, flag, flag_name):
        a = self.read_pc_inc_16()

        if flag:
            self.push(self.pc)
            self.pc = a

        self.debug('CALL %s,0x%04x' % (flag_name, a))

    def _scf(self, instr):
        self.set_flag_c(True)
        self.set_flag_n(False)
        self.set_flag_h(False)

    def _ex_sp_hl(self, instr):
        hl = self.m16(self.h, self.l)
        org_sp_deref = self.read_mem_16(self.sp)
        self.write_mem_16(self.sp, hl)

        (self.h, self.l) = self.u16(org_sp_deref)

        self.debug('EX (SP),HL')

    def _rrca(self, instr):
        self.set_flag_n(False)
        self.set_flag_h(False)

        bit0 = self.a & 1
        self.a >>= 1
        self.a |= bit0 << 7

        self.set_flag_c(bit0 == 1)

        self.debug('RRCA')

    def _di(self, instr):
        self.interrupts = False
        self.debug('DI')

    def _ei(self, instr):
        self.interrupts = True
        self.debug('EI')

    def _ccf(self, instr):
        self.set_flag_c(not self.get_flag_c())
        self.set_flag_n(False)
        self.set_flag_h(False)

        self.debug('CCF')

    def _bit(self, instr):
        nr = (instr - 0x40) >> 3
        src = instr & 7
        (val, src_name) = self.get_src(src)

        self.set_flag_n(False)
        self.set_flag_h(True)

        self.set_flag_z((val & (1 << nr)) == 0)

        self.debug('BIT %d, %s' % (nr, src_name))

    def _srl(self, instr):
        src = instr & 7
        (val, src_name) = self.get_src(src)

        self.set_flag_n(False)
        self.set_flag_h(False)
        self.set_flag_c((val & 1) == 1)
        self.set_flag_z(val == 0)
        self.set_flag_s(val >= 128)

        val >>= 1

        self.set_flag_pv(self.parity(val))

        dst = src
        self.set_dst(dst, val)

        self.debug('SRL %s' % src_name)

    def _set(self, instr):
        bit = (instr - 0xc0) >> 3
        src = instr & 7

        (val, src_name) = self.get_src(src)

        val |= 1 << bit

        dst = src
        self.set_dst(dst, val)

        self.debug('SET %d, %s' % (bit, src_name))

    def _res(self, instr):
        bit = (instr - 0x80) >> 3
        src = instr & 7

        (val, src_name) = self.get_src(src)

        val &= ~(1 << bit)

        dst = src
        self.set_dst(dst, val)

        self.debug('RES %d, %s' % (bit, src_name))

    def _sbc_pair(self, instr):
        which = (instr >> 4) - 4
        (v, name) = self.get_pair(which)

        before = self.m16(self.h, self.l)
        value = v + self.get_flag_c()
        after = before - value

        self.set_flag_c((after & 0x10000) == 0x10000)
        self.set_flag_z((after & 0xffff) == 0)
        self.set_flag_n(True)
        self.set_flag_s((after & 0x8000) == 0x8000)
        self.set_flag_h((((before & 0x0fff) - (value & 0x0fff)) & 0x1000) == 0x1000)

        before_sign = before & 0x8000;
        value_sign = value & 0x8000;
        after_sign = after & 0x8000;
        self.set_flag_pv(before_sign != value_sign and after_sign != before_sign)
 
        self.set_pair(2, after & 0xffff)

        self.debug('SUB HL,%s' % name)

    def _neg(self, instr):
        org_a = self.compl8(self.a)
        a = -org_a

        self.set_sub_flags(org_a, 0, a)

        self.a = a & 0xff

        self.debug('NEG')

    def _ld_ixy(self, instr, is_ix):
        v = self.read_pc_inc_16()

        if is_ix:
            self.ix = v
            self.debug('LD ix,**')

        else:
            self.iy = v
            self.debug('LD iy,**')

    def _inc_ixy(self, instr, is_ix):
        if is_ix:
            self.ix = (self.ix + 1) & 0xffff
            self.debug('INC IX')
        
        else:
            self.iy = (self.iy + 1) & 0xffff
            self.debug('INC IX')

    def _out_c_low(self, instr):
        which = (instr >> 4) - 4

        if which == 0:
            v = self.b
            name = 'B'
        elif which == 1:
            v = self.d
            name = 'D'
        elif which == 2:
            v = self.h
            name = 'H'
        elif which == 3:
            v = 0
            name = '0'
        else:
            self.ui(-1)

        self.out(self.c, v)

        self.debug('OUT (C), %s' % name)

    def _out_c_high(self, instr):
        which = (instr >> 4) - 4

        if which == 0:
            v = self.c
            name = 'C'
        elif which == 1:
            v = self.e
            name = 'E'
        elif which == 2:
            v = self.l
            name = 'L'
        elif which == 3:
            v = self.a
            name = 'A'
        else:
            self.ui(-1)

        self.out(self.c, v)

        self.debug('OUT (C), %s' % name)

    def _jp_ref_iy(self):
        self.pc = self.iy

        self.debug('JP (IY)')

    def _in_ed_low(self, instr):
        which = (instr >> 4) - 4
        v = self.in_(self.c)

        if which == 0:
            self.b = v
            name = 'B'
        elif which == 1:
            self.d = v
            name = 'D'
        elif which == 2:
            self.h = v
            name = 'H'
        else:
            self.ui(-1)

        self.debug('IN %s,(C)' % name)

    def _in_ed_high(self, instr):
        which = (instr >> 4) - 4
        v = self.in_(self.c)

        if which == 0:
            self.c = v
            name = 'C'
        elif which == 1:
            self.e = v
            name = 'E'
        elif which == 2:
            self.l = v
            name = 'L'
        elif which == 3:
            self.a = v
            name = 'A'
        else:
            self.ui(-1)

        self.debug('IN %s,(C)' % name)

    def _outi(self, instr):
        a = self.m16(self.h, self.l)
        self.out(self.c, self.read_mem(a))

        a += 1
        a &= 0xffff

        (self.h, self.l) = self.u16(a)

        self.b -= 1
        self.b &= 0xff

        self.debug('OUTI')

    def _ld_ixy_X(self, instr, is_ix):
        which = instr & 15
        offset = self.compl8(self.read_pc_inc())
        ixy = self.ix if is_ix else self.iy
        name = 'IX' if is_ix else 'IY'
        a = (ixy + offset) & 0xffff

        (val, src_name) = self.get_src(which)
        self.write_mem(a, val)

        self.debug('LD (%s + *),%s' % (name, src_name))

    def _ldi(self, instr):
        self.set_flag_n(False)
        self.set_flag_pv(False)
        self.set_flag_h(False)

        bc = self.m16(self.b, self.c)
        de = self.m16(self.d, self.e)
        hl = self.m16(self.h, self.l)

        v = self.read_mem(hl)
        self.write_mem(de, v)
        hl += 1
        hl &= 0xffff

        de += 1
        de &= 0xffff

        bc -= 1
        bc &= 0xffff

        (self.b, self.c) = self.u16(bc)
        (self.d, self.e) = self.u16(de)
        (self.h, self.l) = self.u16(hl)

        self.debug('LDI')

    def _cpdr(self, instr):
        a = self.m16(self.h, self.l)
        c = self.m16(self.b, self.c)

        result = 0

        while True:
            mem = self.read_mem(a)

            a = self.decp16(a)
            c = self.decp16(c)

            result = self.a - mem

            if result == 0 or c == 0:
                break

        (self.h, self.l) = self.u16(a)
        (self.b, self.c) = self.u16(c)

        self.set_flag_n(True)
        self.set_flag_pv(False)
        self.set_flag_s(result < 0)
        self.set_flag_z(result == 0)

        self.debug('CPDR')

    def _otir(self, instr):
        a = self.m16(self.h, self.l)

        while True:
            mem = self.read_mem(a)
            self.write_io(self.c, mem)

            a = self.incp16(a)
            self.b -= 1

            if self.b == 0:
                break

        (self.h, self.l) = self.u16(a)

        self.set_flag_n(True)
        self.set_flag_z(True)

        self.debug('OTIR')

    def _cpir(self, instr):
        a = self.m16(self.h, self.l)
        c = self.m16(self.b, self.c)

        result = 0

        while True:
            mem = self.read_mem(a)

            a = self.incp16(a)
            c = self.decp16(c)

            result = self.a - mem

            if result == 0 or c == 0:
                break

        (self.h, self.l) = self.u16(a)
        (self.b, self.c) = self.u16(c)

        self.set_flag_n(True)
        self.set_flag_pv(False)
        self.set_flag_s(result < 0)
        self.set_flag_z(result == 0)

        self.debug('CPIR')

    def _cp_im_ixy(self, instr, is_ix):
        offset = self.compl8(self.read_pc_inc())
        a = ((self.ix if is_ix else self.iy) + offset) & 0xffff

        v  = self.read_mem(a)

        temp = self.a - v
        self.set_sub_flags(self.a, v, temp)

        self.debug('CP (I%s + *)' % 'X' if is_ix else 'Y')

    def _and_a_ixy_deref(self, instr, is_ix):
        offset = self.compl8(self.read_pc_inc())
        a = ((self.ix if is_ix else self.iy) + offset) & 0xffff

        self.a &= self.read_mem(a)

        self.and_flags()

        self.debug('AND (I%s + *)' % 'X' if is_ix else 'Y')

    def _ld_X_ixy_deref(self, which, is_ix):
        offset = self.compl8(self.read_pc_inc())
        ixy = self.ix if is_ix else self.iy
        a = (ixy + offset) & 0xffff

        v = self.read_mem(a)
 
        if which == 0x46:
            self.b = v
            name = 'B'
 
        elif which == 0x4e:
            self.c = v
            name = 'C'
 
        elif which == 0x56:
            self.d = v
            name = 'D'
 
        elif which == 0x5e:
            self.e = v
            name = 'E'
 
        elif which == 0x66:
            self.h = v
            name = 'H'
 
        elif which == 0x6e:
            self.l = v
            name = 'L'
 
        elif which == 0x7e:
            self.a = v
            name = 'A'

        else:
            assert False

        self.debug('LD %s,(IX+*)' % name)

    def _add_a_deref_ixy(self, instr, is_ix):
        offset = self.compl8(self.read_pc_inc())
        ixy = self.ix if is_ix else self.iy
        name = 'IX' if is_ix else 'IY'
        a = (ixy + offset) & 0xffff
        old_val = self.a

        v = self.read_mem(a)

        self.a += v
        self.set_add_flags(old_val, v, self.a)
        self.a &= 0xff

        self.debug('ADD A,(%s+*)' % name)

    # from https://stackoverflow.com/questions/8119577/z80-daa-instruction/8119836
    def _daa(self, instr):
        t = 0

        if self.get_flag_h() or (self.a & 0x0f) > 9:
            t += 1

        if self.get_flag_c() or self.a > 0x99:
            t += 2
            self.set_flag_c(True)

        if self.get_flag_n() and not self.get_flag_h():
            self.set_flag_h(False)

        else:
            if self.get_flag_n() and self.get_flag_h():
                self.set_flag_h((self.a & 0x0f) < 6)
            else:
                self.set_flag_h((self.a & 0x0f) >= 0x0a)

        if t == 1:
            self.a += 0xfa if self.get_flag_n() else 0x06

        elif t == 2:
            self.a += 0xa0 if self.get_flag_n() else 0x60

        elif t == 3:
            self.a += 0x9a if self.get_flag_n() else 0x66

        self.a &= 0xff

        self.set_flag_s((self.a & 128) == 128)
        self.set_flag_z(self.a == 0x00)
        self.set_flag_pv(self.parity(self.a))

        self.debug('DAA')

    def _jp_hl(self, instr):
        self.pc = self.m16(self.h, self.l)

        self.debug('JP (HL)')
