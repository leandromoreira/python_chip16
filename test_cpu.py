import cpu
import sure


def test_little_endianess():
    chip16 = cpu.Cpu()

    chip16.write(0x0000,0x00AA)

    chip16.memory[0x0000].should.eql(0x00AA)
    chip16.memory[0x0001].should.eql(0x0000)

    hex(chip16.read(0x0000)).should.eql("0xaa")

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
    chip16.write(0x0000, minus_one)

    chip16.register_r(0x0).should.eql(-1)
    chip16.register_pc().should.eql(-1)
    chip16.register_sp().should.eql(-1)
    chip16.read(0x0000).should.eql(-1)

def test_create_params():
    # 40 YX LL HH
    chip16 = cpu.Cpu()

    op_code = 0x40
    yx = 0b00010010 #y=1, x=2
    ll = 0b00000001
    hh = 0b00000010

    chip16.write(0x0000, op_code)
    chip16.write(0x0001, yx)
    chip16.write(0x0002, ll)
    chip16.write(0x0003, hh)

    params = chip16.create_params(0x0000)

    params['op_code'].should.eql(0x40)
    params['x'].should.eql(2)
    params['y'].should.eql(1)
    params['ll'].should.eql(1)
    params['hh'].should.eql(2)
    params['hhll'].should.eql(0b0000001000000001)

def test_STM_RX():
    # STM RX, HHLL
    chip16 = cpu.Cpu()
    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x30) #op code
    chip16.write(initial_address + 1, 0x00) #x index operand
    chip16.write(initial_address + 2, 0xFF) #ll operand
    chip16.write(initial_address + 3, 0xAA) #hh operand

    chip16.write(0xAAFF, 0xCA)

    chip16.step()

    chip16.register_r(0x00).should.eql(0xCA)
    chip16.current_cyles.should.eql(1)

