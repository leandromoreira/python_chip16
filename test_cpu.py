import cpu
import sure
from mock import Mock


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
    chip16.write(initial_address + 1, 0x00) #x,y index operand
    chip16.write(initial_address + 2, 0xFF) #ll operand
    chip16.write(initial_address + 3, 0xAA) #hh operand

    chip16.r[0x0] = 0xDE
    chip16.write(0xAAFF, 0xCA)

    chip16.step()

    chip16.read(0xAAFF).should.eql(0xDE)
    chip16.current_cyles.should.eql(1)
    chip16.pc.should.eql(initial_address + 4)

def test_STM_RX_RY():
    # STM RX, RY
    chip16 = cpu.Cpu()
    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x31) #op code
    chip16.write(initial_address + 1, 0b00110000) #x,y index operand
    chip16.write(initial_address + 2, 0xFF) #ll operand
    chip16.write(initial_address + 3, 0xAA) #hh operand

    chip16.r[0] = 0xAA # sets r0(x) to 0xAA
    chip16.r[3] = 0x0007 # sets r3(y) pointing to 0x0007
    chip16.write(0x0007, 0x10) # place 0x10 to addressed pointed by y

    chip16.step()

    chip16.read(0x0007).should.eql(0xAA)
    chip16.current_cyles.should.eql(1)
    chip16.pc.should.eql(initial_address + 4)

def test_LDI_RX():
    # LDI RX, HHLL
    chip16 = cpu.Cpu()
    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x20) #op code
    chip16.write(initial_address + 1, 0b00010000) #x,y index operand
    chip16.write(initial_address + 2, 0xFF) #ll operand
    chip16.write(initial_address + 3, 0xAA) #hh operand

    chip16.step()

    chip16.r[0x00].should.eql(0xAAFF)
    chip16.current_cyles.should.eql(1)
    chip16.pc.should.eql(initial_address + 4)

def test_LDI_SP():
    # LDI SP, HHLL
    chip16 = cpu.Cpu()
    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x21) #op code
    chip16.write(initial_address + 1, 0b00010000) #x,y index operand
    chip16.write(initial_address + 2, 0xFF) #ll operand
    chip16.write(initial_address + 3, 0xAA) #hh operand

    chip16.step()

    chip16.sp.should.eql(0xAAFF)
    chip16.current_cyles.should.eql(1)
    chip16.pc.should.eql(initial_address + 4)

def test_LDM_RX():
    # LDM RX, HHLL
    chip16 = cpu.Cpu()
    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x22) #op code
    chip16.write(initial_address + 1, 0b00010010) #x,y index operand
    chip16.write(initial_address + 2, 0xFF) #ll operand
    chip16.write(initial_address + 3, 0xAA) #hh operand
    chip16.write(0xAAFF, 0xAB) # value for address pointed by hhll

    chip16.step()

    chip16.r[0b0010].should.eql(0xAB)
    chip16.current_cyles.should.eql(1)
    chip16.pc.should.eql(initial_address + 4)

def test_LDM_RX_RY():
    # LDM RX, RY - Set RX to [RY].
    chip16 = cpu.Cpu()
    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x23) #op code
    chip16.write(initial_address + 1, 0b00010010) #x,y index operand
    chip16.write(initial_address + 2, 0xFF) #ll operand
    chip16.write(initial_address + 3, 0xAA) #hh operand

    chip16.r[0b0010] = 0xAB
    chip16.r[0b0001] = 0xCD
    chip16.write(0x00CD, 0xEF)

    chip16.step()

    chip16.r[0b0010].should.eql(0xEF)
    chip16.current_cyles.should.eql(1)
    chip16.pc.should.eql(initial_address + 4)

def test_NOP():
    # NOP - No operation.
    chip16 = cpu.Cpu()
    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x00) #op code
    chip16.write(initial_address + 1, 0x00) #x,y index operand
    chip16.write(initial_address + 2, 0x00) #ll operand
    chip16.write(initial_address + 3, 0x00) #hh operand

    chip16.step()

    chip16.current_cyles.should.eql(1)
    chip16.pc.should.eql(initial_address + 4)

def test_CLS():
    # CLS - Clear FG, BG = 0.
    gpu = Mock()
    chip16 = cpu.Cpu()
    chip16.gpu = gpu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x01) #op code
    chip16.write(initial_address + 1, 0x00) #x,y index operand
    chip16.write(initial_address + 2, 0x00) #ll operand
    chip16.write(initial_address + 3, 0x00) #hh operand

    chip16.step()

    gpu.clear_fg.assert_called_once()
    gpu.clear_bg.assert_called_once()
    chip16.current_cyles.should.eql(1)
    chip16.pc.should.eql(initial_address + 4)

def test_VBLNK_when_it_is_disable():
    # VBLNK - Wait for VBlank. If (!vblank) PC -= 4.
    gpu = Mock()
    gpu.vblank = Mock(return_value=False)
    chip16 = cpu.Cpu()
    chip16.gpu = gpu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x02) #op code
    chip16.write(initial_address + 1, 0x00) #x,y index operand
    chip16.write(initial_address + 2, 0x00) #ll operand
    chip16.write(initial_address + 3, 0x00) #hh operand

    chip16.step()

    chip16.current_cyles.should.eql(1)
    chip16.pc.should.eql(initial_address)

def test_VBLNK_when_it_is_enable():
    # VBLNK - Wait for VBlank. If (!vblank) PC -= 4.
    gpu = Mock()
    gpu.vblank = Mock(return_value=True)
    chip16 = cpu.Cpu()
    chip16.gpu = gpu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x02) #op code
    chip16.write(initial_address + 1, 0x00) #x,y index operand
    chip16.write(initial_address + 2, 0x00) #ll operand
    chip16.write(initial_address + 3, 0x00) #hh operand

    chip16.step()

    chip16.current_cyles.should.eql(1)
    chip16.pc.should.eql(initial_address + 4)

def test_BGC():
    # BGC N - Set background color to index N (0 is black).
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x03) #op code
    chip16.write(initial_address + 1, 0x00) #x,y index operand
    chip16.write(initial_address + 2, 0b00000100) #ll operand
    chip16.write(initial_address + 3, 0x00) #hh operand

    chip16.step()

    chip16.current_cyles.should.eql(1)
    chip16.pc.should.eql(initial_address + 4)
    chip16.gpu.bg.should.eql(0b0100)

def test_SPR():
    # SPR HHLL - Set sprite width (LL) and height (HH).
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x04) #op code
    chip16.write(initial_address + 1, 0x00) #x,y index operand
    chip16.write(initial_address + 2, 0x21) #ll operand
    chip16.write(initial_address + 3, 0x42) #hh operand

    chip16.step()

    chip16.current_cyles.should.eql(1)
    chip16.pc.should.eql(initial_address + 4)
    chip16.gpu.spritew.should.eql(0x21)
    chip16.gpu.spriteh.should.eql(0x42)

def test_DRW_HHLL_with_no_overlaps():
    # Draw sprite from address HHLL at (RX, RY).
    gpu = Mock()
    gpu.there_is_overlap = Mock(return_value=False)
    gpu.drw_hhll = Mock(return_value=0)
    chip16 = cpu.Cpu()
    chip16.gpu = gpu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x05) #op code
    chip16.write(initial_address + 1, 0b00010010) #x,y index operand
    chip16.write(initial_address + 2, 0x21) #ll operand
    chip16.write(initial_address + 3, 0x42) #hh operand

    chip16.r[0b0001] = 0x10 #y
    chip16.r[0b0010] = 0x20 #x

    chip16.step()

    gpu.drw_hhll.assert_called_once_with(0x4221, 0x20, 0x10)
    chip16.flag_carry.should.eql(0x0)

def test_DRW_HHLL_with_overlaps():
    # Draw sprite from address HHLL at (RX, RY).
    gpu = Mock()
    gpu.there_is_overlap = Mock(return_value=True)
    gpu.drw_hhll = Mock(return_value=1)
    chip16 = cpu.Cpu()
    chip16.flag_carry = 0x0
    chip16.gpu = gpu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x05) #op code
    chip16.write(initial_address + 1, 0b00010010) #x,y index operand
    chip16.write(initial_address + 2, 0x21) #ll operand
    chip16.write(initial_address + 3, 0x42) #hh operand

    chip16.r[0b0001] = 0x10 #y
    chip16.r[0b0010] = 0x20 #x

    chip16.step()

    gpu.drw_hhll.assert_called_once_with(0x4221, 0x20, 0x10)
    chip16.flag_carry.should.eql(0x1)

def test_DRW_RZ_with_no_overlaps():
    # Draw sprite from [RZ] at (RX, RY).
    gpu = Mock()
    gpu.there_is_overlap = Mock(return_value=False)
    gpu.drw_rz = Mock(return_value=0)
    chip16 = cpu.Cpu()
    chip16.gpu = gpu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x06) #op code
    chip16.write(initial_address + 1, 0b00010010) #x,y index operand
    chip16.write(initial_address + 2, 0b00000011) #ll operand
    chip16.write(initial_address + 3, 0x42) #hh operand

    chip16.r[0b0001] = 0x10 #y
    chip16.r[0b0010] = 0x20 #x
    chip16.r[0b0011] = 0x4000 #z => pointing to address 0x4000

    chip16.write(0x4000, 0xAA)
    chip16.write(0x4001, 0xBB)

    chip16.step()

    # we need to compare both using 2's complement
    gpu.drw_rz.assert_called_once_with(chip16.create_16bit_two_complement(0xBBAA), 0x20, 0x10)
    chip16.flag_carry.should.eql(0x0)

def test_DRW_RZ_with_overlaps():
    # Draw sprite from [RZ] at (RX, RY).
    gpu = Mock()
    gpu.there_is_overlap = Mock(return_value=True)
    gpu.drw_rz = Mock(return_value=1)
    chip16 = cpu.Cpu()
    chip16.gpu = gpu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x06) #op code
    chip16.write(initial_address + 1, 0b00010010) #x,y index operand
    chip16.write(initial_address + 2, 0b00000011) #ll operand
    chip16.write(initial_address + 3, 0x42) #hh operand

    chip16.r[0b0001] = 0x10 #y
    chip16.r[0b0010] = 0x20 #x
    chip16.r[0b0011] = 0x4000 #z => pointing to address 0x4000

    chip16.write(0x4000, 0xAA)
    chip16.write(0x4001, 0xBB)

    chip16.step()

    # we need to compare both using 2's complement
    gpu.drw_rz.assert_called_once_with(chip16.create_16bit_two_complement(0xBBAA), 0x20, 0x10)
    chip16.flag_carry.should.eql(0x1)

def test_RND():
    # RND RX, HHLL - Store random number in RX (max. HHLL).
    chip16 = cpu.Cpu()
    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x07) #op code
    chip16.write(initial_address + 1, 0b00010010) #x,y index operand
    chip16.write(initial_address + 2, 0x10) #ll operand
    chip16.write(initial_address + 3, 0x01) #hh operand

    chip16.write(initial_address + 4, 0x07) #op code
    chip16.write(initial_address + 5, 0b00010010) #x,y index operand
    chip16.write(initial_address + 6, 0x05) #ll operand
    chip16.write(initial_address + 7, 0x00) #hh operand

    chip16.step()

    chip16.r[0b0010].should.be.lower_than_or_equal_to(0x110)

    chip16.step()

    chip16.r[0b0010].should.be.lower_than_or_equal_to(0x5)

def test_FLIP():
    # FLIP [0|1], [0|1] - Set hflip = [false|true], vflip = [false|true]
    chip16 = cpu.Cpu()
    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x08) #op code
    chip16.write(initial_address + 1, 0x0) #x,y index operand
    chip16.write(initial_address + 2, 0x0) #ll operand
    chip16.write(initial_address + 3, 0b00) #hh operand

    chip16.step()

    chip16.gpu.hflip.should.be.falsy
    chip16.gpu.vflip.should.be.falsy

    chip16.write(initial_address + 4, 0x08) #op code
    chip16.write(initial_address + 5, 0x0) #x,y index operand
    chip16.write(initial_address + 6, 0x0) #ll operand
    chip16.write(initial_address + 7, 0b01) #hh operand

    chip16.step()

    chip16.gpu.hflip.should.be.falsy
    chip16.gpu.vflip.should.be.truthy

    chip16.write(initial_address + 8, 0x08) #op code
    chip16.write(initial_address + 9, 0x0) #x,y index operand
    chip16.write(initial_address + 10, 0x0) #ll operand
    chip16.write(initial_address + 11, 0b11) #hh operand

    chip16.step()

    chip16.gpu.hflip.should.be.truthy
    chip16.gpu.vflip.should.be.truthy

def test_SND0():
    # Stop playing sounds.
    spu = Mock()
    chip16 = cpu.Cpu()
    chip16.spu = spu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x09) #op code
    chip16.write(initial_address + 1, 0x0) #x,y index operand
    chip16.write(initial_address + 2, 0x0) #ll operand
    chip16.write(initial_address + 3, 0x0) #hh operand

    chip16.step()

    spu.stop.assert_called_once()

def test_SND1():
    # Play 500Hz tone for HHLL ms.
    spu = Mock()
    chip16 = cpu.Cpu()
    chip16.spu = spu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x0A) #op code
    chip16.write(initial_address + 1, 0x0) #x,y index operand
    chip16.write(initial_address + 2, 0xBB) #ll operand
    chip16.write(initial_address + 3, 0x10) #hh operand

    chip16.step()

    spu.play500hz.assert_called_once_with(0x10BB)

def test_SND2():
    # Play 1000Hz tone for HHLL ms.
    spu = Mock()
    chip16 = cpu.Cpu()
    chip16.spu = spu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x0B) #op code
    chip16.write(initial_address + 1, 0x0) #x,y index operand
    chip16.write(initial_address + 2, 0xBB) #ll operand
    chip16.write(initial_address + 3, 0x10) #hh operand

    chip16.step()

    spu.play1000hz.assert_called_once_with(0x10BB)

def test_SND3():
    # Play 1500Hz tone for HHLL ms.
    spu = Mock()
    chip16 = cpu.Cpu()
    chip16.spu = spu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x0C) #op code
    chip16.write(initial_address + 1, 0x0) #x,y index operand
    chip16.write(initial_address + 2, 0xBB) #ll operand
    chip16.write(initial_address + 3, 0x10) #hh operand

    chip16.step()

    spu.play1500hz.assert_called_once_with(0x10BB)

def test_SNP():
    # Play tone from [RX] for HHLL ms.
    spu = Mock()
    chip16 = cpu.Cpu()
    chip16.spu = spu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x0D) #op code
    chip16.write(initial_address + 1, 0x0) #x,y index operand
    chip16.write(initial_address + 2, 0xBB) #ll operand
    chip16.write(initial_address + 3, 0x10) #hh operand

    chip16.r[0x0] = 0xFAFA # register x(0) pointing to 0xFAFA
    chip16.write(0xFAFA, 0xAD) # value at 0xFAFA memory location is 0xAD

    chip16.step()

    spu.play_tone.assert_called_once_with(0xAD, 0x10BB)

def test_SNG():
    # Set sound generation parameters.
    spu = Mock()
    chip16 = cpu.Cpu()
    chip16.spu = spu

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x0E) #op code
    chip16.write(initial_address + 1, 0x33) #AD
    chip16.write(initial_address + 2, 0xBB) #sr operand
    chip16.write(initial_address + 3, 0x10) #vt operand

    chip16.step()

    spu.setup.assert_called_once_with(0x33, 0x10BB)

def test_JMP():
    # Set PC to HHLL.
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x10) #op code
    chip16.write(initial_address + 1, 0x33) #AD
    chip16.write(initial_address + 2, 0xBB) #sr operand
    chip16.write(initial_address + 3, 0x10) #vt operand

    chip16.step()

    chip16.pc.should.be.eql(0x10BB)

def test_JMPx():
    #f x, then perform a JMP.
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x12) #op code
    chip16.write(initial_address + 1, 0x00) #y,x
    chip16.write(initial_address + 2, 0xBB) #hh
    chip16.write(initial_address + 3, 0x10) #ll

    chip16.write(initial_address + 4, 0x12) #op code
    chip16.write(initial_address + 5, 0b00000001) #y,x
    chip16.write(initial_address + 6, 0xBB) #hh
    chip16.write(initial_address + 7, 0x10) #ll

    chip16.step()

    chip16.pc.should.be.eql(initial_address + 4)

    chip16.step()

    chip16.pc.should.be.eql(0x10BB)

def test_JME():
    #Set PC to HHLL if RX == RY.
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x13) #op code
    chip16.write(initial_address + 1, 0b00010010) #y,x
    chip16.write(initial_address + 2, 0xBB) #hh
    chip16.write(initial_address + 3, 0x10) #ll

    chip16.r[1] = chip16.r[2] = 0xF

    chip16.step()

    chip16.pc.should.be.eql(0x10BB)

def test_CALL():
    # Store PC to [SP], increase SP by 2, set PC to HHLL.
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x14) #op code
    chip16.write(initial_address + 1, 0x00) #y,x
    chip16.write(initial_address + 2, 0xBB) #hh
    chip16.write(initial_address + 3, 0x10) #ll

    chip16.step()

    chip16.sp.should.be.eql(chip16.STACK_START + 2)
    chip16.read(chip16.sp - 2).should.be.eql(initial_address + 4)
    chip16.pc.should.be.eql(0x10BB)

def test_RET():
    # Decrease SP by 2, set PC to [SP].
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x14) #op code
    chip16.write(initial_address + 1, 0x00) #y,x
    chip16.write(initial_address + 2, 0xBB) #hh
    chip16.write(initial_address + 3, 0x10) #ll

    chip16.write(0x10BB + 0, 0x15)
    chip16.write(0x10BB + 1, 0x0)
    chip16.write(0x10BB + 2, 0x0)
    chip16.write(0x10BB + 3, 0x0)

    chip16.step()

    chip16.sp.should.be.eql(chip16.STACK_START + 2)
    chip16.read(chip16.sp - 2).should.be.eql(initial_address + 4)
    chip16.pc.should.be.eql(0x10BB)

    chip16.step()

    chip16.pc.should.be.eql(initial_address + 4)

def test_JMP_RX():
    #Set PC to RX.
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x16) #op code
    chip16.write(initial_address + 1, 0x00) #y,x
    chip16.write(initial_address + 2, 0x00) #hh
    chip16.write(initial_address + 3, 0x00) #ll

    chip16.r[0x0] = 0xFACA

    chip16.step()

    chip16.pc.should.be.eql(0xFACA)

def test_CALL_x():
    #If x, then perform a CALL.
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x17) #op code
    chip16.write(initial_address + 1, 0b00000001) #y,x
    chip16.write(initial_address + 2, 0xFA) #ll
    chip16.write(initial_address + 3, 0xCA) #hh

    chip16.step()

    chip16.pc.should.be.eql(0xCAFA)

def test_CALL_rx():
    #Store PC to [SP], increase SP by 2, set PC to RX.
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x18) #op code
    chip16.write(initial_address + 1, 0b00000001) #y,x
    chip16.write(initial_address + 2, 0xFA) #ll
    chip16.write(initial_address + 3, 0xCA) #hh

    chip16.r[0x1] = 0xFACA

    chip16.step()

    chip16.pc.should.be.eql(0xFACA)
    chip16.sp.should.be.eql(chip16.STACK_START + 2)
    chip16.read(chip16.sp - 2).should.be.eql(initial_address + 4)

def test_ADDI_rx():
    #Set RX to RX+HHLL.
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x40) #op code
    chip16.write(initial_address + 1, 0b00000001) #y,x
    chip16.write(initial_address + 2, 0x03) #ll
    chip16.write(initial_address + 3, 0x00) #hh

    chip16.r[0x1] = 0x3

    chip16.step()

    chip16.r[0x1].should.be.eql(0x6)

def test_ADD_rx():
    #Set RX to RX+RY.
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x41) #op code
    chip16.write(initial_address + 1, 0b00100001) #y,x
    chip16.write(initial_address + 2, 0x03) #ll
    chip16.write(initial_address + 3, 0x00) #hh

    chip16.r[0x1] = 0x3
    chip16.r[0x2] = 0x5

    chip16.step()

    chip16.r[0x1].should.be.eql(0x8)

def test_ADD_rz():
    #Set RZ to RX+RY.
    chip16 = cpu.Cpu()

    initial_address = 0x0000
    chip16.pc = initial_address

    chip16.write(initial_address, 0x42) #op code
    chip16.write(initial_address + 1, 0b00100001) #y,x
    chip16.write(initial_address + 2, 0b00000011) #ll
    chip16.write(initial_address + 3, 0x00) #hh

    chip16.r[0x1] = 0x2
    chip16.r[0x2] = 0x5

    chip16.step()

    chip16.r[0x3].should.be.eql(0x7)
