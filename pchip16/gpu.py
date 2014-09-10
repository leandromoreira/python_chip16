import logging

class Gpu:
    def __init__(self):
        self.bg = 0b0000
        self.spritew = 0x00
        self.spriteh = 0x00
        self.hflip = False
        self.vflip = False
        self.__init_palette()

    def __init_palette(self):
        # rgb fitable for opengl
        self.palette = {}
        self.palette[0x0] = {'r': 0, 'g': 0, 'b': 0}
        self.palette[0x1] = {'r': 0, 'g': 0, 'b': 0}
        self.palette[0x2] = {'r': 136.0/255.0, 'g': 136.0/255.0, 'b': 136.0/255.0}
        self.palette[0x3] = {'r': 191.0/255.0, 'g': 57.0/255.0, 'b': 50.0/255.0}
        self.palette[0x4] = {'r': 222.0/255.0, 'g': 122.0/255.0, 'b': 174.0/255.0}
        self.palette[0x5] = {'r': 76.0/255.0, 'g': 61.0/255.0, 'b': 33.0/255.0}
        self.palette[0x6] = {'r': 144.0/255.0, 'g': 95.0/255.0, 'b': 37.0/255.0}
        self.palette[0x7] = {'r': 228.0/255.0, 'g': 148.0/255.0, 'b': 82.0/255.0}
        self.palette[0x8] = {'r': 234.0/255.0, 'g': 217.0/255.0, 'b': 121.0/255.0}
        self.palette[0x9] = {'r': 83.0/255.0, 'g': 122.0/255.0, 'b': 59.0/255.0}
        self.palette[0xA] = {'r': 171.0/255.0, 'g': 213.0/255.0, 'b': 74.0/255.0}
        self.palette[0xB] = {'r': 37.0/255.0, 'g': 46.0/255.0, 'b': 56.0/255.0}
        self.palette[0xC] = {'r': 0.0, 'g': 70.0/255.0, 'b': 127.0/255.0}
        self.palette[0xD] = {'r': 104.0/255.0, 'g': 171.0/255.0, 'b': 204.0/255.0}
        self.palette[0xE] = {'r': 188.0/255.0, 'g': 222.0/255.0, 'b': 228.0/255.0}
        self.palette[0xF] = {'r': 1, 'g': 1, 'b': 1}

    def set_palette(self, index, r, g, b):
        r = float(r)/255.0 if r>0 else r
        g = float(g)/255.0 if g>0 else g
        b = float(b)/255.0 if b>0 else b
        self.palette[index] = {'r': r, 'g': g, 'b': b}

    def clear_fg(self):
        pass

    def clear_bg(self):
        pass

    def vblank(self):
        return False

    def flip(self, hflip, vflip):
        self.hflip = hflip
        self.vflip = vflip

    def there_is_overlap(self, hhll):
        return False

    def drw_hhll(self, hhll, x, y):
        # Draw using opengl/framebuffer
        if self.there_is_overlap():
            return 1
        else:
            return 0

    def print_state(self):
        logging.debug("$$$$$$$$$$$$$$$$$ Gpu State $$$$$$$$$$$$$$$$$$$$")
        logging.debug("BG=%s, Sprite W=%s, Sprite H=%s, H flip=%s, V flip=%s",self.bg, self.spritew, self.spriteh, self.hflip, self.vflip)
        logging.debug("$$$$$$$$$$$$$$$$$ Gpu State $$$$$$$$$$$$$$$$$$$$")
