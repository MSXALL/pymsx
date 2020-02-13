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

        chars[')'] = ( 0, (1 << 0) ^ 0xff, True )
        chars['0'] = ( 0, (1 << 0) ^ 0xff, False )
        chars['!'] = ( 0, (1 << 1) ^ 0xff, True )
        chars['1'] = ( 0, (1 << 1) ^ 0xff, False )
        chars['@'] = ( 0, (1 << 2) ^ 0xff, True )
        chars['2'] = ( 0, (1 << 2) ^ 0xff, False )
        chars['#'] = ( 0, (1 << 3) ^ 0xff, True )
        chars['3'] = ( 0, (1 << 3) ^ 0xff, False )
        chars['$'] = ( 0, (1 << 4) ^ 0xff, True )
        chars['4'] = ( 0, (1 << 4) ^ 0xff, False )
        chars['%'] = ( 0, (1 << 5) ^ 0xff, True )
        chars['5'] = ( 0, (1 << 5) ^ 0xff, False )
        chars['^'] = ( 0, (1 << 6) ^ 0xff, True )
        chars['6'] = ( 0, (1 << 6) ^ 0xff, False )
        chars['&'] = ( 0, (1 << 7) ^ 0xff, True )
        chars['7'] = ( 0, (1 << 7) ^ 0xff, False )
        chars['*'] = ( 1, (1 << 0) ^ 0xff, True )
        chars['8'] = ( 1, (1 << 0) ^ 0xff, False )
        chars['('] = ( 1, (1 << 1) ^ 0xff, True )
        chars['9'] = ( 1, (1 << 1) ^ 0xff, False )
        chars['_'] = ( 1, (1 << 2) ^ 0xff, True )
        chars['-'] = ( 1, (1 << 2) ^ 0xff, False )
        chars['+'] = ( 1, (1 << 3) ^ 0xff, True )
        chars['='] = ( 1, (1 << 3) ^ 0xff, False )
        chars['|'] = ( 1, (1 << 4) ^ 0xff, True )
        chars['\\'] = ( 1, (1 << 4) ^ 0xff, False )
        chars['{'] = ( 1, (1 << 5) ^ 0xff, True )
        chars['['] = ( 1, (1 << 5) ^ 0xff, False )
        chars['}'] = ( 1, (1 << 6) ^ 0xff, True )
        chars[']'] = ( 1, (1 << 6) ^ 0xff, False )
        chars[':'] = ( 1, (1 << 7) ^ 0xff, True )
        chars[';'] = ( 1, (1 << 7) ^ 0xff, False )
        chars['"'] = ( 2, (1 << 0) ^ 0xff, True )
        chars["'"] = ( 2, (1 << 0) ^ 0xff, False )
        chars['~'] = ( 2, (1 << 1) ^ 0xff, True )
        chars['`'] = ( 2, (1 << 1) ^ 0xff, False )
        chars['<'] = ( 2, (1 << 2) ^ 0xff, True )
        chars[','] = ( 2, (1 << 2) ^ 0xff, False )
        chars['>'] = ( 2, (1 << 3) ^ 0xff, True )
        chars['.'] = ( 2, (1 << 3) ^ 0xff, False )
        chars['?'] = ( 2, (1 << 4) ^ 0xff, True )
        chars['/'] = ( 2, (1 << 4) ^ 0xff, False )
        chars['A'] = ( 2, (1 << 6) ^ 0xff, True )
        chars['a'] = ( 2, (1 << 6) ^ 0xff, False )
        chars['B'] = ( 2, (1 << 7) ^ 0xff, True )
        chars['b'] = ( 2, (1 << 7) ^ 0xff, False )
        chars['C'] = ( 3, (1 << 0) ^ 0xff, True )
        chars['c'] = ( 3, (1 << 0) ^ 0xff, False )
        chars['D'] = ( 3, (1 << 1) ^ 0xff, True )
        chars['d'] = ( 3, (1 << 1) ^ 0xff, False )
        chars['E'] = ( 3, (1 << 2) ^ 0xff, True )
        chars['e'] = ( 3, (1 << 2) ^ 0xff, False )
        chars['F'] = ( 3, (1 << 3) ^ 0xff, True )
        chars['f'] = ( 3, (1 << 3) ^ 0xff, False )
        chars['G'] = ( 3, (1 << 4) ^ 0xff, True )
        chars['g'] = ( 3, (1 << 4) ^ 0xff, False )
        chars['H'] = ( 3, (1 << 5) ^ 0xff, True )
        chars['h'] = ( 3, (1 << 5) ^ 0xff, False )
        chars['I'] = ( 3, (1 << 6) ^ 0xff, True )
        chars['i'] = ( 3, (1 << 6) ^ 0xff, False )
        chars['J'] = ( 3, (1 << 7) ^ 0xff, True )
        chars['j'] = ( 3, (1 << 7) ^ 0xff, False )
        chars['K'] = ( 4, (1 << 0) ^ 0xff, True )
        chars['k'] = ( 4, (1 << 0) ^ 0xff, False )
        chars['L'] = ( 4, (1 << 1) ^ 0xff, True )
        chars['l'] = ( 4, (1 << 1) ^ 0xff, False )
        chars['M'] = ( 4, (1 << 2) ^ 0xff, True )
        chars['m'] = ( 4, (1 << 2) ^ 0xff, False )
        chars['N'] = ( 4, (1 << 3) ^ 0xff, True )
        chars['n'] = ( 4, (1 << 3) ^ 0xff, False )
        chars['O'] = ( 4, (1 << 4) ^ 0xff, True )
        chars['o'] = ( 4, (1 << 4) ^ 0xff, False )
        chars['P'] = ( 4, (1 << 5) ^ 0xff, True )
        chars['p'] = ( 4, (1 << 5) ^ 0xff, False )
        chars['Q'] = ( 4, (1 << 6) ^ 0xff, True )
        chars['q'] = ( 4, (1 << 6) ^ 0xff, False )
        chars['R'] = ( 4, (1 << 7) ^ 0xff, True )
        chars['r'] = ( 4, (1 << 7) ^ 0xff, False )
        chars['S'] = ( 5, (1 << 0) ^ 0xff, True )
        chars['s'] = ( 5, (1 << 0) ^ 0xff, False )
        chars['T'] = ( 5, (1 << 1) ^ 0xff, True )
        chars['t'] = ( 5, (1 << 1) ^ 0xff, False )
        chars['U'] = ( 5, (1 << 2) ^ 0xff, True )
        chars['u'] = ( 5, (1 << 2) ^ 0xff, False )
        chars['V'] = ( 5, (1 << 3) ^ 0xff, True )
        chars['v'] = ( 5, (1 << 3) ^ 0xff, False )
        chars['W'] = ( 5, (1 << 4) ^ 0xff, True )
        chars['w'] = ( 5, (1 << 4) ^ 0xff, False )
        chars['X'] = ( 5, (1 << 5) ^ 0xff, True )
        chars['x'] = ( 5, (1 << 5) ^ 0xff, False )
        chars['Y'] = ( 5, (1 << 6) ^ 0xff, True )
        chars['y'] = ( 5, (1 << 6) ^ 0xff, False )
        chars['Z'] = ( 5, (1 << 7) ^ 0xff, True )
        chars['z'] = ( 5, (1 << 7) ^ 0xff, False )
        chars[pygame.K_F1] = ( 6, (1 << 5) ^ 0xff, False )
        chars[pygame.K_F2] = ( 6, (1 << 6) ^ 0xff, False )
        chars[pygame.K_F3] = ( 6, (1 << 7) ^ 0xff, False )
        chars[pygame.K_F4] = ( 7, (1 << 0) ^ 0xff, False )
        chars[pygame.K_F5] = ( 7, (1 << 1) ^ 0xff, False )
        chars[pygame.K_F6] = ( 6, (1 << 5) ^ 0xff, True )
        chars[pygame.K_F7] = ( 6, (1 << 6) ^ 0xff, True )
        chars[pygame.K_F8] = ( 6, (1 << 7) ^ 0xff, True )
        chars[pygame.K_F9] = ( 7, (1 << 0) ^ 0xff, True )
        chars[pygame.K_F10] = ( 7, (1 << 1) ^ 0xff, True )
        chars[pygame.K_BACKSPACE] = ( 7, (1 << 5) ^ 0xff, False )
        chars[pygame.K_RETURN] = ( 7, (1 << 7) ^ 0xff, False )
        chars[pygame.K_SPACE] = ( 8, (1 << 0) ^ 0xff, False )
        chars[pygame.K_DELETE] = ( 8, (1 << 3) ^ 0xff, False )
        chars[pygame.K_LEFT] = ( 8, (1 << 4) ^ 0xff, False )
        chars[pygame.K_UP] = ( 8, (1 << 5) ^ 0xff, False )
        chars[pygame.K_DOWN] = ( 8, (1 << 6) ^ 0xff, False )
        chars[pygame.K_RIGHT] = ( 8, (1 << 7) ^ 0xff, False )

        if c.unicode in chars:
            return chars[c.unicode]

        if c.key in chars:
            return chars[c.key]

        print('unicode %s / key %d not found' % (c.unicode, c.key), file=sys.stderr)

        return None

    def poll_kb(self):
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                self.stop_flag = True
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    print('MARKER', file=sys.stderr)

                self.k_lock.acquire()
                self.keyboard_queue.append(event)
                self.k_lock.release()

    def draw_sprite_part(self, off_x, off_y, pattern_offset, color, nr):
        sc = (self.registers[5] << 7) + nr * 16

        for y in range(off_y, off_y + 8):
            cur_pattern = self.ram[pattern_offset]
            pattern_offset += 1

            col = self.ram[sc]
            i = 128 if col & 8 else 0

            if y >= 192:
                break

            for x in range(off_x, off_x + 8):
                if x >= 256:
                    break

                if cur_pattern & 128:
                    self.arr[x, y] = color

                cur_pattern <<= 1

            sc += 1

    def draw_sprites(self):
        attr = (self.registers[5] & 127) << 7
        patt = self.registers[6] << 11

        for i in range(0, 32):
            attribute_offset = attr + i * 4

            spx = self.ram[attribute_offset + 0]
            if spx == 0xd0:
                break

            colori = self.ram[attribute_offset + 3] & 15;
            if colori == 0:
                continue

            rgb = self.rgb[colori]

            spy = self.ram[attribute_offset + 1]

            pattern_index = self.ram[attribute_offset + 2];

            if self.registers[1] & 2:
                offset = patt + 8 * pattern_index;

                self.draw_sprite_part(spx + 0, spy + 0, offset + 0, rgb, i)
                self.draw_sprite_part(spx + 0, spy + 8, offset + 8, rgb, i)
                self.draw_sprite_part(spx + 8, spy + 0, offset + 16, rgb, i)
                self.draw_sprite_part(spx + 8, spy + 8, offset + 24, rgb, i)

            else:
                self.draw_sprite_part(spx, spy, pattern_index, colorfg, nr);

    def run(self):
        self.setName('msx-display')

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

                self.draw_sprites()

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
            # print('fps: %f, cache hit: %.2f%%' % (1 / took, hit * 100.0 / hitdiv))

            self.debug_msg_lock.acquire()
            if self.debug_msg:
                #self.win.addstr(25, 0, msg)
                pass  # FIXME
            self.debug_msg_lock.release()
