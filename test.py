#! /usr/bin/python3

import sys
from inspect import getframeinfo, stack
from z80 import z80

io = [ 0 ] * 256

ram0 = [ 0 ] * 16384

slots = [ ] # slots
slots.append(( ram0, None, None, None ))
slots.append(( None, None, None, None ))
slots.append(( None, None, None, None ))
slots.append(( None, None, None, None ))

pages = [ 0, 0, 0, 0]

def reset_mem():
    ram0 = [ 0 ] * 16384

def read_mem(a):
    page = a >> 14

    if slots[page][pages[page]] == None:
        return 0xee

    return slots[page][pages[page]][a & 0x3fff]

def write_mem(a, v):
    global subpage

    my_assert(v >= 0 and v <= 255)

    page = a >> 14

    if slots[page][pages[page]] == None:
        my_assert(False)

    slots[page][pages[page]][a & 0x3fff] = v

def read_io(a):
    return io[a]
 
def write_io(a, v):
    io[a] = v

def debug(x):
    pass

def my_assert(r):
    if not r:
        print(cpu.reg_str())
        caller = getframeinfo(stack()[1][0])
        flags = ''
        for i in range(0, 8):
            if i == (7 - 5) or i == (7 - 3):
                flags += 'x'
            elif cpu.f & (128 >> i):
                flags += '1'
            else:
                flags += '0'
        print(flags)
        print('%s:%d' % (caller.filename, caller.lineno))
        sys.exit(1)

def test_ld():
    # LD C,L
    reset_mem()
    cpu.reset()
    cpu.c = 123
    cpu.l = 4
    cpu.a = 0
    cpu.f = 0
    ram0[0] = 0x4d
    cpu.step()
    my_assert(cpu.c == 4)
    my_assert(cpu.l == 4)
    my_assert(cpu.a == 0)
    my_assert(cpu.f == 0)
    my_assert(cpu.pc == 1)

    # LD A,*
    reset_mem()
    cpu.reset()
    cpu.a = 123
    cpu.f = 0
    ram0[0] = 0x3e
    ram0[1] = 0xff
    cpu.step()
    my_assert(cpu.a == 0xff)
    my_assert(cpu.f == 0)
    my_assert(cpu.pc == 2)

    # LD (HL),*
    reset_mem()
    cpu.reset()
    cpu.f = 0
    ram0[0] = 0x21 # LD HL,0101
    ram0[1] = 0x01
    ram0[2] = 0x01
    ram0[3] = 0x36 # LD (HL),*
    ram0[4] = 0xff
    cpu.step()
    cpu.step()
    my_assert(cpu.a == 0xff)
    my_assert(cpu.f == 0)
    my_assert(cpu.pc == 5)
    my_assert(cpu.read_mem(0x0101) == 0xff)

    # LD HL,**
    reset_mem()
    cpu.reset()
    cpu.f = 0
    ram0[0] = 0x21
    ram0[1] = 0xff
    ram0[2] = 0x12
    cpu.step()
    my_assert(cpu.f == 0)
    my_assert(cpu.h == 0x12)
    my_assert(cpu.l == 0xff)
    my_assert(cpu.pc == 3)

def test_jp():
    # JP **
    reset_mem()
    cpu.reset()
    cpu.f = 0
    ram0[0] = 0xc3
    ram0[1] = 0x10
    ram0[2] = 0x22
    cpu.step()
    my_assert(cpu.f == 0)
    my_assert(cpu.pc == 0x2210)
    my_assert(cpu.sp == 0xffff)

    # JP Z,** taken
    reset_mem()
    cpu.reset()
    cpu.f = 64
    ram0[0] = 0xca
    ram0[1] = 0x10
    ram0[2] = 0x22
    cpu.step()
    my_assert(cpu.f == 64)
    my_assert(cpu.pc == 0x2210)
    my_assert(cpu.sp == 0xffff)

    # JP Z,** not taken
    reset_mem()
    cpu.reset()
    cpu.f = 0
    ram0[0] = 0xca
    ram0[1] = 0x10
    ram0[2] = 0x22
    cpu.step()
    my_assert(cpu.f == 0)
    my_assert(cpu.pc == 3)
    my_assert(cpu.sp == 0xffff)

    # JP M,** taken
    reset_mem()
    cpu.reset()
    cpu.f = 128
    ram0[0] = 0xfa
    ram0[1] = 0x10
    ram0[2] = 0x22
    cpu.step()
    my_assert(cpu.f == 128)
    my_assert(cpu.pc == 0x2210)
    my_assert(cpu.sp == 0xffff)

def test_call_ret():
    # CALL **
    reset_mem()
    cpu.reset()
    cpu.f = 0
    cpu.sp = 0x3fff
    ram0[0] = 0xcd
    ram0[1] = 0x10
    ram0[2] = 0x22
    ram0[0x2210] = 0xc9
    cpu.step()
    my_assert(cpu.f == 0)
    my_assert(cpu.pc == 0x2210)
    my_assert(cpu.sp == 0x3ffd)
    cpu.step()
    my_assert(cpu.f == 0)
    my_assert(cpu.pc == 3)
    my_assert(cpu.sp == 0x3fff)

    # CALL Z,** taken
    reset_mem()
    cpu.reset()
    cpu.f = 64
    cpu.sp = 0x3fff
    ram0[0] = 0xcc
    ram0[1] = 0x10
    ram0[2] = 0x22
    ram0[0x2210] = 0xc9
    cpu.step()
    my_assert(cpu.f == 64)
    my_assert(cpu.pc == 0x2210)
    my_assert(cpu.sp == 0x3ffd)
    cpu.step()
    my_assert(cpu.f == 64)
    my_assert(cpu.pc == 3)
    my_assert(cpu.sp == 0x3fff)

    # CALL Z,** not taken
    reset_mem()
    cpu.reset()
    cpu.f = 0
    cpu.sp = 0x3fff
    ram0[0] = 0xcc
    ram0[1] = 0x10
    ram0[2] = 0x22
    ram0[0x2210] = 0xc9
    cpu.step()
    my_assert(cpu.f == 0)
    my_assert(cpu.pc == 3)
    my_assert(cpu.sp == 0x3fff)
    
    # RET C taken
    reset_mem()
    cpu.reset()
    cpu.f = 1
    cpu.sp = 0x3fff
    ram0[0] = 0xcd
    ram0[1] = 0x10
    ram0[2] = 0x22
    ram0[0x2210] = 0xd8
    cpu.step()
    my_assert(cpu.f == 1)
    my_assert(cpu.pc == 0x2210)
    my_assert(cpu.sp == 0x3ffd)
    cpu.step()
    my_assert(cpu.f == 1)
    my_assert(cpu.pc == 3)
    my_assert(cpu.sp == 0x3fff)
    
    # RET C not taken
    reset_mem()
    cpu.reset()
    cpu.f = 0
    cpu.sp = 0x3fff
    ram0[0] = 0xcd
    ram0[1] = 0x10
    ram0[2] = 0x22
    ram0[0x2210] = 0xd8
    cpu.step()
    my_assert(cpu.f == 0)
    my_assert(cpu.pc == 0x2210)
    my_assert(cpu.sp == 0x3ffd)
    cpu.step()
    my_assert(cpu.f == 0)
    my_assert(cpu.pc == 0x2211)
    my_assert(cpu.sp == 0x3ffd)

def test_cpl():
    # CPL
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.f = 0
    ram0[0] = 0x2f
    cpu.step()
    my_assert(cpu.a == 0x0f)
    my_assert(cpu.f == 18)
    my_assert(cpu.pc == 1)

def test__flags():
    # CPL
    reset_mem()
    cpu.reset()

    cpu.f = 0xff
    my_assert(cpu.get_flag_c())
    my_assert(cpu.get_flag_n())
    my_assert(cpu.get_flag_pv())
    my_assert(cpu.get_flag_h())
    my_assert(cpu.get_flag_z())
    my_assert(cpu.get_flag_s())

    cpu.f = 0
    cpu.a = 12
    cpu.set_flag_parity()
    my_assert(cpu.f == 4)
    cpu.a = 13
    cpu.set_flag_parity()
    my_assert(cpu.f == 0)

    cpu.f = 0x00
    my_assert(not cpu.get_flag_c())
    my_assert(not cpu.get_flag_n())
    my_assert(not cpu.get_flag_pv())
    my_assert(not cpu.get_flag_h())
    my_assert(not cpu.get_flag_z())
    my_assert(not cpu.get_flag_s())

    cpu.set_flag_c(True)
    my_assert(cpu.f == 1)
    my_assert(cpu.get_flag_c())
    cpu.set_flag_n(True)
    my_assert(cpu.f == 3)
    my_assert(cpu.get_flag_n())
    cpu.set_flag_pv(True)
    my_assert(cpu.f == 7)
    my_assert(cpu.get_flag_pv())
    cpu.set_flag_h(True)
    my_assert(cpu.f == 23)
    my_assert(cpu.get_flag_h())
    cpu.set_flag_z(True)
    my_assert(cpu.f == 87)
    my_assert(cpu.get_flag_z())
    cpu.set_flag_s(True)
    my_assert(cpu.f == 215)
    my_assert(cpu.get_flag_s())
    cpu.set_flag_s(True)

def _test_registers_initial(incl_pc):
    my_assert(cpu.a == 0xff)
    my_assert(cpu.b == 0xff)
    my_assert(cpu.c == 0xff)
    my_assert(cpu.d == 0xff)
    my_assert(cpu.e == 0xff)
    my_assert(cpu.f == 0xff)
    my_assert(cpu.h == 0xff)
    my_assert(cpu.l == 0xff)
    my_assert(cpu.a_ == 0xff)
    my_assert(cpu.b_ == 0xff)
    my_assert(cpu.c_ == 0xff)
    my_assert(cpu.d_ == 0xff)
    my_assert(cpu.e_ == 0xff)
    my_assert(cpu.f_ == 0xff)
    my_assert(cpu.h_ == 0xff)
    my_assert(cpu.l_ == 0xff)
    my_assert(cpu.ix == 0xffff)
    my_assert(cpu.iy == 0xffff)
    my_assert(cpu.interrupts)
    my_assert(cpu.pc == 0x0000 or not incl_pc)
    my_assert(cpu.sp == 0xffff)
    my_assert(cpu.im == 0)

def test__support():
    my_assert(cpu.parity(0) == True)
    my_assert(cpu.parity(127) == False)
    my_assert(cpu.parity(128) == False)
    my_assert(cpu.parity(129) == True)
    my_assert(cpu.parity(255) == True)

    cpu.a = cpu.b = cpu.c = cpu.d = cpu.e = cpu.f = cpu.h = cpu.l = 0x12
    cpu.a_ = cpu.b_ = cpu.c_ = cpu.d_ = cpu.e_ = cpu.f_ = cpu.h_ = cpu.l_ = 0x34
    cpu.ix = cpu.iy = 0x1234
    cpu.interrupts = False
    cpu.pc = 0x4321
    cpu.sp = 0xee55
    cpu.im = 2
    cpu.reset()
    _test_registers_initial(True)

    cpu.out(0xa8, 123)
    my_assert(io[0xa8] == 123)
    my_assert(cpu.in_(0xa8) == 123)
    my_assert(cpu.in_(0xa7) == 0x00)

    cpu.reset()
    ram0[0x0000] = 0x56
    my_assert(cpu.read_pc_inc() == 0x56)
    my_assert(cpu.pc == 0x0001)
    ram0[0x0001] = 0x12
    ram0[0x0002] = 0x34
    my_assert(cpu.read_pc_inc_16() == 0x3412)
    my_assert(cpu.pc == 0x0003)

    my_assert(cpu.m16(0x34, 0x12) == 0x3412)

    cpu.set_dst(0, 0x10)
    my_assert(cpu.b == 0x10)
    my_assert(cpu.get_src(0) == (0x10, 'B'))
    cpu.set_dst(1, 0x19)
    my_assert(cpu.c == 0x19)
    my_assert(cpu.get_src(1) == (0x19, 'C'))
    cpu.set_dst(2, 0x39)
    my_assert(cpu.d == 0x39)
    my_assert(cpu.get_src(2) == (0x39, 'D'))
    cpu.set_dst(3, 0x49)
    my_assert(cpu.e == 0x49)
    my_assert(cpu.get_src(3) == (0x49, 'E'))
    cpu.set_dst(4, 0x12)
    my_assert(cpu.h == 0x12)
    my_assert(cpu.get_src(4) == (0x12, 'H'))
    cpu.set_dst(5, 0x13)
    my_assert(cpu.l == 0x13)
    my_assert(cpu.get_src(5) == (0x13, 'L'))
    ram0[0x1213] = 0x34
    my_assert(cpu.get_src(6) == (0x34, '(HL)'))
    cpu.set_dst(7, 0x99)
    my_assert(cpu.a == 0x99)
    my_assert(cpu.get_src(7) == (0x99, 'A'))

    my_assert(cpu.get_pair(0) == (0x1019, 'BC'))
    my_assert(cpu.get_pair(1) == (0x3949, 'DE'))
    my_assert(cpu.get_pair(2) == (0x1213, 'HL'))
    my_assert(cpu.get_pair(3) == (0xffff, 'SP'))

    my_assert(cpu.set_pair(0, 0x7723) == 'BC')
    my_assert(cpu.b == 0x77)
    my_assert(cpu.c == 0x23)
    my_assert(cpu.set_pair(1, 0x4422) == 'DE')
    my_assert(cpu.d == 0x44)
    my_assert(cpu.e == 0x22)
    my_assert(cpu.set_pair(2, 0xBCDE) == 'HL')
    my_assert(cpu.h == 0xBC)
    my_assert(cpu.l == 0xDE)
    my_assert(cpu.set_pair(3, 0x1133) == 'SP')
    my_assert(cpu.sp == 0x1133)

    reset_mem()
    cpu.write_mem_16(0x0103, 0x1934)
    my_assert(ram0[0x0103] == 0x34)
    my_assert(ram0[0x0104] == 0x19)
    my_assert(cpu.read_mem_16(0x0103) == 0x1934)

    reset_mem()
    cpu.reset()
    cpu.f = 0x00
    cpu.set_dst(5, 0x12)
    my_assert(cpu.l == 0x12)
    my_assert(cpu.get_src(5) == (0x12, 'L'))
    cpu.set_dst(4, 0x34)
    my_assert(cpu.h == 0x34)
    my_assert(cpu.get_src(4) == (0x34, 'H'))
    cpu.set_dst(7, 0x55)
    my_assert(cpu.a == 0x55)
    my_assert(cpu.get_src(7) == (0x55, 'A'))
    my_assert(cpu.f == 0x00)
    cpu.set_dst(6, 0xa9)
    my_assert(ram0[0x3412] == 0xa9)
    my_assert(cpu.get_src(6) == (0xa9, '(HL)'))

    reset_mem()
    cpu.reset()
    cpu.sp = 0x3fff
    cpu.push(0x1020)
    cpu.ret_flag(False)
    my_assert(cpu.pc == 0x0000)

    cpu.reset()
    cpu.sp = 0x3fff
    cpu.push(0x1122)
    cpu.ret_flag(True)
    my_assert(cpu.pc == 0x1122)

    # SUB flags
    cpu.reset()
    cpu.f = 0
    cpu.set_sub_flags(0xf0, 0x21, 0xf0 - 0x21)
    my_assert(cpu.f == (0xb2 & 0xd7))

    cpu.f = 0
    cpu.set_sub_flags(0xf0, 0xf0, 0)
    my_assert(cpu.f == (0x62 & 0xd7))

    cpu.f = 0
    cpu.set_sub_flags(0x01, 0xa0, 0x01 - 0xa0)
    my_assert(cpu.f == (0x23 & 0xd7))

    # ADD flags
    cpu.reset()
    cpu.f = 0
    cpu.set_add_flags(0xf0, 0x21, 0xf0 + 0x21)
    my_assert(cpu.f == (0x01 & 0xd7))

    cpu.f = 0
    cpu.set_add_flags(0xf0, 0xf0, 0xf0 + 0xf0)
    my_assert(cpu.f == (0x81 & 0xd7))

    cpu.f = 0
    cpu.set_add_flags(0x01, 0xa0, 0x01 + 0xa0)
    my_assert(cpu.f == (0x80 & 0xd7))

    cpu.f = 0
    cpu.set_add_flags(0xa0, 0xa0, 0xa0 + 0xa0)
    my_assert(cpu.f == (0x05 & 0xd7))

def test_nop():
    cpu.reset()
    ram0[0] = 0x00
    cpu.step()
    _test_registers_initial(False)

def test_cp():
    # CP B
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.b = 0x21 # 
    cpu.f = 0
    ram0[0] = 0xb8
    cpu.step()
    my_assert(cpu.a == 0xf0)
    # 04
    my_assert(cpu.f == (0xb2 & 0xd7))
    my_assert(cpu.pc == 1)

    cpu.reset()
    cpu.a = 0xf0
    cpu.b = 0xf0 # zero flag
    cpu.f = 0
    cpu.step()
    my_assert(cpu.a == 0xf0)
    my_assert(cpu.f == (0x62 & 0xd7))

    cpu.reset()
    cpu.a = 0x01
    cpu.b = 0xa0 # overflow flag
    cpu.f = 0
    cpu.step()
    my_assert(cpu.a == 0x01)
    my_assert(cpu.f == (0x23 & 0xd7))

def test_add():
    # ADD B
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.b = 0x21 # 
    cpu.f = 0
    ram0[0] = 0x80
    cpu.step()
    my_assert(cpu.a == 0x11)
    my_assert(cpu.f == (0x01 & 0xd7))
    my_assert(cpu.pc == 1)

    # ADC B
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.b = 0x21 # 
    cpu.f = 0
    ram0[0] = 0x37
    cpu.step()
    assert(cpu.get_flag_c())
    ram0[1] = 0x88
    cpu.step()
    my_assert(cpu.a == 0x12)
    my_assert(cpu.f == (0x01 & 0xd7))
    my_assert(cpu.pc == 2)

    # ADD HL,BC
    reset_mem()
    cpu.reset()
    cpu.h = 0xf0
    cpu.l = 0x21
    cpu.b = 0x03
    cpu.c = 0x57
    cpu.f = 0
    ram0[0] = 0x09
    cpu.step()
    my_assert(cpu.h == 0xf3)
    my_assert(cpu.l == 0x78)
    my_assert(cpu.f == (0x00 & 0xd7))
    my_assert(cpu.pc == 1)

def test_or():
    # OR B
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.b = 0x21 # 
    cpu.f = 0
    ram0[0] = 0xb0
    cpu.step()
    my_assert(cpu.a == 0xf1)
    my_assert(cpu.f == (0x80 & 0xd7))
    my_assert(cpu.pc == 1)

    # OR *
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.f = 0
    ram0[0] = 0xf6
    ram0[1] = 0x21
    cpu.step()
    my_assert(cpu.a == 0xf1)
    my_assert(cpu.f == (0x80 & 0xd7))
    my_assert(cpu.pc == 2)

def test_and():
    # AND B
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.b = 0x21 # 
    cpu.f = 0
    ram0[0] = 0xa0
    cpu.step()
    my_assert(cpu.a == 0x20)
    my_assert(cpu.f == (0x10 & 0xd7))
    my_assert(cpu.pc == 1)

    # AND *
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.f = 0
    ram0[0] = 0xe6
    ram0[1] = 0x21
    cpu.step()
    my_assert(cpu.a == 0x20)
    my_assert(cpu.f == (0x10 & 0xd7))
    my_assert(cpu.pc == 2)

def test_xor():
    # XOR B
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.b = 0x21
    cpu.f = 0
    ram0[0] = 0xa8
    cpu.step()
    my_assert(cpu.a == 0xd1)
    my_assert(cpu.f == (0x84 & 0xd7))
    my_assert(cpu.pc == 1)

    # XOR *
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.b = 0x00
    cpu.f = 0
    ram0[0] = 0xee
    ram0[1] = 0x21
    cpu.step()
    my_assert(cpu.a == 0xd1)
    my_assert(cpu.f == (0x84 & 0xd7))
    my_assert(cpu.pc == 2)

def test_out_in():
    # OUT (*),A
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.f = 0
    ram0[0] = 0xd3
    ram0[1] = 0x00
    cpu.step()
    my_assert(cpu.a == 0xf0)
    my_assert(cpu.f == 0x00)
    my_assert(cpu.pc == 2)
    my_assert(io[0x00] == 0xf0)

    # IN A,(*)
    cpu.pc = 0x0000
    cpu.a = 123
    ram0[0] = 0xdb
    ram0[1] = 0x00
    cpu.step()
    my_assert(cpu.a == 0xf0)
    my_assert(cpu.f == 0x00)
    my_assert(cpu.pc == 2)
    my_assert(io[0x00] == 0xf0)

def test_sla():
    # SLA B
    reset_mem()
    cpu.reset()
    cpu.b = 0x21
    cpu.f = 0
    ram0[0] = 0xcb
    ram0[1] = 0x20
    cpu.step()
    my_assert(cpu.a == 0xff)
    my_assert(cpu.b == 0x42)
    my_assert(cpu.f == 0x04)
    my_assert(cpu.pc == 2)

def test_push_pop():
    reset_mem()
    cpu.reset()
    cpu.b = 0x12
    cpu.c = 0x34
    cpu.sp = 0x3fff
    cpu._push(0) # 0xc0 PUSH BC
    my_assert(cpu.sp == 0x3ffd)
    my_assert(cpu.read_mem_16(0x3ffd) == 0x1234)
    cpu.a = 0xaa
    cpu.f = 0xbb
    cpu._push(3) # 0xf0 PUSH AF
    cpu._push(1) # 0xc0 PUSH DE => 0xffff

    cpu._pop(3)
    my_assert(cpu.a == 0xff)
    my_assert(cpu.f == 0xff)
    cpu._pop(0)
    my_assert(cpu.b == 0xaa)
    my_assert(cpu.c == 0xbb)
    cpu.d = 0x50
    cpu.e = 0x50
    cpu._pop(1)
    my_assert(cpu.d == 0x12)
    my_assert(cpu.e == 0x34)

def test_jr():
    # JR -2
    reset_mem()
    cpu.reset()
    cpu.f = 0
    ram0[0] = 0x18
    ram0[1] = 0xfe
    cpu.step()
    my_assert(cpu.f == 0x00)
    my_assert(cpu.pc == 0)

    # JR NZ,-2
    reset_mem()
    cpu.reset()
    cpu.f = 64
    ram0[0] = 0x20
    ram0[1] = 0xfe
    cpu.step()
    my_assert(cpu.f == 64)
    my_assert(cpu.pc == 2)

def test_djnz():
    # DJNZ -2 not taken
    reset_mem()
    cpu.reset()
    cpu.b = 1
    cpu.f = 0
    ram0[0] = 0x10
    ram0[1] = 0xfe
    cpu.step()
    my_assert(cpu.f == 0x00)
    my_assert(cpu.pc == 2)

    # DJNZ,-2 taken
    reset_mem()
    cpu.reset()
    cpu.b == 2
    cpu.f = 0
    ram0[0] = 0x10
    ram0[1] = 0xfe
    cpu.step()
    my_assert(cpu.f == 0x00)
    my_assert(cpu.pc == 0)

def test_sub():
    # SUB B
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.b = 0x21
    cpu.f = 0
    ram0[0] = 0x90
    cpu.step()
    my_assert(cpu.a == 0xf0 - 0x21)
    my_assert(cpu.f == (0xb2 & 0xd7))
    my_assert(cpu.pc == 1)

    # SBC B
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.b = 0x21
    cpu.f = 1
    ram0[0] = 0x98
    cpu.step()
    my_assert(cpu.a == 0xf0 - 0x21 - 1)
    my_assert(cpu.f == (0xb2 & 0xd7))
    my_assert(cpu.pc == 1)

    # SUB *
    reset_mem()
    cpu.reset()
    cpu.a = 0xf0
    cpu.f = 0
    ram0[0] = 0xd6
    ram0[1] = 0x21
    cpu.step()
    my_assert(cpu.a == 0xf0 - 0x21)
    my_assert(cpu.f == (0xb2 & 0xd7))
    my_assert(cpu.pc == 2)

def test_inc():
    # INC b
    reset_mem()
    cpu.reset()
    cpu.b = 0xff
    cpu.f = 1
    ram0[0] = 0x04
    cpu.step()
    my_assert(cpu.b == 0x00)
    my_assert(cpu.f == (0x51 & 0xd7))
    my_assert(cpu.pc == 1)

    # INC de
    reset_mem()
    cpu.reset()
    cpu.d = 0x22
    cpu.e = 0x33
    cpu.f = 123
    ram0[0] = 0x13
    cpu.step()
    my_assert(cpu.d == 0x22)
    my_assert(cpu.e == 0x34)
    my_assert(cpu.f == 123)
    my_assert(cpu.pc == 1)

    # INC hl
    reset_mem()
    cpu.reset()
    cpu.h = 0x22
    cpu.l = 0x33
    cpu.f = 0
    ram0[0] = 0x34
    ram0[0x2233] = 0xff
    cpu.step()
    my_assert(cpu.h == 0x22)
    my_assert(cpu.l == 0x33)
    my_assert(cpu.pc == 1)
    my_assert(cpu.read_mem(0x2233) == 0x00)
    my_assert(cpu.f == (0x50 & 0xd7))

def test_dec():
    # DEC b
    reset_mem()
    cpu.reset()
    cpu.b = 0x80
    cpu.f = 1
    ram0[0] = 0x05
    cpu.step()
    my_assert(cpu.b == 0x7f)
    my_assert(cpu.f == (0x17 & 0xd7))
    my_assert(cpu.pc == 1)

    # DEC de
    reset_mem()
    cpu.reset()
    cpu.d = 0x22
    cpu.e = 0x33
    cpu.f = 123
    ram0[0] = 0x1b
    cpu.step()
    my_assert(cpu.d == 0x22)
    my_assert(cpu.e == 0x32)
    my_assert(cpu.f == 123)
    my_assert(cpu.pc == 1)

def test_rlca_rlc():
    # RLCA
    reset_mem()
    cpu.reset()
    cpu.a = 0xe1
    cpu.f = 0
    ram0[0] = 0x07
    cpu.step()
    my_assert(cpu.a == 0xc3)
    my_assert(cpu.f == (0x01 & 0xd7))
    my_assert(cpu.pc == 1)

    # RLC B
    reset_mem()
    cpu.reset()
    cpu.b = 0xe1
    cpu.f = 1
    ram0[0] = 0xcb
    ram0[1] = 0x00
    cpu.step()
    my_assert(cpu.b == 0xc3)
    my_assert(cpu.f == (0x85 & 0xd7))
    my_assert(cpu.pc == 2)

def test_di_ei():
    # DI
    reset_mem()
    cpu.reset()
    cpu.f = 0
    ram0[0] = 0xf3
    cpu.step()
    my_assert(cpu.f == 0)
    my_assert(cpu.pc == 1)
    my_assert(cpu.interrupts == False)

    # EI
    reset_mem()
    cpu.reset()
    cpu.f = 0
    ram0[0] = 0xfb
    cpu.step()
    my_assert(cpu.f == 0)
    my_assert(cpu.pc == 1)
    my_assert(cpu.interrupts == True)

def test_ex():
    # EX DE,HL
    reset_mem()
    cpu.reset()
    cpu.d = 123
    cpu.e = 210
    cpu.h = 50
    cpu.l = 20
    cpu.f = 123
    ram0[0] = 0xeb
    cpu.step()
    my_assert(cpu.f == 123)
    my_assert(cpu.pc == 1)
    my_assert(cpu.d == 50)
    my_assert(cpu.e == 20)
    my_assert(cpu.h == 123)
    my_assert(cpu.l == 210)

    # EX (SP),HL
    reset_mem()
    cpu.reset()
    cpu.sp = 0x1000
    cpu.write_mem_16(0x1000, 0xffdd)
    cpu.h = 0x50
    cpu.l = 0x20
    cpu.f = 123
    ram0[0] = 0xe3
    cpu.step()
    my_assert(cpu.f == 123)
    my_assert(cpu.pc == 1)
    my_assert(cpu.h == 0xff)
    my_assert(cpu.l == 0xdd)
    my_assert(cpu.read_mem_16(0x1000) == 0x5020)

def test_rrca():
    # RRCA
    reset_mem()
    cpu.reset()
    cpu.a = 0xe1
    cpu.f = 0
    ram0[0] = 0x0f
    cpu.step()
    my_assert(cpu.a == 0xf0)
    my_assert(cpu.f == (0x01 & 0xd7))
    my_assert(cpu.pc == 1)

def test_rr():
    # RR
    reset_mem()
    cpu.reset()
    cpu.b = 0xe1
    cpu.f = 1
    ram0[0] = 0xcb
    ram0[1] = 0x18
    cpu.step()
    my_assert(cpu.pc == 2)
    my_assert(cpu.f == (0x85 & 0xd7))
    my_assert(cpu.b == 0xf0)

def test_rst():
    # RST
    reset_mem()
    cpu.reset()
    cpu.f = 123
    cpu.sp = 0x3fff
    ram0[0] = 0xd7
    cpu.step()
    my_assert(cpu.pc == 0x10)
    my_assert(cpu.f == 123)
    my_assert(cpu.sp == 0x3ffd)
    my_assert(cpu.read_mem_16(0x3ffd) == 0x001)

cpu = z80(read_mem, write_mem, read_io, write_io, debug)

test__flags()
test__support()
test_add()
test_and()
test_call_ret()
test_cp()
test_cpl()
test_dec()
test_di_ei()
test_djnz()
test_ex()
test_inc()
test_jp()
test_jr()
test_ld()
test_nop()
test_or()
test_out_in()
test_push_pop()
test_rlca_rlc()
test_rr()
test_rrca()
test_rst()
test_sla()
test_sub()
test_xor()

# FIXME negative relative jump

print('All fine')
