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
