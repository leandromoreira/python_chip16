import sure
import loader
from rom_chip16 import RomChip16


def test_integration_load_rom():
    rom = RomChip16(loader.load("roms/ASCII.c16"))

    rom.magic_number.should.eql("CH16")
    rom.spec_version.should.eql(0x11)
    rom.program_start.should.eql(0x0000)
    rom.crc32.should.eql(0x390d4da6)
    len(rom.rom).should.eql(rom.size)

