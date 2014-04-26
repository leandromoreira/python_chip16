import gpu
import spu
import logging
import random

# machine specs https://github.com/tykel/chip16/wiki/Machine-Specification
class Cpu:
    RAM_ROM_START = 0x0000
    STACK_START = 0xFDF0
    IO_PORTS_START = 0xFFF0
    CYCLES_PER_SECOND = 1000000 #1MHz
    CYCLES_PER_INSTRUCTION = 1

    def __init__(self):
        logging.basicConfig(filename='pchip16.log', level=logging.DEBUG)
        self.gpu = gpu.Gpu()
        self.spu = spu.Spu()
        self.reset()

    def reset(self):
        self.__instruction_set = self.__instruction_table()
        self.current_cyles = 0
        self.pc = Cpu.RAM_ROM_START
        self.sp = Cpu.STACK_START
        self.r  = [None] * (0xF + 1)
        self.flag_carry = 0
        self.flag_zero = 0
        self.flag_overflow = 0
        self.flag_negative = 0
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
        logging.debug("PC=%s, SP=%s",hex(self.pc), hex(self.sp))
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

    def create_16bit_two_complement(self, value):
        return self.__create_16bit_two_complement(value)

    # from http://stackoverflow.com/questions/1604464/twos-complement-in-python
    def __create_16bit_two_complement(self, value):
        # the machine works with 2's complement representation
        if( (value&(1<<(16-1))) != 0 ):
            value = value - (1<<16)
        return value

    def create_params(self, address):
        params = {}
        params['op_code'] = self.memory[address]
        params['y'] = self.memory[address + 1] >> 4
        params['x'] = self.memory[address + 1] & 0b00001111
        params['n'] = self.memory[address + 2] & 0b00001111
        params['z'] = params['n']
        params['ll'] = self.memory[address + 2]
        params['hh'] = self.memory[address + 3]
        params['hflip'] = (params['hh'] >> 1)
        params['vflip'] = (params['hh'] & 1)
        params['hhll'] = (params['hh'] << 8) | params['ll']
        params['vtsr'] = params['hhll']
        params['ad'] = self.memory[address + 1]
        return params

    def __replace_constants(self, mnemonic, params):
        mnemonic = mnemonic.replace(" 0, 0", " %s, %s" % (params['hflip'], params['vflip']))
        mnemonic = mnemonic.replace("X", hex(params['x'])[2:])
        mnemonic = mnemonic.replace("Y", hex(params['y'])[2:])
        mnemonic = mnemonic.replace("RZ", "r%s" % hex(params['z'])[2:])
        mnemonic = mnemonic.replace(" N", " " + hex(params['n'])[2:])
        mnemonic = mnemonic.replace("HHLL", hex(params['hhll']))
        mnemonic = mnemonic.replace("VTSR", hex(params['vtsr']))
        mnemonic = mnemonic.replace(" AD", " %s" % hex(params['ad']))
        return mnemonic.lower()

    def __instruction_table(self):
        instruction_table = {}

        ### 0x - Misc/Video/Audio ###
        def nop(params):
            return 4

        instruction_table[0x00] = {
            'Mnemonic': 'NOP',
            'execute': nop
        }

        def cls(params):
            self.gpu.clear_fg()
            self.gpu.clear_bg()
            return 4

        instruction_table[0x01] = {
            'Mnemonic': 'CLS',
            'execute': cls
        }

        def vblank(params):
            if self.gpu.vblank():
                return 4
            return 0

        instruction_table[0x02] = {
            'Mnemonic': 'VBLNK',
            'execute': vblank
        }

        def bgc(params):
            self.gpu.bg = params['n']
            return 4

        instruction_table[0x03] = {
            'Mnemonic': 'BGC N',
            'execute': bgc
        }

        def spr(params):
            self.gpu.spritew = params['ll']
            self.gpu.spriteh = params['hh']
            return 4

        instruction_table[0x04] = {
            'Mnemonic': 'SPR HHLL',
            'execute': spr
        }

        def drw_hhll(params):
            carried = self.gpu.drw_hhll(params['hhll'], self.r[params['x']], self.r[params['y']])
            self.flag_carry = carried
            return 4

        instruction_table[0x05] = {
            'Mnemonic': 'DRW RX, RY, HHLL',
            'execute': drw_hhll
        }

        def drw_rz(params):
            carried = self.gpu.drw_rz(self.read(self.r[params['z']]), self.r[params['x']], self.r[params['y']])
            self.flag_carry = carried
            return 4

        instruction_table[0x06] = {
            'Mnemonic': 'DRW RX, RY, RZ',
            'execute': drw_rz
        }

        def rnd(params):
            self.r[params['x']] = random.randint(0, params['hhll'])
            return 4

        instruction_table[0x07] = {
            'Mnemonic': 'RND RX, HHLL',
            'execute': rnd
        }

        def flip(params):
            self.gpu.flip(params['hflip'] == 1, params['vflip'] == 1)
            return 4

        instruction_table[0x08] = {
            'Mnemonic': 'FLIP 0, 0',
            'execute': flip
        }

        def snd0(params):
            self.spu.stop()
            return 4

        instruction_table[0x09] = {
            'Mnemonic': 'SND0',
            'execute': snd0
        }

        def snd1(params):
            self.spu.play500hz(params['hhll'])
            return 4

        instruction_table[0x0A] = {
            'Mnemonic': 'SND1 HHLL',
            'execute': snd1
        }

        def snd2(params):
            self.spu.play1000hz(params['hhll'])
            return 4

        instruction_table[0x0B] = {
            'Mnemonic': 'SND2 HHLL',
            'execute': snd2
        }

        def snd3(params):
            self.spu.play1500hz(params['hhll'])
            return 4

        instruction_table[0x0C] = {
            'Mnemonic': 'SND3 HHLL',
            'execute': snd3
        }

        def snp(params):
            self.spu.play_tone(self.memory[self.r[params['x']]], params['hhll'])
            return 4

        instruction_table[0x0D] = {
            'Mnemonic': 'SNP RX, HHLL',
            'execute': snp
        }

        def sng(params):
            self.spu.setup(params['ad'], params['vtsr'])
            return 4

        instruction_table[0x0E] = {
            'Mnemonic': 'SNG AD, VTSR',
            'execute': sng
        }
        ########################
        ### 1x - Jumps (Branches) ###
        def jmp(params):
            return params['hhll'] - self.pc

        instruction_table[0x10] = {
            'Mnemonic': 'JMP HHLL',
            'execute': jmp
        }

        def jmpx(params):
            if params['x'] != 0:
                return params['hhll'] - self.pc
            else:
                return 4

        instruction_table[0x12] = {
            'Mnemonic': 'Jx HHLL',
            'execute': jmpx
        }

        def jme(params):
            if self.r[params['x']] == self.r[params['y']]:
                return params['hhll'] - self.pc
            else:
                return 4

        instruction_table[0x13] = {
            'Mnemonic': 'JME RX, RY, HHLL',
            'execute': jme
        }

        def call(params):
            self.write(self.sp, self.pc + 4)
            self.sp += 2
            return params['hhll'] - self.pc

        instruction_table[0x14] = {
            'Mnemonic': 'CALL HHLL',
            'execute': call
        }

        def ret(params):
            self.sp -= 2
            return self.read(self.sp) - self.pc

        instruction_table[0x15] = {
            'Mnemonic': 'RET',
            'execute': ret
        }

        def jmp_rx(params):
            return self.r[params['x']] - self.pc

        instruction_table[0x16] = {
            'Mnemonic': 'JMP RX',
            'execute': jmp_rx
        }

        def call_x(params):
            if params['x'] != 0:
                return call(params)
            else:
                return 4

        instruction_table[0x17] = {
            'Mnemonic': 'Cx HHLL',
            'execute': call_x
        }

        def call_rx(params):
            self.write(self.sp, self.pc + 4)
            self.sp += 2
            return self.r[params['x']] - self.pc

        instruction_table[0x18] = {
            'Mnemonic': 'CALL RX',
            'execute': call_rx
        }
        ########################
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

        def check_carry_add(result):
            if result > 0b1111111111111111:
                self.flag_carry = 1
            else:
                self.flag_carry = 0

        def check_zero_add(result):
            if result == 0:
                self.flag_zero = 1
            else:
                self.flag_zero = 0

        def check_overflow_add(result, operand1, operand2):
            result_is_positive = self.__create_16bit_two_complement(result) >= 0
            operands_are_negative = self.__create_16bit_two_complement(operand1) < 0 and self.__create_16bit_two_complement(operand2) < 0
            result_is_negative = not result_is_positive
            operands_are_positive =  not operands_are_negative

            if (result_is_positive and operands_are_negative) or (result_is_negative and operands_are_positive):
                self.flag_overflow = 1
            else:
                self.flag_overflow = 0

        def check_negative_add(result):
            if self.__create_16bit_two_complement(result) < 0:
                self.flag_negative = 1
            else:
                self.flag_negative = 0

        ### 4x - Addition ###
        def addi_rx(params):
            sum = self.r[params['x']] + params['hhll']
            check_carry_add(sum)
            check_zero_add(sum)
            check_overflow_add(sum, self.r[params['x']], params['hhll'])
            check_negative_add(sum)
            self.r[params['x']] = sum & 0xFFFF
            return 4

        instruction_table[0x40] = {
            'Mnemonic': 'ADDI RX, HHLL',
            'execute': addi_rx
        }

        def add_rx(params):
            sum = self.r[params['x']] + self.r[params['y']]
            check_carry_add(sum)
            check_zero_add(sum)
            check_overflow_add(sum, self.r[params['x']], params['y'])
            check_negative_add(sum)
            self.r[params['x']] = sum & 0xFFFF
            return 4

        instruction_table[0x41] = {
            'Mnemonic': 'ADD RX, RY',
            'execute': add_rx
        }

        def add_rz(params):
            sum = self.r[params['x']] + self.r[params['y']]
            check_carry_add(sum)
            check_zero_add(sum)
            check_overflow_add(sum, self.r[params['x']], params['y'])
            check_negative_add(sum)
            self.r[params['z']] = sum & 0xFFFF
            return 4

        instruction_table[0x42] = {
            'Mnemonic': 'ADD RX, RY, RZ',
            'execute': add_rz
        }
        ########################
        ### 5x - Subtraction ###
        ########################

        return instruction_table
