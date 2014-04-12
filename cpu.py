class Cpu:
    RAM_START = 0x0000
    STACK_START = 0xFDF0
    IO_PORTS_START = 0xFFF0
    CYCLES_PER_SECOND = 1000000
    CYCLES_PER_INSTRUCTION = 1

    def __init__(self):
        self.reset()

    def reset(self):
        self.pc = Cpu.RAM_START
        self.sp = Cpu.STACK_START
        self.r  = [None] * (0xF + 1)
        self.flag = 0b00000000
        self.memory = [None] * (0xFFFF + 1)

    def register_pc(self):
        return self.__create_16bit_two_complement(self.pc)

    def register_sp(self):
        return self.__create_16bit_two_complement(self.sp)

    def register_r(self, index):
        return self.__create_16bit_two_complement(self.r[index])

    def write(self, address, value):
        self.memory[address]   = value & 0xFF
        self.memory[address + 1] = value >> 8

    def read(self, address):
        value = (self.memory[address + 1] << 8) | self.memory[address]
        two_complement = self.__create_16bit_two_complement(value)
        return two_complement

    # from http://stackoverflow.com/questions/1604464/twos-complement-in-python
    def __create_16bit_two_complement(self, value):
        if( (value&(1<<(16-1))) != 0 ):
            value = value - (1<<16)
        return value
