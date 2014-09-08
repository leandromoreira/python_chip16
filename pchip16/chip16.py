from cpu import Cpu
from gpu import Gpu

class Chip16:

    def __init__(self, rom):
        self.rom = rom
        self.cpu = Cpu()
        self.gpu = Gpu()
        self.cpu.gpu = self.gpu
        # fill ram/rom
        for index, byte in enumerate(self.rom.rom):
            self.cpu.memory[index] = byte

    def step(self):
        self.cpu.step()

    def print_debug(self):
        self.cpu.print_state()
