# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import os
import signal
import struct
import sys
import threading
from vdp import vdp

class screen_kb:
    MSG_SET_IO = 0
    MSG_GET_IO = 1
    MSG_INTERRUPT = 2
    MSG_GET_REG = 3

    def __init__(self, io):
        self.stop_flag = False
        self.io = io

        self.keyboard_queue = []
        self.k_lock = threading.Lock()

        self.debug_msg_lock = threading.Lock()
        self.debug_msg = None

        self.init_screen()

        super(screen_kb, self).__init__()

    def init_screen(self):
        # pipes for data to the VDP
        self.pipe_tv_in, self.pipe_tv_out = os.pipe()       

        # pipes for data from the VDP
        self.pipe_fv_in, self.pipe_fv_out = os.pipe()       

        self.pid = os.fork()

        if self.pid == 0:
            self.vdp = vdp()
            self.vdp.start()
            
            while True:
                type_ = os.read(self.pipe_tv_in, 1)[0]

                if type_ == screen_kb.MSG_SET_IO:
                    data = os.read(self.pipe_tv_in, 2)
                    a = data[0]
                    v = data[1]

                    self.vdp.write_io(a, v)

                elif type_ == screen_kb.MSG_GET_IO:
                    a = os.read(self.pipe_tv_in, 1)[0]
                    v = self.vdp.read_io(a)

                    packet = ( screen_kb.MSG_GET_IO, a, v )
                    os.write(self.pipe_fv_out, bytearray(packet))

                elif type_ == screen_kb.MSG_INTERRUPT:
                    self.vdp.registers[2] |= 128

                elif type_ == screen_kb.MSG_GET_REG:
                    a = os.read(self.pipe_tv_in, 1)[0]

                    packet = ( screen_kb.MSG_GET_REG, self.vdp.registers[a] )
                    os.write(self.pipe_fv_out, bytearray(packet))

                else:
                    print('Unexpected message %d' % type_)

            sys.exit(1)

        print(self.pid)

        os.close(self.pipe_tv_in)
        os.close(self.pipe_fv_out)

    def interrupt(self):
        os.write(self.pipe_tv_out, screen_kb.MSG_INTERRUPT.to_bytes(1, 'big'))

    def IE0(self):
        reg = 1  # request VDP status register 1
        packet = [ screen_kb.MSG_GET_REG, reg ]
        os.write(self.pipe_tv_out, bytearray(packet))

        data = os.read(self.pipe_fv_in, 2)
        type_ = data[0]
        assert type_ == screen_kb.MSG_GET_REG
        v = data[1]

        return (v & 32) == 32

    def write_io(self, a, v):
        packet = ( screen_kb.MSG_SET_IO, a, v )
        os.write(self.pipe_tv_out, bytearray(packet))

    def read_io(self, a):
        if a in (0x98, 0x99, 0xa9):

            packet = ( screen_kb.MSG_GET_IO, a )
            os.write(self.pipe_tv_out, bytearray(packet))

            data = os.read(self.pipe_fv_in, 3)
            type_ = data[0]
            assert type_ == screen_kb.MSG_GET_IO

            a_ = data[1]
            assert a_ == a

            v = data[2]

            return v

        print('unexpected port %02x' % a)

        return 0x00

    def debug(self, str_):
        self.debug_msg_lock.acquire()
        self.debug_msg = str_
        self.debug_msg_lock.release()

    def stop(self):
        self.stop_flag = True
        os.kill(self.pid, signal.SIGKILL)
        os.wait()

        os.close(self.pipe_tv_out)
        os.close(self.pipe_fv_in)
