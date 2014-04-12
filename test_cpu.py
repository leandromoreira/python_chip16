import cpu
import sure


def test_little_endianess():
    chip16 = cpu.Cpu()

    chip16.write(0x000,0xFFAA)

    chip16.memory[0x000].should.eql(0x00AA)
    chip16.memory[0x001].should.eql(0x00FF)

    hex(chip16.read(0x000)).should.eql("0xffaa")

