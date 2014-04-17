import logging

class Gpu:

    def __init__(self):
        self.bg = 0b0000
        self.spritew = 0x00
        self.spriteh = 0x00
        self.hflip = False
        self.vflip = False

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
