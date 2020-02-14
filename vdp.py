# (C) 2020 by Folkert van Heusden <mail@vanheusden.com>
# released under AGPL v3.0

# implements VDP and also kb because of pygame

import pygame
import sys
import threading
import time

class vdp(threading.Thread):
    def __init__(self):
        pygame.init()

        self.ram = [ 0 ] * 16384

        self.vdp_rw_pointer = 0
        self.vdp_addr_state = False
        self.vdp_addr_b1 = None
        self.vdp_read_ahead = 0

        self.keyboard_row = 0

        self.registers = [ 0 ] * 8

        self.keys_pressed = {}

        self.stop_flag = False

        # TMS9918 palette 
        self.rgb = [ self.rgb_to_i(0, 0, 0), self.rgb_to_i(0, 0, 0), self.rgb_to_i(33, 200, 66), self.rgb_to_i(94, 220, 120), self.rgb_to_i(84, 85, 237), self.rgb_to_i(125, 118, 252), self.rgb_to_i(212, 82, 77), self.rgb_to_i(66, 235, 245), self.rgb_to_i(252, 85, 84), self.rgb_to_i(255, 121, 120), self.rgb_to_i(212, 193, 84), self.rgb_to_i(231, 206, 128), self.rgb_to_i(33, 176, 59), self.rgb_to_i(201, 91, 186), self.rgb_to_i(204, 204, 204), self.rgb_to_i(255, 255, 255) ] 

        self.screen = pygame.display.set_mode((320, 192))
        self.surface = pygame.Surface((320, 192))
        self.arr = pygame.surfarray.array2d(self.screen)

        self.cv = threading.Condition()

        self.init_kb()

        super(vdp, self).__init__()

    def init_kb(self):
        self.keys = [ None ] * 16
        self.keys[0] = [ pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7 ]
        self.keys[1] = [ pygame.K_8, pygame.K_9, pygame.K_MINUS, pygame.K_PLUS, pygame.K_BACKSLASH, pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET, pygame.K_SEMICOLON ]
        self.keys[2] = [ pygame.K_QUOTE, pygame.K_BACKQUOTE, pygame.K_COMMA, pygame.K_PERIOD, pygame.K_SLASH, None, pygame.K_a, pygame.K_b ]
        self.keys[3] = [ pygame.K_c, pygame.K_d, pygame.K_e, pygame.K_f, pygame.K_g, pygame.K_h, pygame.K_i, pygame.K_j ]
        self.keys[4] = [ pygame.K_k, pygame.K_l, pygame.K_m, pygame.K_n, pygame.K_o, pygame.K_p, pygame.K_q, pygame.K_r ]
        self.keys[5] = [ pygame.K_s, pygame.K_t, pygame.K_u, pygame.K_v, pygame.K_w, pygame.K_x, pygame.K_y, pygame.K_z ]
        self.keys[6] = [ pygame.K_LSHIFT, pygame.K_LCTRL, None, pygame.K_CAPSLOCK, None, pygame.K_F1, pygame.K_F2, pygame.K_F3 ]
        self.keys[7] = [ pygame.K_F4, pygame.K_F5, pygame.K_ESCAPE, pygame.K_TAB, None, pygame.K_BACKSPACE, None, pygame.K_RETURN ]
        self.keys[8] = [ pygame.K_SPACE, None, None, None, pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN, pygame.K_RIGHT ]

    def rgb_to_i(self, r, g, b):
        return (r << 16) | (g << 8) | b

    def interrupts_enabled(self):
        return (self.registers[0] & 1) == 1

    def interrupt(self):
        self.registers[2] |= 128

    def video_mode(self):
        m1 = (self.registers[1] >> 4) & 1;
        m2 = (self.registers[1] >> 3) & 1;
        m3 = (self.registers[0] >> 1) & 1;

        return (m1 << 2) | (m2 << 1) | m3

    def set_register(self, a, v):
        self.registers[a] = v

    def write_io(self, a, v):
        if a == 0x98:
            self.ram[self.vdp_rw_pointer] = v
            self.vdp_rw_pointer += 1
            self.vdp_rw_pointer &= 0x3fff
            self.vdp_addr_state = False
            self.vdp_read_ahead = v

        elif a == 0x99:
            if self.vdp_addr_state == False:
                self.vdp_addr_b1 = v

            else:
                if (v & 128) == 128:
                    v &= 7
                    self.set_register(v, self.vdp_addr_b1)

                else:
                    self.vdp_rw_pointer = ((v & 63) << 8) + self.vdp_addr_b1

                    if (v & 64) == 0:
                        self.vdp_read_ahead = self.ram[self.vdp_rw_pointer]
                        self.vdp_rw_pointer += 1
                        self.vdp_rw_pointer &= 0x3fff

            self.vdp_addr_state = not self.vdp_addr_state

        elif a == 0xaa:  # PPI register C
            self.keyboard_row = v & 15

        else:
            print('vdp::write_io: Unexpected port %02x' % a)

    def read_keyboard(self):
        cur_row = self.keys[self.keyboard_row]
        if not cur_row:
            print('kb fail', self.keyboard_row)
            return 255

        bits = 0

        bit_nr = 0
        for key in cur_row:
            if key and key in self.keys_pressed and self.keys_pressed[key]:
                bits |= 1 << bit_nr

            bit_nr += 1

        return bits ^ 0xff

    def read_io(self, a):
        rc = 0

        if a == 0x98:
            rc = self.vdp_read_ahead
            self.vdp_read_ahead = self.ram[self.vdp_rw_pointer]
            self.vdp_rw_pointer += 1
            self.vdp_rw_pointer &= 0x3fff

        elif a == 0x99:
            rc = self.registers[2]
            self.registers[2] &= 127

        elif a == 0xa9:
            rc = self.read_keyboard() 

        else:
            print('vdp::read_io: Unexpected port %02x' % a)

        return rc

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

            spx = self.ram[attribute_offset + 1]
            if spx == 0xd0:
                break

            colori = self.ram[attribute_offset + 3] & 15;
            if colori == 0:
                continue

            rgb = self.rgb[colori]

            spy = self.ram[attribute_offset + 0]

            pattern_index = self.ram[attribute_offset + 2];

            if self.registers[1] & 2:
                offset = patt + 8 * pattern_index;

                self.draw_sprite_part(spx + 0, spy + 0, offset + 0, rgb, i)
                self.draw_sprite_part(spx + 0, spy + 8, offset + 8, rgb, i)
                self.draw_sprite_part(spx + 8, spy + 0, offset + 16, rgb, i)
                self.draw_sprite_part(spx + 8, spy + 8, offset + 24, rgb, i)

            else:
                self.draw_sprite_part(spx, spy, pattern_index, rgb, i);

    def poll_kb(self):
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                self.stop_flag = True
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    print('MARKER', file=sys.stderr)

                self.keys_pressed[event.key] = True

            elif event.type == pygame.KEYUP:
                self.keys_pressed[event.key] = False

    def run(self):
        self.setName('msx-display')

        while not self.stop_flag:
            self.poll_kb()
            time.sleep(0.02)

            #msg = self.debug_msg[0:79]

            s = time.time()
            hit = 0
            hitdiv = 1

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
                #msg = 'Unsupported resolution'
                print('Unsupported resolution')
                pass

            took = time.time() - s
            # print('fps: %f, cache hit: %.2f%%' % (1 / took, hit * 100.0 / hitdiv))

            #self.debug_msg_lock.acquire()
            #if self.debug_msg:
                #self.win.addstr(25, 0, msg)
            #    pass  # FIXME
            #self.debug_msg_lock.release()
