# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import curses
import math
import pygame
import sys
import threading
import time

from screen_kb import screen_kb

class screen_kb_pygame(screen_kb):
    def __init__(self, cpu, io):
        pygame.init()

        super(screen_kb_pygame, self).__init__(cpu, io)

    def init_kb(self):
        pass  # FIXME

    def rgb_to_i(self, r, g, b):
        return (r << 16) | (g << 8) | b

    def init_screen(self):
        # TMS9918 palette 
        self.rgb = [ self.rgb_to_i(0, 0, 0), self.rgb_to_i(0, 0, 0), self.rgb_to_i(33, 200, 66), self.rgb_to_i(94, 220, 120), self.rgb_to_i(84, 85, 237), self.rgb_to_i(125, 118, 252), self.rgb_to_i(212, 82, 77), self.rgb_to_i(66, 235, 245), self.rgb_to_i(252, 85, 84), self.rgb_to_i(255, 121, 120), self.rgb_to_i(212, 193, 84), self.rgb_to_i(231, 206, 128), self.rgb_to_i(33, 176, 59), self.rgb_to_i(201, 91, 186), self.rgb_to_i(204, 204, 204), self.rgb_to_i(255, 255, 255) ] 

        self.screen = pygame.display.set_mode((256, 192))
        self.surface = pygame.Surface((256, 192))
        self.arr = pygame.surfarray.array2d(self.screen)

    def stop2(self):
        pass

    def run(self):
        while not self.stop_flag:
            with self.cv:
                t = time.time()

                while self.redraw == False and self.stop_flag == False:
                    c = -1  # FIXME
                    events = pygame.event.get()
                    for event in events:
                        if event.type == pygame.QUIT:
                            self.stop_flag = True
                            break

                    if c != -1:
                        if c == 13 or c == 10:
                            print('MARKER', file=sys.stderr)

                        self.k_lock.acquire()
                        self.keyboard_queue.append(c)
                        self.k_lock.release()

                    self.cv.wait(0.02)

                    now = time.time()
                    if now - t >= 0.02:
                        self.cpu.interrupt()
                        self.registers[2] |= 128
                        t = now

                self.redraw = False

            msg = self.debug_msg[0:79]

            # redraw
            vm = self.video_mode()
            if vm == 1:  # 'screen 2' (256 x 192)
                bg_map    = (self.registers[2] &  15) << 10
                bg_colors = (self.registers[3] & 128) <<  6
                bg_tiles  = (self.registers[4] &   4) << 11

                s = time.time()

                par = pygame.PixelArray(self.surface)

                for map_index in range(0, 32 * 24):
                    cur_char_nr = self.ram[bg_map + map_index]
                    block_nr    = (map_index >> 8) & 3
                    cur_tiles   = bg_tiles  + (block_nr * 256 * 8) + (cur_char_nr * 8)
                    cur_colors  = bg_colors + (block_nr * 256 * 8) + (cur_char_nr * 8)
                    # offset in SDL window
                    scr_x = (map_index & 31) * 8;
                    scr_y = ((map_index >> 5) & 31) * 8;
                    end_x = scr_x + 8;

                    for y in range(7, -1, -1):
                        current_tile = self.ram[cur_tiles]
                        cur_tiles += 1

                        current_color = self.ram[cur_colors]
                        cur_colors += 1

                        fg = self.rgb[current_color >> 4]
                        bg = self.rgb[current_color & 15]

                        for x in range(scr_x, end_x):
                            self.arr[x, scr_y] = fg if (current_tile & 128) == 128 else bg
                            current_tile <<= 1

                        scr_y += 1

                pygame.surfarray.blit_array(self.screen, self.arr)
                pygame.display.flip()

                print('daar %f %f' % (s, time.time() - s))

            else:
                msg = 'Unsupported resolution'

            self.debug_msg_lock.acquire()
            if self.debug_msg:
                #self.win.addstr(25, 0, msg)
                pass  # FIXME
            self.debug_msg_lock.release()

    def get_keyboard(self):
        return 255  # FIXME
