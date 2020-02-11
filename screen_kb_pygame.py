# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

import math
import pygame
import sys
import threading
import time

from screen_kb import screen_kb

class screen_kb_pygame(screen_kb):
    def __init__(self, io):
        pygame.init()

        super(screen_kb_pygame, self).__init__(io)

    def rgb_to_i(self, r, g, b):
        return (r << 16) | (g << 8) | b

    def init_screen(self):
        # TMS9918 palette 
        self.rgb = [ self.rgb_to_i(0, 0, 0), self.rgb_to_i(0, 0, 0), self.rgb_to_i(33, 200, 66), self.rgb_to_i(94, 220, 120), self.rgb_to_i(84, 85, 237), self.rgb_to_i(125, 118, 252), self.rgb_to_i(212, 82, 77), self.rgb_to_i(66, 235, 245), self.rgb_to_i(252, 85, 84), self.rgb_to_i(255, 121, 120), self.rgb_to_i(212, 193, 84), self.rgb_to_i(231, 206, 128), self.rgb_to_i(33, 176, 59), self.rgb_to_i(201, 91, 186), self.rgb_to_i(204, 204, 204), self.rgb_to_i(255, 255, 255) ] 

        self.screen = pygame.display.set_mode((320, 192))
        self.surface = pygame.Surface((320, 192))
        self.arr = pygame.surfarray.array2d(self.screen)

    def stop2(self):
        pass

    def find_char_row(self, c):
        chars = { }

        chars[pygame.K_RIGHTPAREN] = ( 0, (1 << 0) ^ 0xff, True )
        chars[pygame.K_0] = ( 0, (1 << 0) ^ 0xff, False )
        chars[pygame.K_EXCLAIM] = ( 0, (1 << 1) ^ 0xff, True )
        chars[pygame.K_1] = ( 0, (1 << 1) ^ 0xff, False )
        chars[pygame.K_AT] = ( 0, (1 << 2) ^ 0xff, True )
        chars[pygame.K_2] = ( 0, (1 << 2) ^ 0xff, False )
        chars[pygame.K_HASH] = ( 0, (1 << 3) ^ 0xff, True )
        chars[pygame.K_3] = ( 0, (1 << 3) ^ 0xff, False )
        chars[pygame.K_DOLLAR] = ( 0, (1 << 4) ^ 0xff, True )
        chars[pygame.K_4] = ( 0, (1 << 4) ^ 0xff, False )
#        chars[pygame.K_PERCENT] = ( 0, (1 << 5) ^ 0xff, True )
        chars[pygame.K_5] = ( 0, (1 << 5) ^ 0xff, False )
        chars[pygame.K_CARET] = ( 0, (1 << 6) ^ 0xff, True )
        chars[pygame.K_6] = ( 0, (1 << 6) ^ 0xff, False )
        chars[pygame.K_AMPERSAND] = ( 0, (1 << 7) ^ 0xff, True )
        chars[pygame.K_7] = ( 0, (1 << 7) ^ 0xff, False )
        chars[pygame.K_KP_MULTIPLY] = ( 1, (1 << 0) ^ 0xff, True )
        chars[pygame.K_8] = ( 1, (1 << 0) ^ 0xff, False )
        chars[pygame.K_LEFTPAREN] = ( 1, (1 << 1) ^ 0xff, True )
        chars[pygame.K_9] = ( 1, (1 << 1) ^ 0xff, False )
        chars[ord('_')] = ( 1, (1 << 2) ^ 0xff, True )
        chars[ord('-')] = ( 1, (1 << 2) ^ 0xff, False )
        chars[ord('+')] = ( 1, (1 << 3) ^ 0xff, True )
        chars[ord('=')] = ( 1, (1 << 3) ^ 0xff, False )
        chars[ord('|')] = ( 1, (1 << 4) ^ 0xff, True )
        chars[ord('\\')] = ( 1, (1 << 4) ^ 0xff, False )
        chars[ord('{')] = ( 1, (1 << 5) ^ 0xff, True )
        chars[ord('[')] = ( 1, (1 << 5) ^ 0xff, False )
        chars[ord('}')] = ( 1, (1 << 6) ^ 0xff, True )
        chars[ord(']')] = ( 1, (1 << 6) ^ 0xff, False )
        chars[ord(':')] = ( 1, (1 << 7) ^ 0xff, True )
        chars[ord(';')] = ( 1, (1 << 7) ^ 0xff, False )
        chars[pygame.K_QUOTEDBL] = ( 2, (1 << 0) ^ 0xff, True )
        chars[pygame.K_QUOTE] = ( 2, (1 << 0) ^ 0xff, False )
        chars[ord('~')] = ( 2, (1 << 1) ^ 0xff, True )
        chars[ord('`')] = ( 2, (1 << 1) ^ 0xff, False )
        chars[ord('<')] = ( 2, (1 << 2) ^ 0xff, True )
        chars[ord(',')] = ( 2, (1 << 2) ^ 0xff, False )
        chars[ord('>')] = ( 2, (1 << 3) ^ 0xff, True )
        chars[ord('.')] = ( 2, (1 << 3) ^ 0xff, False )
        chars[ord('?')] = ( 2, (1 << 4) ^ 0xff, True )
        chars[ord('/')] = ( 2, (1 << 4) ^ 0xff, False )
        chars[pygame.K_a] = ( 2, (1 << 6) ^ 0xff, None )
        chars[pygame.K_b] = ( 2, (1 << 7) ^ 0xff, None )
        chars[pygame.K_c] = ( 3, (1 << 0) ^ 0xff, None )
        chars[pygame.K_d] = ( 3, (1 << 1) ^ 0xff, None )
        chars[pygame.K_e] = ( 3, (1 << 2) ^ 0xff, None )
        chars[pygame.K_f] = ( 3, (1 << 3) ^ 0xff, None )
        chars[pygame.K_g] = ( 3, (1 << 4) ^ 0xff, None )
        chars[pygame.K_h] = ( 3, (1 << 5) ^ 0xff, None )
        chars[pygame.K_i] = ( 3, (1 << 6) ^ 0xff, None )
        chars[pygame.K_j] = ( 3, (1 << 7) ^ 0xff, None )
        chars[pygame.K_k] = ( 4, (1 << 0) ^ 0xff, None )
        chars[pygame.K_l] = ( 4, (1 << 1) ^ 0xff, None )
        chars[pygame.K_m] = ( 4, (1 << 2) ^ 0xff, None )
        chars[pygame.K_n] = ( 4, (1 << 3) ^ 0xff, None )
        chars[pygame.K_o] = ( 4, (1 << 4) ^ 0xff, None )
        chars[pygame.K_p] = ( 4, (1 << 5) ^ 0xff, None )
        chars[pygame.K_q] = ( 4, (1 << 6) ^ 0xff, None )
        chars[pygame.K_r] = ( 4, (1 << 7) ^ 0xff, None )
        chars[pygame.K_s] = ( 5, (1 << 0) ^ 0xff, None )
        chars[pygame.K_t] = ( 5, (1 << 1) ^ 0xff, None )
        chars[pygame.K_u] = ( 5, (1 << 2) ^ 0xff, None )
        chars[pygame.K_v] = ( 5, (1 << 3) ^ 0xff, None )
        chars[pygame.K_w] = ( 5, (1 << 4) ^ 0xff, None )
        chars[pygame.K_x] = ( 5, (1 << 5) ^ 0xff, None )
        chars[pygame.K_y] = ( 5, (1 << 6) ^ 0xff, None )
        chars[pygame.K_z] = ( 5, (1 << 7) ^ 0xff, None )
        chars[pygame.K_BACKSPACE] = ( 7, (1 << 5) ^ 0xff, False )
        chars[pygame.K_RETURN] = ( 7, (1 << 7) ^ 0xff, False )
        chars[pygame.K_SPACE] = ( 8, (1 << 0) ^ 0xff, False )
        chars[pygame.K_DELETE] = ( 8, (1 << 3) ^ 0xff, False )
        chars[pygame.K_LEFT] = ( 8, (1 << 4) ^ 0xff, False )
        chars[pygame.K_UP] = ( 8, (1 << 5) ^ 0xff, False )
        chars[pygame.K_DOWN] = ( 8, (1 << 6) ^ 0xff, False )
        chars[pygame.K_RIGHT] = ( 8, (1 << 7) ^ 0xff, False )

        if not c.key in chars:
            print('key %c not in chars (space = %d)' % (c.key, pygame.K_SPACE), file=sys.stderr)
            return None

        if c.key >= pygame.K_a and c.key <= pygame.K_z:
            shift = (c.mod & (pygame.KMOD_LSHIFT | pygame.KMOD_RSHIFT | pygame.KMOD_CAPS)) != 0

            return (chars[c.key][0], chars[c.key][1], shift)

        if c.key == pygame.K_SPACE:
            print('hier', file=sys.stderr)
        print('daar %s %s %s' % chars[c.key], file=sys.stderr)

        return chars[c.key]

    def poll_kb(self):
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                self.stop_flag = True
                break

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RETURN:
                    print('MARKER', file=sys.stderr)

                self.k_lock.acquire()
                self.keyboard_queue.append(event)
                self.k_lock.release()

    def run(self):
        while not self.stop_flag:
            with self.cv:
                self.poll_kb()

                while self.redraw == False and self.stop_flag == False:
                    self.poll_kb()

                    self.cv.wait(0.01)

                self.redraw = False

            msg = self.debug_msg[0:79]

            s = time.time()
            hit = 0
            hitdiv = 1

            # redraw
            vm = self.video_mode()
            if vm == 1:  # 'screen 2' (256 x 192)
                bg_map    = (self.registers[2] &  15) << 10
                bg_colors = (self.registers[3] & 128) <<  6
                bg_tiles  = (self.registers[4] &   4) << 11

                par = pygame.PixelArray(self.surface)

                pb = None
                cache = None

                tiles_offset = colors_offset = 0

                hitdiv = 32 * 24

                for map_index in range(0, 32 * 24):
                    block_nr    = (map_index >> 8) & 3

                    if block_nr != pb:
                        cache = [ None ] * 256
                        pb = block_nr

                        tiles_offset = bg_tiles  + (block_nr * 256 * 8)
                        colors_offset = bg_colors + (block_nr * 256 * 8)

                    cur_char_nr = self.ram[bg_map + map_index]

                    scr_x = (map_index & 31) * 8;
                    scr_y = ((map_index >> 5) & 31) * 8;

                    if cache[cur_char_nr] == None:
                        cache[cur_char_nr] = [ 0 ] * 64

                        cur_tiles   = tiles_offset + cur_char_nr * 8
                        cur_colors  = colors_offset + cur_char_nr * 8

                        for y in range(0, 8):
                            current_tile = self.ram[cur_tiles]
                            cur_tiles += 1

                            current_color = self.ram[cur_colors]
                            cur_colors += 1

                            fg = self.rgb[current_color >> 4]
                            bg = self.rgb[current_color & 15]

                            for x in range(0, 8):
                                cache[cur_char_nr][y * 8 + x] = fg if (current_tile & 128) == 128 else bg
                                current_tile <<= 1
                    else:
                        hit += 1

                    for y in range(0, 8):
                        for x in range(0, 8):
                            self.arr[scr_x + x, scr_y + y] = cache[cur_char_nr][y * 8 + x]

                pygame.surfarray.blit_array(self.screen, self.arr)
                pygame.display.flip()

            elif vm == 4:  # 40 x 24
                cols = 40  # FIXME
                hitdiv = cols * 24

                bg_map = (self.registers[2] & 0x7c) << 10 if cols == 80 else (self.registers[2] & 15) << 10
                bg_tiles = (self.registers[4] & 7) << 11

                bg = self.rgb[self.registers[7] & 15]
                fg = self.rgb[self.registers[7] >> 4]

                par = pygame.PixelArray(self.surface)

                pb = None
                cache = [ None ] * 256

                tiles_offset = colors_offset = 0

                for map_index in range(0, 40 * 24):
                    cur_char_nr = self.ram[bg_map + map_index]

                    scr_x = (map_index % cols) * 8;
                    scr_y = (map_index // cols) * 8;

                    if cache[cur_char_nr] == None:
                        cache[cur_char_nr] = [ 0 ] * 64

                        cur_tiles = bg_tiles + cur_char_nr * 8

                        for y in range(0, 8):
                            current_tile = self.ram[cur_tiles]
                            cur_tiles += 1

                            for x in range(0, 8):
                                cache[cur_char_nr][y * 8 + x] = fg if (current_tile & 128) == 128 else bg
                                current_tile <<= 1
                    else:
                        hit += 1

                    for y in range(0, 8):
                        for x in range(0, 8):
                            self.arr[scr_x + x, scr_y + y] = cache[cur_char_nr][y * 8 + x]

                pygame.surfarray.blit_array(self.screen, self.arr)
                pygame.display.flip()

            elif vm == 0:  # 'screen 1' (32 x 24)
                bg_map    = (self.registers[2] &  15) << 10;
                bg_colors = (self.registers[3] & 128) <<  6
                bg_tiles  = (self.registers[4] &   4) << 11

                cols = 32
                hitdiv = cols * 24

                par = pygame.PixelArray(self.surface)

                pb = None
                cache = [ None ] * 256

                tiles_offset = colors_offset = 0

                for map_index in range(0, 32 * 24):
                    cur_char_nr = self.ram[bg_map + map_index]

                    current_color = self.ram[bg_colors + cur_char_nr // 8]
                    fg = self.rgb[current_color >> 4];
                    bg = self.rgb[current_color & 15];

                    scr_x = (map_index % cols) * 8;
                    scr_y = (map_index // cols) * 8;

                    if cache[cur_char_nr] == None:
                        cache[cur_char_nr] = [ 0 ] * 64

                        cur_tiles = bg_tiles + cur_char_nr * 8

                        for y in range(0, 8):
                            current_tile = self.ram[cur_tiles]
                            cur_tiles += 1

                            for x in range(0, 8):
                                cache[cur_char_nr][y * 8 + x] = fg if (current_tile & 128) == 128 else bg
                                current_tile <<= 1
                    else:
                        hit += 1

                    for y in range(0, 8):
                        for x in range(0, 8):
                            self.arr[scr_x + x, scr_y + y] = cache[cur_char_nr][y * 8 + x]

                pygame.surfarray.blit_array(self.screen, self.arr)
                pygame.display.flip()
                par = pygame.PixelArray(self.surface)

            else:
                msg = 'Unsupported resolution'

            took = time.time() - s
            print('fps: %f, cache hit: %.2f%%' % (1 / took, hit * 100.0 / hitdiv))

            self.debug_msg_lock.acquire()
            if self.debug_msg:
                #self.win.addstr(25, 0, msg)
                pass  # FIXME
            self.debug_msg_lock.release()
