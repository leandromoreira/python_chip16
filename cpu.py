import logging

# machine specs https://github.com/tykel/chip16/wiki/Machine-Specification
class Cpu:
    RAM_ROM_START = 0x0000
    STACK_START = 0xFDF0
    IO_PORTS_START = 0xFFF0
    CYCLES_PER_SECOND = 1000000 #1MHz
    CYCLES_PER_INSTRUCTION = 1

    def __init__(self):
        logging.basicConfig(filename='pchip16.log', level=logging.DEBUG)
        self.reset()

    def reset(self):
        self.__instruction_set = self.__instruction_table()
        self.current_cyles = 0
        self.pc = Cpu.RAM_ROM_START
        self.sp = Cpu.STACK_START
        self.r  = [None] * (0xF + 1)
        # Flags: xCZxxxON
        # C => carry
        # Z => zero
        # O => overflow
        # N => negative
        self.flag = 0b00000000
        self.memory = [None] * (0xFFFF + 1)

    def step(self):
        params = self.create_params(self.pc)
        current_instruction = self.__instruction_set[params['op_code']]

        logging.info(self.__replace_constants(current_instruction['Mnemonic'], params))

        self.pc += current_instruction['execute'](params)
        self.current_cyles += 1

    def register_pc(self):
        return self.__create_16bit_two_complement(self.pc)

    def register_sp(self):
        return self.__create_16bit_two_complement(self.sp)

    def register_r(self, index):
        return self.__create_16bit_two_complement(self.r[index])

    def write(self, address, value):
        # little-endian machine
        self.memory[address]   = value & 0xFF
        self.memory[address + 1] = value >> 8

    def read(self, address):
        # little-endian machine
        value = (self.memory[address + 1] << 8) | self.memory[address]
        return self.__create_16bit_two_complement(value)

    def print_memory(self):
        logging.debug("$$$$$$$$$$$$$$$$$ Memory State $$$$$$$$$$$$$$$$$$$$")
        used_memory = ["[%s]=%s" % (hex(index), hex(x)) for index, x in enumerate(self.memory) if x is not None]
        logging.debug(used_memory)
        logging.debug("$$$$$$$$$$$$$$$$$ Memory State $$$$$$$$$$$$$$$$$$$$")

    def print_state(self):
        logging.debug("$$$$$$$$$$$$$$$$$ Cpu State $$$$$$$$$$$$$$$$$$$$")
        logging.debug("PC=%s, SP=%s, Flags=%s",hex(self.pc), hex(self.sp), bin(self.flag))
        pc_memory = self.memory[self.pc]
        sp_memory = self.memory[self.sp]
        if pc_memory is not None:
            pc_memory = hex(pc_memory)
        if sp_memory is not None:
            sp_memory = hex(sp_memory)
        r = ["R%s=%s" % (index, hex(x)) for index, x in enumerate(self.r) if x is not None]
        logging.debug("[PC]=%s, [SP]=%s", pc_memory, sp_memory)
        logging.debug("General regiters: %s", r)
        logging.debug("$$$$$$$$$$$$$$$$$ Cpu State $$$$$$$$$$$$$$$$$$$$")

    # from http://stackoverflow.com/questions/1604464/twos-complement-in-python
    def __create_16bit_two_complement(self, value):
        # the machine works with 2's complement representation
        if( (value&(1<<(16-1))) != 0 ):
            value = value - (1<<16)
        return value

    def create_params(self, address):
        # 40 YX LL HH
        params = {}
        params['op_code'] = self.memory[address]
        params['y'] = self.memory[address + 1] >> 4
        params['x'] = self.memory[address + 1] & 0b00001111
        params['ll'] = self.memory[address + 2]
        params['hh'] = self.memory[address + 3]
        params['hhll'] = (params['hh'] << 8) | params['ll']
        return params

    def __replace_constants(self, mnemonic, params):
        mnemonic = mnemonic.replace("X", hex(params['x'])[2:])
        mnemonic = mnemonic.replace("Y", hex(params['y'])[2:])
        mnemonic = mnemonic.replace("HHLL", hex(params['hhll']))
        return mnemonic.lower()

    def __instruction_table(self):
        instruction_table = {}

        ### 2x Load operations ###
        def ldi_rx(params):
            self.r[params['x']] = params['hhll']
            return 4

        instruction_table[0x20] = {
            'Mnemonic': 'LDI RX, HHLL',
            'execute': ldi_rx
        }

        def ldi_sp(params):
            self.sp = params['hhll']
            return 4

        instruction_table[0x21] = {
            'Mnemonic': 'LDI SP, HHLL',
            'execute': ldi_sp
        }

        def ldm_rx(params):
            self.r[params['x']] = self.memory[params['hhll']]
            return 4

        instruction_table[0x22] = {
            'Mnemonic': 'LDM RX, HHLL',
            'execute': ldm_rx
        }

        def ldm_rx_ry(params):
            self.r[params['x']] = self.memory[self.r[params['y']]]
            return 4

        instruction_table[0x23] = {
            'Mnemonic': 'LDM RX, RY',
            'execute': ldm_rx_ry
        }

        def mov_rx_ry(params):
            self.r[params['x']] = self.memory[self.r[params['y']]]
            return 4

        instruction_table[0x24] = {
            'Mnemonic': 'MOV RX, RY',
            'execute': mov_rx_ry
        }
        ########################

        ### 3x Store operations ###
        def stm_rx(params):
            self.memory[params['hhll']] = self.r[params['x']]
            return 4

        instruction_table[0x30] = {
            'Mnemonic': 'STM RX, HHLL',
            'execute': stm_rx
        }

        def stm_rx_ry(params):
            self.memory[self.r[params['y']]] = self.r[params['x']]
            return 4

        instruction_table[0x31] = {
            'Mnemonic': 'STM RX, RY',
            'execute': stm_rx_ry
        }
        ########################

        return instruction_table


