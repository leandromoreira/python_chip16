import sure
import loader
from rom_chip16 import RomChip16
from chip16 import Chip16

def test_few_steps():
    rom = RomChip16(loader.load("roms/ASCII.c16"))
    vm = Chip16(rom)
    vm.step()

    vm.cpu.pc.should.eql(0x0004)
    vm.cpu.memory[vm.cpu.pc].should.eql(0x04)


