import cpu
import sure


def test_little_endianess():
    chip16 = cpu.Cpu()

    chip16.write(0x000,0xFFAA)

    chip16.memory[0x000].should.eql(0x00AA)
    chip16.memory[0x001].should.eql(0x00FF)

    hex(chip16.read(0x000)).should.eql("0xffaa")

def test_program_counter():
    chip16 = cpu.Cpu()

    chip16.pc = 0xCAFE

    chip16.pc.should.eql(0xCAFE)

def test_stack_pointer():
    chip16 = cpu.Cpu()

    chip16.sp = 0xCAFE

    chip16.sp.should.eql(0xCAFE)

def test_general_registers():
    chip16 = cpu.Cpu()

    for r in range(0x0,0xF):
        chip16.r[r] = 0x00FA

    chip16.r[0x0].should.eql(0x00FA)
    chip16.r[0xF-1].should.eql(0x00FA)

def test_two_complements():
    chip16 = cpu.Cpu()

    minus_one = 0xFFFF

    chip16.r[0x0] = minus_one
    chip16.pc = minus_one
    chip16.sp = minus_one

    chip16.register_r(0x0).should.eql(-1)
    chip16.register_pc().should.eql(-1)
    chip16.register_sp().should.eql(-1)

