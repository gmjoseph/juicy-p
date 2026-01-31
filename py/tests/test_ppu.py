from typing import Tuple

import pytest

from clock import Clock
from cpu import CPU
from io_db import IO_DB
from ppu import PPU


@pytest.fixture
def chips() -> Tuple[CPU, PPU]:
    bus = IO_DB()
    clock = Clock()
    cpu = CPU(bus=bus, clock=clock, oam=None)
    cpu.pc = 0xc000
    ppu = PPU(bus=bus, clock=clock, oam=None)
    return cpu, ppu


def test_PPUSCROLL_writes(chips):
    """
    Writing to this register is done using successive pushes/stores
    where the memory-mapped address is the target, for example:
    LDA $low_byte (immediate mode)
    STA 0x2005
    LDA $high_byte (immediate mode)
    STA 0x2005    
    Would result with PPUSCROLL holding the x and y values in the
    register.
    """
    cpu, ppu = chips

    # a9 be (LDA 0xba)
    # 8d 05 20 (STA 0x2005)
    # a9 ba (LDA 0xbe)
    # 8d 05 20 (STA 0x2005)
    assembly = bytearray([
        0xa9, 0xba,
        0x8d, 0x05, 0x20,
        0xa9, 0xbe,
        0x8d, 0x05, 0x20,
    ])
    cpu.memory.write_cpu_memory(assembly, 0xc000)

    cpu.next(
        pre_instruction_callback=ppu.before_cpu,
        post_instruction_callback=ppu.after_cpu,
    )
    assert ppu.PPUSCROLL != 0xbabe
    assert cpu.a == 0xba

    cpu.next(
        pre_instruction_callback=ppu.before_cpu,
        post_instruction_callback=ppu.after_cpu,
    )
    assert ppu._PPUSCROLL_pushes == 1
    assert ppu.PPUSCROLL == 0xba00
    assert ppu.scroll_x == 0xba
    assert ppu.scroll_y == 0x00

    cpu.next(
        pre_instruction_callback=ppu.before_cpu,
        post_instruction_callback=ppu.after_cpu,
    )
    assert cpu.a == 0xbe

    cpu.next(
        pre_instruction_callback=ppu.before_cpu,
        post_instruction_callback=ppu.after_cpu,
    )
    assert ppu._PPUSCROLL_pushes == 0
    assert ppu.PPUSCROLL == 0xbabe
    assert ppu.scroll_x == 0xba
    assert ppu.scroll_y == 0xbe


def test_PPUADDR_writes(chips):
    """
    Writing to this register is done using successive pushes/stores
    where the memory-mapped address is the target, for example:
    LDA $low_byte (immediate mode)
    STA 0x2006
    LDA $high_byte (immediate mode)
    STA 0x2006    
    Would result with PPUADDR holding a 16 bit address for PPU memory.
    """
    cpu, ppu = chips

    # a9 ba (LDA 0xba)
    # 8d 05 20 (STA 0x2006)
    # a9 be (LDA 0xbe)
    # 8d 05 20 (STA 0x2006)
    assembly = bytearray([
        0xa9, 0xba,
        0x8d, 0x06, 0x20,
        0xa9, 0xbe,
        0x8d, 0x06, 0x20,
    ])
    cpu.memory.write_cpu_memory(assembly, 0xc000)

    cpu.next(
        pre_instruction_callback=ppu.before_cpu,
        post_instruction_callback=ppu.after_cpu,
    )
    assert ppu.PPUADDR != 0xbabe
    assert cpu.a == 0xba

    cpu.next(
        pre_instruction_callback=ppu.before_cpu,
        post_instruction_callback=ppu.after_cpu,
    )
    assert ppu._PPUADDR_pushes == 1
    assert ppu.PPUADDR == 0xba00

    cpu.next(
        pre_instruction_callback=ppu.before_cpu,
        post_instruction_callback=ppu.after_cpu,
    )
    assert cpu.a == 0xbe

    cpu.next(
        pre_instruction_callback=ppu.before_cpu,
        post_instruction_callback=ppu.after_cpu,
    )
    assert ppu._PPUADDR_pushes == 0
    assert ppu.PPUADDR == 0xbabe
