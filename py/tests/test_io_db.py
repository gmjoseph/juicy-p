import pytest

from constants import PPUAddress
from constants import ReadMnemonic
from constants import WriteMnemonic
from clock import Clock
from cpu import CPU
from io_db import IO_DB
from ppu import PPU


# TODO
# BIT is special in that it doesn't actually update a register.
# So in this case, we expect the registers to be unchanged from
# their defaults. Therefore, while the BIT operation can result
# in a read from a PPU register, it's hard to test because the
# value is then read internally in the op_BIT function.
# MagicMocks would work here to test certain calls in that
# function.

# Seed the CPU registers with values we can check the bus for.
# TODO
# Do this on 'READ' from PPU registers as well.
_IO_A = 0xff
_IO_X = 0xba
_IO_Y = 0xbe

# What data do we expect to be on the bus for write mnemonics
# going from CPU to PPU.
_BUS_DATA_FOR_MNEMONIC = {
    WriteMnemonic.STA: _IO_A,
    WriteMnemonic.STX: _IO_X,
    WriteMnemonic.STY: _IO_Y,
}


def _assemble(mnemonic, address) -> bytearray:
    """
    Assemble the mnemonic and address into bytecode
    """
    # Assuming ABSOLUTE addressing for each of these
    mnemonic_to_opcode = {
        ReadMnemonic.LDA: 0xad,
        ReadMnemonic.LDX: 0xae,
        ReadMnemonic.LDY: 0xac,
        ReadMnemonic.BIT: 0x2c,
        WriteMnemonic.STA: 0x8d, 
        WriteMnemonic.STX: 0x8e,
        WriteMnemonic.STY: 0x8c,
    }

    opcode = mnemonic_to_opcode[mnemonic]
    high = address >> 0x8
    low = address & 0xff

    # Little endian
    return bytearray([opcode, low, high])


@pytest.fixture
def bus() -> IO_DB:
    return IO_DB()


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def cpu(bus: IO_DB, clock: Clock) -> CPU:
    c = CPU(bus=bus, clock=clock, oam=None)
    c.pc = 0xc000
    c.a = _IO_A
    c.x = _IO_X
    c.y = _IO_Y
    return c


@pytest.fixture
def ppu(bus: IO_DB, clock: Clock) -> PPU:
    return PPU(bus=bus, clock=clock, oam=None)


# Fully parametrized tests don't work well because not all addresses
# are supported. Compounding that, there are very different behaviours
# to expect when writing to certain PPU registers. As a result they
# need to be tested semi-discretely.

@pytest.mark.parametrize('mnemonic', WriteMnemonic)
def test_cpu_writes_to_PPUCTRL(cpu, ppu, mnemonic):
    """
    Ensures that the CPU register data ends up in PPUCTRL
    """
    assembly = _assemble(mnemonic, PPUAddress.PPUCTRL_ADDRESS)
    cpu.memory.write_cpu_memory(assembly, cpu.pc)
    # E.g. if it's STA we'll put the cpu's 'a' value into whichever
    # PPU register it is. So if the argument is PPUCTRL we should
    # expect the cpu.a == ppu.PPUCTRL
    data_from_cpu = _BUS_DATA_FOR_MNEMONIC[mnemonic]
    assert not cpu._bus.has_data
    assert ppu.PPUCTRL != data_from_cpu

    # PPU can only read from the bus after the CPU instruction
    # finished writing.
    cpu.next(post_instruction_callback=ppu.after_cpu)
    assert not cpu._bus.has_data
    assert ppu.PPUCTRL == data_from_cpu


@pytest.mark.parametrize('mnemonic', WriteMnemonic)
def test_cpu_writes_to_PPUMASK(cpu, ppu, mnemonic):
    """
    Ensures that the CPU register data ends up in PPUMASK
    """
    assembly = _assemble(mnemonic, PPUAddress.PPUMASK_ADDRESS)
    cpu.memory.write_cpu_memory(assembly, cpu.pc)
    data_from_cpu = _BUS_DATA_FOR_MNEMONIC[mnemonic]
    assert ppu.PPUMASK != data_from_cpu
    assert not cpu._bus.has_data

    # PPU can only read from the bus after the CPU instruction
    # finished writing.
    cpu.next(post_instruction_callback=ppu.after_cpu)
    assert not cpu._bus.has_data
    assert ppu.PPUMASK == data_from_cpu


@pytest.mark.parametrize('mnemonic', WriteMnemonic)
def test_cpu_writes_to_PPUADDR(cpu, ppu, mnemonic):
    """
    PPUADDR is special in that it takes two writes to it and builds
    up an address for where we are in PPU memory.
    """
    first_instruction = _assemble(mnemonic, PPUAddress.PPUADDR_ADDRESS)
    second_instruction = _assemble(mnemonic, PPUAddress.PPUADDR_ADDRESS)
    assembly = first_instruction + second_instruction
    cpu.memory.write_cpu_memory(assembly, cpu.pc)
    assert not cpu._bus.has_data

    # Two instructions to write the entire address to the register.
    cpu.next(post_instruction_callback=ppu.after_cpu)
    assert not cpu._bus.has_data

    cpu.next(post_instruction_callback=ppu.after_cpu)
    assert not cpu._bus.has_data

    high = _BUS_DATA_FOR_MNEMONIC[mnemonic] << 8
    low = _BUS_DATA_FOR_MNEMONIC[mnemonic]
    expected_address = high + low
    assert ppu.PPUADDR == expected_address


@pytest.mark.parametrize('mnemonic', WriteMnemonic)
def test_cpu_writes_to_PPUDATA(cpu, ppu, mnemonic):
    """
    PPUDATA is special in that it takes the data that's given to
    it over the bus and then puts it into memory based on PPUADDR.
    It also needs to read from PPUSTATUS first. Lastly, it
    increments PPUADDR.
    """
    assembly = _assemble(mnemonic, PPUAddress.PPUDATA_ADDRESS)
    cpu.memory.write_cpu_memory(assembly, cpu.pc)
    assert not cpu._bus.has_data

    start_address = ppu.PPUADDR
    cpu.next(post_instruction_callback=ppu.after_cpu)
    assert not cpu._bus.has_data
    assert ppu.PPUADDR == start_address + 1

    data_in_memory = ppu.memory.read_one(start_address)
    data_from_cpu = _BUS_DATA_FOR_MNEMONIC[mnemonic]
    assert data_in_memory == data_from_cpu


@pytest.mark.parametrize(('mnemonic', 'register'), [
    (ReadMnemonic.LDA, 'a'),
    (ReadMnemonic.LDX, 'x'),
    (ReadMnemonic.LDY, 'y'),
])
def test_cpu_reads_from_PPUSTATUS(cpu, ppu, mnemonic, register):
    """
    Reads from PPU registers put the right value in the right CPU register.
    """
    assembly = _assemble(mnemonic, PPUAddress.PPUSTATUS_ADDRESS)
    cpu.memory.write_cpu_memory(assembly, cpu.pc)
    assert not cpu._bus.has_data
    assert ppu.PPUSTATUS != getattr(cpu, register)

    cpu.next(pre_instruction_callback=ppu.before_cpu)
    assert not cpu._bus.has_data
    assert ppu.PPUSTATUS == getattr(cpu, register)


def test_cpu_BIT_from_PPUSTATUS(cpu, ppu):
    """
    BIT is special because it only uses the value from the PPU register
    internally for calculations.
    """
    assembly = _assemble(ReadMnemonic.BIT, PPUAddress.PPUSTATUS_ADDRESS)
    cpu.memory.write_cpu_memory(assembly, cpu.pc)
    # Start state of the register before it gets modified by BIT
    assert cpu.p == 0x24
    assert not cpu._bus.has_data

    cpu.next(post_instruction_callback=ppu.after_cpu)
    assert not cpu._bus.has_data
    # TODO
    # Need to check this given differing PPUSTATUS data just to
    # be sure it's all working.
    assert cpu.p == 0x26
