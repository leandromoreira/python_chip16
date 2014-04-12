class Cpu:
    RAM_START = 0x0000
    STACK_START = 0xFDF0
    IO_PORTS_START = 0xFFF0

    def __init__(self):
        self.reset()

    def reset(self):
        self.pc = Cpu.RAM_START
        self.sp = Cpu.STACK_START
        self.r  = [None] * (0xF + 1)
        self.flag = 0b00000000
        self.memory = [None] * (0xFFFF + 1)

    def write(self, address, value):
        self.memory[address]   = value & 0xFF
        self.memory[address + 1] = value >> 8

    def read(self, address):
        return (self.memory[address + 1] << 8) | self.memory[address]

