import sure
import loader
from rom_chip16 import RomChip16
from chip16 import Chip16

def test_few_steps():
    rom = RomChip16(loader.load("roms/ASCII.c16"))
    vm = Chip16(rom)
    vm.cpu.print_state()
    vm.gpu.print_state()
    vm.step()
    vm.step()
    vm.step()
    vm.step()
    vm.step()
    vm.step()
    vm.cpu.print_state()
    vm.gpu.print_state()

    vm.cpu.r[0xC].should.eql(0xAAAA)

