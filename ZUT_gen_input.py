#! /usr/bin/python3

# http://www.z80.info/decoding.htm

r = [ 'b', 'c', 'd', 'e', 'h', 'l', '(hl)', 'a' ]
rp = [ 'bc', 'de', 'hl', 'sp' ]
rp2 = [ 'bc', 'de', 'hl', 'af' ]
cc = [ 'nz', 'z', 'nc', 'c', 'po', 'pe', 'p', 'm' ]
alu = [ 'add a,', 'adc a,', 'sub', 'sbc a,', 'and', 'xor', 'or', 'cp' ]
rot = [ 'rlc', 'rrc', 'rl', 'rr', 'sla', 'sra', 'sll', 'srl' ]
im = [ '0', '0/1', '1', '2', '0', '0/1', '1', '2' ]
bli = [ None ] * 8
bli[4] = [ 'LDI', 'CPI', 'INI', 'OUTI' ]
bli[5] = [ 'LDD', 'CPD', 'IND', 'OUTD' ]
bli[4] = [ 'LDIR', 'CPIR', 'INIR', 'OTIR' ]
bli[5] = [ 'LDDR', 'CPDR', 'INDR', 'OTDR' ]

offset = 0

for i in range(0x00, 0x100):
    x = i >> 6
    y = (i >> 3) & 7
    z = i & 7
    p = y >> 1
    q = y & 1

    instr = None

    if x == 0:
        if z == 0:
            if y == 0:
                instr = 'NOP'
            elif y == 1:
                instr == "EX AF,AF'"
            elif y == 2:
                instr = 'DJNZ 0%02xh' % offset
            elif y == 3:
                instr = 'JR 0%02xh' % offset
            elif y >= 4 and y <= 7:
                instr = 'JR %s,0%02xh' % (cc[y - 4], offset)

    if instr:
        print(x, y, z, instr)
