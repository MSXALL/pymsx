import time

class z80:
    def __init__(self, read_mem, write_mem, read_io, write_io, debug):
        self.read_mem = read_mem
        self.write_mem = write_mem
        self.read_io = read_io
        self.write_io = write_io
        self.debug_out = debug

        self.reset()

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

    def step(self):
        if self.int:
            self.int = False
            self.debug('Interrupt %f' % time.time())
            self.push(self.pc)
            self.pc = 0x38

        old_pc = self.pc
        instr = self.read_pc_inc()
        #print('%04x %02x  ' % (old_pc, instr), end='')

        self.cycles += 1 # FIXME

        major = instr >> 4
        minor = instr & 15
        minor1 = instr & 8
        minor2 = instr & 7

        if major <= 0x03:
            if minor == 0x00:
                if major == 0x00:
                    pass  # NOP

                elif major == 0x01:
                    self._djnz()

                elif major == 0x02:
                    self._jr(not self.get_flag_z(), "nz")

                elif major == 0x03:
                    self._jr(not self.get_flag_c(), "nc")

                else:
                    self.ui(instr)

            elif minor == 0x01:
                self._ld_pair(major)

            elif minor == 0x02:
                if major == 0x00 or major == 0x01:
                    self._ld_pair_from_a(major)

                elif major == 0x02 or major == 0x03:
                    self._ld_imem_from(major)

                else:
                    self.ui(instr)

            elif minor == 0x03:
                self._inc_pair(major)

            elif minor == 0x04:
                self._inc_high(major)

            elif minor == 0x05:
                self._dec_high(major)

            elif minor == 0x06:
                self._ld_val_high(major)

            elif minor == 0x07:
                if major == 0:
                    self._rlca()

                elif major == 0x01:
                    self._rla()

                elif major == 0x03:
                    self._scf()

                else:
                    self.ui(instr)

            elif minor == 0x08:
                if major == 0:
                    self._ex_af()

                elif major == 1:
                    self._jr(True, '')

                elif major == 2:
                    self._jr(self.get_flag_z(), 'z')

                elif major == 3:
                    self._jr(self.get_flag_c(), 'c')

                else:
                    self.ui(instr)

            elif minor == 0x09:
                self._add_pair(major)

            elif minor == 0x0a:
                if major == 0x00 or major == 0x01:
                    self._ld_a_imem(major)

                elif major == 0x02 or major == 0x03:
                    self._ld_imem(major)

                else:
                    self.ui(instr)

            elif minor == 0x0b:
                self._dec_pair(major)

            elif minor == 0x0c:
                self._inc_low(major)

            elif minor == 0x0d:
                self._dec_low(major)

            elif minor == 0x0e:
                self._ld_val_low(major)

            elif minor == 0x0f:
                if major == 0x00:
                    self._rrca()

                elif major == 0x01:
                    self._rr(7)

                elif major == 0x02:  # CPL
                    self._cpl()

                elif major == 0x03:
                    self._ccf()

                else:
                    self.ui(instr)

            else:
                self.ui(instr)

        elif major >= 0x04 and major <= 0x07:  # LD
            self._ld(instr)

        elif major == 0x08:  # ADD/ADC
            self._add(minor2, minor1)

        elif major == 0x09:  # SUB/SBC
            self._sub(minor2, minor1)

        elif major == 0x0a:  # AND/XOR
            if minor1:
                self._xor(minor2)

            else:
                self._and(minor2)

        elif major == 0x0b:  # OR/CP
            if minor1:
                self._cp(minor2)

            else:
                self._or(minor2)

        elif major >= 0x0c:
            if minor == 0x00:
                if major == 0x0c:
                    self._ret(not self.get_flag_z(), 'NZ')

                elif major == 0x0d:
                    self._ret(not self.get_flag_c(), 'NC')

                elif major == 0x0e:
                    self._ret(not self.get_flag_pv(), 'PO')

                elif major == 0x0f:
                    self._ret(not self.get_flag_s(), 'P')

                else:
                    self.ui(instr)

            elif minor == 0x01:
                self._pop(major - 0x0c)

            elif minor == 0x02:
                if major == 0x0c:
                    self._jp(not self.get_flag_z(), 'NZ')

                elif major == 0x0d:
                    self._jp(not self.get_flag_c(), 'NC')

                elif major == 0x0e:
                    self._jp(not self.get_flag_pv(), 'PO')

                elif major == 0x0f:
                    self._jp(not self.get_flag_s(), 'P')

                else:
                    self.ui(instr)

            elif minor == 0x03:
                if major == 0x0c:  # JP
                    self._jp(True, None)

                elif major == 0x0d:  # OUT (*), a
                    self._out()

                elif major == 0x0e:  # EX (SP),HL
                    self._ex_sp_hl()

                elif major == 0x0f:  # DI
                    self._di()

                else:
                    self.ui(instr)

            elif minor == 0x04:
                if major == 0x0c:
                    self._call_flag(not self.get_flag_z(), 'NZ')

                elif major == 0x0d:
                    self._call_flag(not self.get_flag_c(), 'NC')

                elif major == 0x0e:
                    self._call_flag(not self.get_flag_pv(), 'PO')

                elif major == 0x0f:
                    self._call_flag(self.get_flag_pv(), 'P')

                else:
                    self.ui(instr)

            elif minor == 0x05:  # PUSH
                self._push(major - 0x0c)

            elif minor == 0x06:
                if major == 0x0c:  # ADD A, *
                    self._add_a_val(False)

                elif major == 0x0d:  # SUB *
                    self._sub_val()

                elif major == 0x0e:  # AND *
                    self._and_val()

                elif major == 0x0f:  # OR *
                    self._or_val()

                else:
                    self.ui(instr)

            elif minor == 0x07:
                self._rst(minor1, major - 0x0c)

            elif minor == 0x08:
                if major == 0x0c:
                    self._ret(self.get_flag_z(), 'Z')

                elif major == 0x0d:
                    self._ret(self.get_flag_c(), 'C')

                elif major == 0x0e:
                    self._ret(not self.get_flag_s(), 'P')

                elif major == 0x0f:
                    self._ret(self.get_flag_s(), 'M')

                else:
                    self.ui(instr)

            elif minor == 0x09:
                if major == 0x0c:  # RET
                    self._ret_always()

                elif major == 0x0d:  # EXX
                    self._exx()

                elif major == 0x0f:  # LD SP, HL
                    self._ld_sp_hl()

                else:
                    self.ui(instr)

            elif minor == 0x0a:
                if major == 0x0c:  # JP Z,**
                    self._jp(self.get_flag_z(), 'Z')

                elif major == 0x0d:  # JP c,**
                    self._jp(self.get_flag_c(), 'C')

                elif major == 0x0e:  # JP pe,**
                    self._jp(self.get_flag_pv(), 'PE')

                elif major == 0x0f:  # JP M,**
                    self._jp(self.get_flag_s(), 'M')

                else:
                    self.ui(instr)

            elif minor == 0x0b:
                if major == 0x0c:  # BITS
                    self.bits()

                elif major == 0x0d:  # IN A,(*)
                    self._in()

                elif major == 0x0e:  # EX DE, HL
                    self._ex_de_hl()

                elif major == 0x0f:  # EI
                    self._ei()

                else:
                    self.ui(instr)

            elif minor == 0x0c:
                if major == 0x0c:  # CALL Z,**
                    self._call_flag(self.get_flag_z(), 'Z')

                elif major == 0x0d:  # CALL C,**
                    self._call_flag(self.get_flag_c(), 'C')

                elif major == 0x0e:  # CALL PE,**
                    self._call_flag(self.get_flag_pv(), 'PE')

                elif major == 0x0f:  # CALL M,**
                    self._call_flag(self.get_flag_s(), 'M')

                else:
                    self.ui(instr)

            elif minor == 0x0d:
                if major == 0x0c:  # CALL
                    self._call()

                elif major == 0x0d:
                    self._ix()

                elif major == 0x0e:
                    self._ed()

                elif major == 0x0f:
                    self._iy()

                else:
                    self.ui(instr)

            elif minor == 0x0e:
                if major == 0x0c:
                    self._add_a_val(True)

                elif major == 0x0e:
                    self._xor_mem()

                elif major == 0x0f:
                    self._cp_mem()

                else:
                    self.ui(instr)

            elif minor == 0x0f:
                self._rst(minor1, major - 0x0c)

            else:
                self.ui(instr)

        else:
            self.ui(instr)

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

    def parity(self, v):
        count = 0

        for i in range(0, 8):
            count += (v & (1 << i)) != 0

        return (count & 1) == 0

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

    def bits(self):
        instr = self.read_pc_inc()

        ui = (0xcb << 8) | instr

        major = instr >> 4
        minor = instr & 15
        minor1 = instr & 8
        minor2 = instr & 7

        if major == 0x00:
            if minor1:
                self.ui(ui)

            else:
                self._rlc(minor2)

        elif major == 0x01:
            if minor1:
                self._rr(minor2)

            else:
                self._rl(minor2)

        elif major == 0x02:
            if minor1:
                self.ui(ui)

            else:
                self._sla(minor2)

        elif major == 0x03:
            self._srl(minor2)

        elif major >= 0x04 and major <= 0x07:
            i = instr - 0x40
            self._bit(i >> 3, minor2)

        elif major >= 0x08 and major <= 0x0b:
            i = instr - 0x80
            self._res(i >> 3, minor2)

        elif major >= 0x0c:
            i = instr - 0xc0
            self._set(i >> 3, minor2)

        else:
            self.ui(ui)

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

    def _add(self, src, c):
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

    def _or(self, src):
        (val, name) = self.get_src(src)
        self.a |= val

        self.or_flags()

        self.debug('OR %s' % name)

    def _or_val(self):
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

    def _and(self, src):
        (val, name) = self.get_src(src)
        self.a &= val

        self.and_flags()

        self.debug('AND %s' % name)

    def _and_val(self):
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

    def _xor(self, src):
        (val, name) = self.get_src(src)

        self.a ^= val

        self.xor_flags()

        self.debug('XOR %s' % name)

    def _xor_mem(self):
        val = self.read_pc_inc()

        self.a ^= val

        self.xor_flags()

        self.debug('XOR %02x' % val)

    def _out(self):
        a = self.read_pc_inc()
        self.out(a, self.a)
        self.debug('OUT (0x%02x), A [%02x]' % (a, self.a))

    def _sla(self, src):
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

    def _ld_val_low(self, which):
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

    def _ld_val_high(self, which):
        val = self.read_pc_inc()

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

    def _ld_pair(self, which):
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

    def _call(self):
        a = self.read_pc_inc_16()
        self.push(self.pc)
        self.pc = a

        self.debug('CALL 0x%04x' % a)

    def _push(self, which):
        if which == 3:
            v = self.m16(self.a, self.f)
            name = 'AF'

        else:
            (v, name) = self.get_pair(which)

        self.push(v)

        self.debug('PUSH %s' % name)

    def _pop(self, which):
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

    def _djnz(self):
        offset = self.compl8(self.read_pc_inc())

        self.b -= 1
        self.b &= 0xff

        if self.b > 0:
            self.pc += offset
            self.debug('DJNZ 0x%04x' % self.pc)

        else:
            self.debug('DJNZ 0x%04x NOT TAKEN' % self.pc)

    def _cpl(self):
        self.a ^= 0xff

        self.set_flag_n(True)
        self.set_flag_h(True)

        self.debug('CPL')

    def set_sub_flags(self, before, value, after):
        self.set_flag_c((after & 0x100) != 0)

        self.set_flag_z(after == 0)

        before = self.compl8(before)
        value = self.compl8(value)
        after = self.compl8(after & 0xff)
        self.set_flag_pv((before < 0 and value >= 0 and after >= 0) or (before >= 0 and value < 0 and after < 0))

        self.set_flag_s((after & 128) == 128)

        self.set_flag_n(True)

        self.set_flag_h((((before & 0x0f) - (value & 0x0f)) & 0x10) != 0)

    def _cp(self, src):
        (val, name) = self.get_src(src)

        temp = self.a - val
        self.set_sub_flags(self.a, val, temp)

        self.debug('CP %s' % name)

    def sub(self, val):
        result = self.a - val

        self.set_sub_flags(self.a, val, result)

        return result & 0xff

    def _sub(self, src, c):
        (val, name) = self.get_src(src)

        if c:
            val += self.get_flag_c()

        self.a = self.sub(val)

        self.debug('%s %s [%02x]' % ('SBC' if c else 'SUB', name, val))

    def _sub_val(self):
        v = self.read_pc_inc()
        self.a = self.sub(v)
        self.debug('SUB 0x%02x' % v)

    def _inc_pair(self, which):
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

    def _inc_high(self, which):
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

    def _inc_low(self, which):
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

    def _add_pair(self, which):
        org_val = val = self.m16(self.h, self.l)

        (v, name) = self.get_pair(which)
        val += v

        self.set_flag_h((((org_val & 0x0fff) + (v & 0x0fff)) & 0x1000) == 0x1000)
        self.set_flag_c((val & 0x10000) == 0x10000)
        self.set_flag_n(False);

        val &= 0xffff

        (self.h, self.l) = self.u16(val)

        self.debug('ADD HL, %s' % name)

    def _dec_pair(self, which):
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

    def _dec_high(self, which):
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

    def _dec_low(self, which):
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

    def _rst(self, un, which):
        self.push(self.pc)

        if un:
            self.pc = 0x08 + (which << 4)

        else:
            self.pc = which << 4

        self.debug('RST %02x' % self.pc)

    def _ex_de_hl(self):
        self.d, self.h = self.h, self.d
        self.e, self.l = self.l, self.e
        self.debug('EX DE,HL')

    def _ld_a_imem(self, which):
        if which == 0:
            self.a = self.read_mem(self.m16(self.b, self.c))
            self.debug('LD A,(BC)')

        elif which == 1:
            self.a = self.read_mem(self.m16(self.d, self.e))
            self.debug('LD A,(DE)')

        else:
            assert False

    def _ld_imem(self, which):
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

    def _exx(self):
        self.b, self.b_ = self.b_, self.b
        self.c, self.c_ = self.c_, self.c
        self.d, self.d_ = self.d_, self.d
        self.e, self.e_ = self.e_, self.e
        self.h, self.h_ = self.h_, self.h
        self.l, self.l_ = self.l_, self.l
        self.debug('EXX')

    def _ex_af(self):
        self.a, self.a_ = self.a_, self.a
        self.f, self.f_ = self.f_, self.f
        self.debug('EX AF')

    def _push_iy(self):
        self.push(self.iy)

        self.debug('PUSH IY')

    def _pop_iy(self):
        self.iy = self.pop()

        self.debug('POP IY')

    def _push_ix(self):
        self.push(self.ix)

        self.debug('PUSH IX')

    def _pop_ix(self):
        self.ix = self.pop()

        self.debug('POP IX')

    def _iy(self):
        instr = self.read_pc_inc()

        ui = (0xfd << 8) | instr

        major = instr >> 4
        minor = instr & 15
        minor1 = instr & 8
        minor2 = instr & 7

        if major == 0x02:
            if minor == 0x01:  # LD IY,**
                self._ld_iy()

            elif minor == 0x0a:
                a = self.read_pc_inc_16()
                v = self.read_mem_16(a)
                self.iy = v
                self.debug('LD IY,(0x%04x)' % a)

            else:
                self.ui(ui)

        elif major == 0x05:
            if minor == 0x06:
                self._ld_d_iy()

            elif minor == 0x0e:
                self._ld_e_iy()

            else:
                self.ui(ui)

        elif major == 0x0e:
            if minor == 0x01:  # POP IY
                self._pop_iy()

            elif minor == 0x05:  # PUSH IY
                self._push_iy()

            elif minor == 0x09:  # JP (IY)
                self._jp_ref_iy()

            else:
                self.ui(ui)

        elif major == 0x07:
            if minor == 0x0e:  # LD A,(IY + *)
                self._ld_a_iy()

            else:
                self.ui(ui)

        else:
            self.ui(ui)

    def _ix(self):
        instr = self.read_pc_inc()

        ui = (0xdd << 8) | instr

        major = instr >> 4
        minor = instr & 15
        minor1 = instr & 8
        minor2 = instr & 7

        if major == 0x02:
            if minor == 0x01:  # LD IX,**
                self._ld_ix()

            elif minor == 0x03:  # INC IX
                self._inc_ix()

            else:
                self.ui(ui)

        elif major == 0x04:
            if minor == 0x06:
                self._ld_X_ix_deref(instr)

            elif minor == 0x0e:
                self._ld_X_ix_deref(instr)

            else:
                self.ui(ui)

        elif major == 0x05:
            if minor == 0x06:
                self._ld_X_ix_deref(instr)

            elif minor == 0x0e:
                self._ld_X_ix_deref(instr)

            else:
                self.ui(ui)

        elif major == 0x06:
            if minor == 0x06:
                self._ld_X_ix_deref(instr)

            elif minor == 0x0e:
                self._ld_X_ix_deref(instr)

            else:
                self.ui(ui)

        elif major == 0x07:
            if minor <= 0x05:
                self._ld_ix_X(minor)
 
            elif minor == 0x06:
                self._ld_X_ix_deref(instr)

            elif minor == 0x0e:
                self._ld_ix_im()

            else:
                self.ui(ui)

        elif major == 0x0a:
            if minor == 0x06:
                self._and_a_ix_deref()

            else:
                self.ui(ui)

        elif major == 0x0b:
            if minor == 0x0e:
                self._cp_im_ix()

            else:
                self.ui(ui)

        elif major == 0x0c:
            if minor == 0x0b:  # IX instructions
                self.ix_bit()

            else:
                self.ui(ui)

        elif major == 0x0e:
            if minor == 0x01:  # POP IX
                self._pop_ix()

            elif minor == 0x05:  # PUSH IX
                self._push_ix()

            elif minor == 0x09:  # JP (IX)
                self._jp_ix()

            else:
                self.ui(ui)

        else:
            self.ui(ui)

    def ix_bit(self):
        instr = self.read_pc_inc()

        ui = (0xddcb << 8) | instr

        major = instr >> 4
        minor = instr & 15
        minor1 = instr & 8
        minor2 = instr & 7

        if major == 0x00:
            self.ui(ui)

        else:
            self.ui(ui)

    def _ed(self):
        instr = self.read_pc_inc()

        ui = (0xed << 8) | instr

        major = instr >> 4
        minor = instr & 15
        minor1 = instr & 8
        minor2 = instr & 7

        if instr == 0xb0:
            self._ldir()

        elif minor == 0 and major >= 4 and major <= 6:
            self._in_ed_low(major - 4)

        elif minor == 2 and major >= 4 and major <= 7:
            self._sbc16(major - 4)

        elif minor == 5 and major >= 4 and major <= 7:
            self._neg()

        elif minor == 8 and major >= 4 and major <= 7:
            self._in_ed_high(major - 4)

        elif instr == 0x71 or instr == 0x61 or instr == 0x51 or instr == 0x41:
            self._out_c_low(major - 4)

        elif instr == 0x43:
            a = self.read_pc_inc_16()
            self.write_mem_16(a, self.m16(self.b, self.c))
            self.debug('LD (0x%04x), BC' % a)

        elif instr == 0x53:
            a = self.read_pc_inc_16()
            self.write_mem_16(a, self.m16(self.d, self.h))
            self.debug('LD (0x%04x), DE' % a)

        elif instr == 0x5b:
            a = self.read_pc_inc_16()
            v = self.read_mem_16(a)
            (self.d, self.e) = self.u16(v)
            self.debug('LD DE,(0x%04x) [%04x]' % (a, v))

        elif instr == 0x73:
            a = self.read_pc_inc_16()
            self.write_mem_16(a, self.sp)
            self.debug('LD (0x%04x), SP' % a)

        elif instr == 0x79 or instr == 0x69 or instr == 0x59 or instr == 0x49:
            self._out_c_high(major - 4)

        elif instr == 0x7b:
            a = self.read_pc_inc_16()
            v = self.read_mem_16(a)
            self.sp = v

        elif instr == 0xa0:
            self._ldi()

        elif instr == 0xa3:
            self._outi()

        elif instr == 0xb1:
            self._cpir()

        elif instr == 0xb9:
            self._cpdr()

        elif minor == 6:
            self._im(major & 1)

        else:
            self.ui(ui)

    def _in(self):
        a = self.read_pc_inc()
        self.a = self.in_(a)
        self.debug('IN A, (0x%02x) [%02x]' % (a, self.a))

    def _ld_sp_hl(self):
        self.sp = self.m16(self.h, self.l)
        self.debug('LD SP, HL [%04x]' % self.sp)

    def _add_a_val(self, use_c):
        v = self.read_pc_inc()
        old_val = self.a
        self.a += v

        if use_c:
            self.a += self.get_flag_c()

        self.set_add_flags(old_val, v, self.a)

        self.a &= 0xff
        self.debug('ADD A, 0x%02d [%02x]' % (v, self.a))

    def _ld_pair_from_a(self, which):
        if which == 0:  # (BC) = a
            self.write_mem(self.m16(self.b, self.c), self.a)
            self.debug('LD (BC),A')
        elif which == 1:
            self.write_mem(self.m16(self.d, self.e), self.a)
            self.debug('LD (DE),A')
        else:
            assert False

    def _ld_imem_from(self, which):
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

    def _rlca(self):
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

    def _rla(self):
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

    def _rlc(self, src):
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

    def _cp_mem(self):
        val = self.read_pc_inc()

        temp = self.a - val
        self.set_sub_flags(self.a, val, temp)

        self.debug('CP 0x%02x' % val)

    def _ldir(self):
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

    def _rr(self, src):
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

    def _rl(self, src):
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

    def _im(self, which):
        self.im = which

        self.debug('IM %d' % which)

    def _ret_always(self):
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

    def _scf(self):
        self.set_flag_c(True)
        self.set_flag_n(False)
        self.set_flag_h(False)

    def _jp_ix(self):
        self.pc = self.ix

        self.debug('JP (IX)')

    def _ex_sp_hl(self):
        hl = self.m16(self.h, self.l)
        org_sp_deref = self.read_mem_16(self.sp)
        self.write_mem_16(self.sp, hl)

        (self.h, self.l) = self.u16(org_sp_deref)

        self.debug('EX (SP),HL')

    def _rrca(self):
        self.set_flag_n(False)
        self.set_flag_h(False)

        bit0 = self.a & 1
        self.a >>= 1
        self.a |= bit0 << 7

        self.set_flag_c(bit0 == 1)

        self.debug('RRCA')

    def _di(self):
        self.interrupts = False
        self.debug('DI')

    def _ei(self):
        self.interrupts = True
        self.debug('EI')

    def _ccf(self):
        self.set_flag_c(not self.get_flag_c())
        self.set_flag_n(False)
        self.set_flag_h(False)

        self.debug('CCF')

    def _bit(self, nr, src):
        (val, src_name) = self.get_src(src)

        self.set_flag_n(False)
        self.set_flag_h(True)

        self.set_flag_z((val & (1 << nr)) != 0)

        self.debug('BIT %d, %s' % (nr, src_name))

    def _srl(self, src):
        (val, src_name) = self.get_src(src)

        self.set_flag_n(False)
        self.set_flag_h(False)
        self.set_flag_c((val & 1) == 1)
        self.set_flag_pv(self.parity(val))
        self.set_flag_z(val == 0)
        self.set_flag_s(val >= 128)

        val >>= 1

        dst = src
        self.set_dst(dst, val)

        self.debug('SRL %s' % src_name)

    def _set(self, bit, src):
        (val, src_name) = self.get_src(src)

        val |= 1 << bit

        dst = src
        self.set_dst(dst, val)

        self.debug('SET %d, %s' % (bit, src_name))

    def _res(self, bit, src):
        (val, src_name) = self.get_src(src)

        val &= ~(1 << bit)

        dst = src
        self.set_dst(dst, val)

        self.debug('RES %d, %s' % (bit, src_name))

    def _sbc16(self, which):
        (v, name) = self.get_pair(which)

        before = self.m16(self.h, self.l)
        value = v + self.get_flag_c()
        after = before - value

        self.set_flag_c((after & 0x10000) == 0x10000)
        self.set_flag_z((after & 0xffff) == 0)
        self.set_flag_n(True)
        self.set_flag_s((after & 0x8000) == 0x8000)

        before = self.compl16(before)
        value = self.compl16(value)
        after = self.compl16(after & 0xffff)
        self.set_flag_pv((before >= 0 and value >= 0 and after < 0) or (before < 0 and value < 0 and after >= 0))
 
        self.set_pair(2, after & 0xffff)

        self.debug('SUB HL,%s' % name)

    def _neg(self):
        org_a = self.compl8(self.a)
        a = -org_a

        self.set_sub_flags(org_a, 0, a)

        self.a = a & 0xff

        self.debug('NEG')

    def _ld_ix(self):
        v = self.read_pc_inc_16()
        self.ix = v

        self.debug('LD ix,**')

    def _ld_iy(self):
        v = self.read_pc_inc_16()
        self.iy = v

        self.debug('LD iy,**')

    def _ld_ix_im(self):
        offset = self.read_pc_inc()

        a = (self.ix + offset) & 0xffff

        self.a = self.read_mem(a)

        self.debug('LD A,(IX + *)')

    def _inc_ix(self):
        self.ix = (self.ix + 1) & 0xffff

        self.debug('INC IX')

    def _out_c_low(self, which):
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

    def _out_c_high(self, which):
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

    def _ld_a_iy(self):
        offset = self.read_pc_inc()

        a = (self.iy + offset) & 0xffff

        self.a = self.read_mem(a)

        self.debug('LD A,(IY + *)')

    def _ld_d_iy(self):
        offset = self.read_pc_inc()

        a = (self.iy + offset) & 0xffff

        self.d = self.read_mem(a)

        self.debug('LD D,(IY + *)')

    def _ld_e_iy(self):
        offset = self.read_pc_inc()

        a = (self.iy + offset) & 0xffff

        self.e = self.read_mem(a)

        self.debug('LD E,(IY + *)')

    def _in_ed_low(self, which):
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

    def _in_ed_high(self, which):
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

    def _outi(self):
        a = self.m16(self.h, self.l)
        self.out(self.c, self.read_mem(a))

        a += 1
        a &= 0xffff

        (self.h, self.l) = self.u16(a)

        self.b -= 1
        self.b &= 0xff

        self.debug('OUTI')

    def _ld_ix_X(self, which):
        offset = self.read_pc_inc()
        a = (self.ix + offset) & 0xffff

        (val, src_name) = self.get_src(which)
        self.write_mem(a, val)

        self.debug('LD (IX + *),%s' % src_name)

    def _ldi(self):
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

    def _cpdr(self):
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

    def _cpir(self):
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

    def _cp_im_ix(self):
        offset = self.read_pc_inc()
        a = (self.ix + offset) & 0xffff

        v  = self.read_mem(a)

        temp = self.a - v
        self.set_sub_flags(self.a, v, temp)

        self.debug('CP (IX + *)')

    def _and_a_ix_deref(self):
        offset = self.read_pc_inc()
        a = (self.ix + offset) & 0xffff

        v = self.read_mem(a)
 
        result = self.a & v

        self.set_add_flags(self.a, v, result)

        self.a = result & 0xff

        self.debug('AND (IX+*)')

    def _ld_X_ix_deref(self, which):
        offset = self.read_pc_inc()
        a = (self.ix + offset) & 0xffff

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
 
        elif which == 0x76:
            self.a = v
            name = 'A'

        self.debug('LD %s,(IX+*)' % name)
