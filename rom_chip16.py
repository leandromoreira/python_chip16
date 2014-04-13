class RomChip16:
    def __init__(self, rom):
        self.magic_number = chr(rom[0]) + chr(rom[1]) + chr(rom[2]) + chr(rom[3])
        self.reserved = rom[4]
        self.spec_version = rom[5]
        self.size = (rom[9] << 24) | (rom[8] << 16) | (rom[7] << 8) | rom[6]
        self.program_start = (rom[11] << 8) | rom[10]
        self.crc32 = (rom[15] << 24) | (rom[14] << 16) | (rom[13] << 8) | rom[12]
        self.rom = rom[16:]

    def __repr__(self):
        return "<RomChip16 { %s, version=%s, size=%s, start=%s (CRC32=%s) }>" % (self.magic_number, hex(self.spec_version), self.size, hex(self.program_start), hex(self.crc32))
