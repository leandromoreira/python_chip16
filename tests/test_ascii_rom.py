import sure
from pchip16 import loader
from pchip16.rom_chip16 import RomChip16
from pchip16.chip16 import Chip16

def test_few_steps():
    rom = RomChip16(loader.load("roms/ASCII.c16"))
    vm = Chip16(rom)
    for x in range(1,10):
        vm.step()

    vm.cpu.r[0xC].should.eql(0xAAAA)
    vm.cpu.r[0xA].should.eql(0xA)
    vm.cpu.r[0xB].should.eql(0xA)
    vm.cpu.pc.should.eql(0x0050)
