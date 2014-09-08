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
    DEBUG_MODE = False

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

        if self.DEBUG_MODE:
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

    def write_16bit(self, address, value):
        # little-endian machine
        self.memory[address]   = value & 0xFF
        self.memory[address + 1] = value >> 8

    def read_16bit(self, address):
        # little-endian machine
        return (self.memory[address + 1] << 8) | self.memory[address]

    def write_8bit(self, address, value):
        self.memory[address]   = value & 0xFF

    def read_8bit(self, address):
        return self.memory[address]

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
        if not mnemonic.startswith('XOR') and not mnemonic.startswith('XORI'):
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
            carried = self.gpu.drw_rz(self.read_16bit(self.r[params['z']]), self.r[params['x']], self.r[params['y']])
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
            self.write_16bit(self.sp, self.pc + 4)
            self.sp += 2
            return params['hhll'] - self.pc

        instruction_table[0x14] = {
            'Mnemonic': 'CALL HHLL',
            'execute': call
        }

        def ret(params):
            self.sp -= 2
            return self.read_16bit(self.sp) - self.pc

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
            self.write_16bit(self.sp, self.pc + 4)
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

        def check_zero(result):
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

        def check_negative(result):
            if self.__create_16bit_two_complement(result) < 0:
                self.flag_negative = 1
            else:
                self.flag_negative = 0

        ### 4x - Addition ###
        def addi_rx(params):
            sum = self.r[params['x']] + params['hhll']
            check_carry_add(sum)
            check_zero(sum)
            check_overflow_add(sum, self.r[params['x']], params['hhll'])
            check_negative(sum)
            self.r[params['x']] = sum & 0xFFFF
            return 4

        instruction_table[0x40] = {
            'Mnemonic': 'ADDI RX, HHLL',
            'execute': addi_rx
        }

        def add_rx(params):
            sum = self.r[params['x']] + self.r[params['y']]
            check_carry_add(sum)
            check_zero(sum)
            check_overflow_add(sum, self.r[params['x']], params['y'])
            check_negative(sum)
            self.r[params['x']] = sum & 0xFFFF
            return 4

        instruction_table[0x41] = {
            'Mnemonic': 'ADD RX, RY',
            'execute': add_rx
        }

        def add_rz(params):
            sum = self.r[params['x']] + self.r[params['y']]
            check_carry_add(sum)
            check_zero(sum)
            check_overflow_add(sum, self.r[params['x']], params['y'])
            check_negative(sum)
            self.r[params['z']] = sum & 0xFFFF
            return 4

        instruction_table[0x42] = {
            'Mnemonic': 'ADD RX, RY, RZ',
            'execute': add_rz
        }
        ########################
        ### 5x - Subtraction ###
        def check_carry_sub(result):
            if self.__create_16bit_two_complement(result) < 0x0:
                self.flag_carry = 1
            else:
                self.flag_carry = 0

        def check_overflow_sub(result, operand1, operand2):
            result_is_positive = self.__create_16bit_two_complement(result) >= 0
            operand1_is_posivite = self.__create_16bit_two_complement(operand1) >= 0
            operand2_is_posivite = self.__create_16bit_two_complement(operand2) >= 0
            result_is_negative = not result_is_positive
            operand1_is_negative = not operand1_is_posivite
            operand2_is_negative = not operand2_is_posivite

            if (result_is_positive and operand1_is_negative and operand2_is_negative) or (result_is_negative and operand1_is_posivite and operand2_is_negative):
                self.flag_overflow = 1
            else:
                self.flag_overflow = 0

        def subi_rx(params):
            #Set RX to RX-HHLL.
            result = self.r[params['x']] - params['hhll']
            check_carry_sub(result)
            check_zero(result)
            check_overflow_sub(result, self.r[params['x']], params['hhll'])
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0x50] = {
            'Mnemonic': 'SUBI RX, HHLL',
            'execute': subi_rx
        }

        def sub_rx(params):
            #Set RX to RX-RY.
            result = self.r[params['x']] - self.r[params['y']]
            check_carry_sub(result)
            check_zero(result)
            check_overflow_sub(result, self.r[params['x']], self.r[params['y']])
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0x51] = {
            'Mnemonic': 'SUB RX, RY',
            'execute': sub_rx
        }

        def sub_rz(params):
            #Set RZ to RX-RY.
            result = self.r[params['x']] - self.r[params['y']]
            check_carry_sub(result)
            check_zero(result)
            check_overflow_sub(result, self.r[params['x']], self.r[params['y']])
            check_negative(result)
            self.r[params['z']] = result & 0xFFFF
            return 4

        instruction_table[0x52] = {
            'Mnemonic': 'SUB RX, RY, RZ',
            'execute': sub_rz
        }

        def sub_cmpi_rx(params):
            #Compute RX-HHLL, discard result.
            result = self.r[params['x']] - params['hhll']
            check_carry_sub(result)
            check_zero(result)
            check_overflow_sub(result, self.r[params['x']], params['hhll'])
            check_negative(result)
            return 4

        instruction_table[0x53] = {
            'Mnemonic': 'CMPI RX, HHLL',
            'execute': sub_cmpi_rx
        }

        def sub_cmpi_ry(params):
            #Compute RX-RY, discard result.
            result = self.r[params['x']] - self.r[params['y']]
            check_carry_sub(result)
            check_zero(result)
            check_overflow_sub(result, self.r[params['x']], self.r[params['y']])
            check_negative(result)
            return 4

        instruction_table[0x54] = {
            'Mnemonic': 'CMP RX, RY',
            'execute': sub_cmpi_ry
        }
        ########################
        ### 6x - Bitwise AND ###
        def andi(params):
            #Set RX to RX&HHLL.
            result = self.r[params['x']] & params['hhll']
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0x60] = {
            'Mnemonic': 'ANDI RX, HHLL',
            'execute': andi
        }

        def and_rx(params):
            #Set RX to RX&RY.
            result = self.r[params['x']] & self.r[params['y']]
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0x61] = {
            'Mnemonic': 'AND RX, RY',
            'execute': and_rx
        }

        def and_rz(params):
            #Set RZ to RX&RY.
            result = self.r[params['x']] & self.r[params['y']]
            check_zero(result)
            check_negative(result)
            self.r[params['z']] = result & 0xFFFF
            return 4

        instruction_table[0x62] = {
            'Mnemonic': 'AND RX, RY, RZ',
            'execute': and_rz
        }

        def tsti_rx(params):
            #Compute RX&HHLL, discard result.
            result = self.r[params['x']] & params['hhll']
            check_zero(result)
            check_negative(result)
            return 4

        instruction_table[0x63] = {
            'Mnemonic': 'TSTI RX, HHLL',
            'execute': tsti_rx
        }

        def tsti_ry(params):
            #Compute RX&RY, discard result.
            result = self.r[params['x']] & self.r[params['y']]
            check_zero(result)
            check_negative(result)
            return 4

        instruction_table[0x64] = {
            'Mnemonic': 'TST RX, RY',
            'execute': tsti_ry
        }
        ########################

        ########################
        ### 7x - Bitwise OR ###
        def ori_rx(params):
            #Set RX to RX|HHLL.
            result = self.r[params['x']] | params['hhll']
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0x70] = {
            'Mnemonic': 'ORI RX, HHLL',
            'execute': ori_rx
        }

        def or_ry(params):
            #Set RX to RX|RY.
            result = self.r[params['x']] | self.r[params['y']]
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0x71] = {
            'Mnemonic': 'OR RX, RY',
            'execute': or_ry
        }

        def or_rz(params):
            #Set RZ to RX|RY.
            result = self.r[params['x']] | self.r[params['y']]
            check_zero(result)
            check_negative(result)
            self.r[params['z']] = result & 0xFFFF
            return 4

        instruction_table[0x72] = {
            'Mnemonic': 'OR RX, RY, RZ',
            'execute': or_rz
        }
        ########################

        ########################
        ### 8x - Bitwise XOR ###
        def xori_rx(params):
            #Set RX to RX^HHLL.
            result = self.r[params['x']] ^ params['hhll']
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0x80] = {
            'Mnemonic': 'XORI RX, HHLL',
            'execute': xori_rx
        }

        def xor_ry(params):
            #Set RX to RX^RY.
            result = self.r[params['x']] ^ self.r[params['y']]
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0x81] = {
            'Mnemonic': 'XOR RX, RY',
            'execute': xor_ry
        }

        def xor_rz(params):
            #Set RZ to RX^RY.
            result = self.r[params['x']] ^ self.r[params['y']]
            check_zero(result)
            check_negative(result)
            self.r[params['z']] = result & 0xFFFF
            return 4

        instruction_table[0x82] = {
            'Mnemonic': 'XOR RX, RY, RZ',
            'execute': xor_rz
        }
        ########################

        ########################
        ### 9x - Multiplication ###
        def check_carry_mul(result):
            if result > 0xFFFF:
                self.flag_carry = 1
            else:
                self.flag_carry = 0

        def muli(params):
            #Set RX to RX*HHLL
            result = self.r[params['x']] * params['hhll']
            check_carry_mul(result)
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0x90] = {
            'Mnemonic': 'MULI RX, HHLL',
            'execute': muli
        }

        def mul_rx(params):
            #Set RX to RX*RY
            result = self.r[params['x']] * self.r[params['y']]
            check_carry_mul(result)
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0x91] = {
            'Mnemonic': 'MUL RX, RY',
            'execute': mul_rx
        }

        def mul_rz(params):
            #Set RZ to RX*RY
            result = self.r[params['x']] * self.r[params['y']]
            check_carry_mul(result)
            check_zero(result)
            check_negative(result)
            self.r[params['z']] = result & 0xFFFF
            return 4

        instruction_table[0x92] = {
            'Mnemonic': 'MUL RX, RY, RZ',
            'execute': mul_rz
        }
        ########################

        ########################
        ### Ax - Division ###
        def check_carry_div(operand1, operand2):
            reminder = operand1 % operand2
            if reminder != 0x0:
                self.flag_carry = 1
            else:
                self.flag_carry = 0

        def divi_rx(params):
            #Set RX to RX\HHLL
            result = self.r[params['x']] / params['hhll']
            check_carry_div(self.r[params['x']], params['hhll'])
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0xA0] = {
            'Mnemonic': 'DIVI RX, HHLL',
            'execute': divi_rx
        }

        def div_rx_ry(params):
            #Set RX to RX\RY
            result = self.r[params['x']] / self.r[params['y']]
            check_carry_div(self.r[params['x']], self.r[params['y']])
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0xA1] = {
            'Mnemonic': 'DIV RX, RY',
            'execute': div_rx_ry
        }

        def div_rx_rz(params):
            #Set RZ to RX\RY
            result = self.r[params['x']] / self.r[params['y']]
            check_carry_div(self.r[params['x']], self.r[params['y']])
            check_zero(result)
            check_negative(result)
            self.r[params['z']] = result & 0xFFFF
            return 4

        instruction_table[0xA2] = {
            'Mnemonic': 'DIV RX, RY, RZ',
            'execute': div_rx_rz
        }

        def mod_rx(params):
            #Set RX to RX MOD HHLL
            result = self.r[params['x']] % params['hhll']
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0xA3] = {
            'Mnemonic': 'MODI RX, HHLL',
            'execute': mod_rx
        }

        def mod_rx_ry(params):
            #Set RX to RX MOD RY
            result = self.r[params['x']] % self.r[params['y']]
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0xA4] = {
            'Mnemonic': 'MOD RX, RY',
            'execute': mod_rx_ry
        }

        def mod_rx_rz(params):
            #Set RZ to RX MOD RY
            result = self.r[params['x']] % self.r[params['y']]
            check_zero(result)
            check_negative(result)
            self.r[params['z']] = result & 0xFFFF
            return 4

        instruction_table[0xA5] = {
            'Mnemonic': 'MOD RX, RY, RZ',
            'execute': mod_rx_rz
        }

        instruction_table[0xA6] = {
            'Mnemonic': 'REMI RX, HHLL',
            'execute': mod_rx
        }

        instruction_table[0xA7] = {
            'Mnemonic': 'REM RX, RY',
            'execute': mod_rx_ry
        }

        instruction_table[0xA8] = {
            'Mnemonic': 'REM RX, RY, RZ',
            'execute': mod_rx_rz
        }
        ########################

        ########################
        ### Bx - Logical/Arithmetic Shifts ###
        def shl_rx(params):
            #Set RX to RX << N
            result = self.r[params['x']] << params['n']
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0xB0] = {
            'Mnemonic': 'SHL RX, N',
            'execute': shl_rx
        }

        def shr_rx(params):
            #Set RX to RX >> N
            result = self.r[params['x']] >> params['n']
            check_zero(result)
            check_negative(result)
            self.r[params['x']] = result & 0xFFFF
            return 4

        instruction_table[0xB1] = {
            'Mnemonic': 'SHR RX, N',
            'execute': shr_rx
        }

        instruction_table[0xB2] = {
            'Mnemonic': 'SAR RX, N',
            'execute': shr_rx
        }

        def shl_ry(params):
            #Set RY to RX << RY
            result = self.r[params['x']] << self.r[params['y']]
            check_zero(result)
            check_negative(result)
            self.r[params['y']] = result & 0xFFFF
            return 4

        instruction_table[0xB3] = {
            'Mnemonic': 'SHL RX, RY',
            'execute': shl_ry
        }

        def shr_ry(params):
            #Set RY to RX >> RY
            result = self.r[params['x']] >> self.r[params['y']]
            check_zero(result)
            check_negative(result)
            self.r[params['y']] = result & 0xFFFF
            return 4

        instruction_table[0xB4] = {
            'Mnemonic': 'SHR RX, RY',
            'execute': shr_ry
        }

        instruction_table[0xB5] = {
            'Mnemonic': 'SAR RX, RY',
            'execute': shr_ry
        }
        ########################

        ########################
        ### Cx - Push/Pop ###
        def push_rx(params):
            #Set [SP] to RX, increase SP by 2
            self.write_16bit(self.sp, self.r[params['x']])
            self.sp += 2
            return 4

        instruction_table[0xC0] = {
            'Mnemonic': 'PUSH RX',
            'execute': push_rx
        }

        def pop_rx(params):
            #Decrease SP by 2, set RX to [SP]
            self.sp -= 2
            self.r[params['x']] = self.read_16bit(self.sp)
            return 4

        instruction_table[0xC1] = {
            'Mnemonic': 'POP RX',
            'execute': pop_rx
        }

        def push_all(params):
            #Store R0..RF at [SP], increase SP by 32
            for x in range(0x0, 0xF + 1):
                push_rx({'x': x})
            return 4

        instruction_table[0xC2] = {
            'Mnemonic': 'PUSHALL',
            'execute': push_all
        }

        def pop_all(params):
            #Decrease SP by 32, load R0..RF from [SP]
            for x in reversed(range(0x0, 0xF + 1)):
                pop_rx({'x': x})
            return 4

        instruction_table[0xC3] = {
            'Mnemonic': 'POPALL',
            'execute': pop_all
        }

        def push_flags(params):
            #Set [SP] to FLAGS, increase SP by 2
            #[0,Carry,Zero,0,0,0,Overflow,Negative]
            flags = self.read_16bit(self.sp)
            self.flag_carry = (flags >> 1) & 1
            self.flag_zero = (flags >> 2) & 1
            self.flag_overflow = (flags >> 6) & 1
            self.flag_negative = (flags >> 7) & 1
            self.sp += 2
            return 4

        instruction_table[0xC4] = {
            'Mnemonic': 'PUSHF',
            'execute': push_flags
        }

        def pop_flags(params):
            #Decrease SP by 2, set FLAGS to [SP]
            #[0,Carry,Zero,0,0,0,Overflow,Negative]
            self.sp -= 2
            flags = (self.flag_carry << 1) & 0xFFFF
            flags = (self.flag_zero << 2) | flags
            flags = (self.flag_overflow << 6) | flags
            flags = (self.flag_negative << 7) | flags
            self.write_16bit(self.sp, flags)
            return 4

        instruction_table[0xC5] = {
            'Mnemonic': 'POPF',
            'execute': pop_flags
        }
        ########################

        ########################
        ### Dx - Palette ###
        ########################

        ########################
        ### Ex - Not/Neg ###
        ########################
        return instruction_table
