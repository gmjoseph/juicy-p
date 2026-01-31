import pytest

from clock import Clock
from cpu import CPU
from io_db import IO_DB
from oam import OAM
from ppu import PPU


@pytest.mark.parametrize('opcodes', [
    # a9 02 (LDA 0x02)
    # 8d 14 40 (STA 0x4014)
    [
        0xa9, 0x02,
        0x8d, 0x14, 0x40,
    ],
    # a2 02 (LDX 0x02)
    # 8e 14 40 (STX 0x4014)
    [
        0xa2, 0x02,
        0x8e, 0x14, 0x40,
    ],
    # a0 02 (LDY 0x02)
    # 8c 14 40 (STY 0x4014)
    [
        0xa0, 0x02,
        0x8c, 0x14, 0x40,
    ],
])
def test_oam(opcodes):
    # TODO
    # Init CPU with memory at 0x0200 -> 0x02ff
    # Ensure that STA/STX/STY on 0x4014 will copy
    # all that to OAM.
    # TODO
    # Once that's done, remove OAMDMA port

    bus = IO_DB()
    clock = Clock()
    oam = OAM()

    cpu = CPU(bus=bus, clock=clock, oam=oam)
    ppu = PPU(bus=bus, clock=clock, oam=oam)
    # Ensure that they use the same reference.
    assert cpu._oam is ppu._oam

    assembly = bytearray(opcodes)
    cpu.memory.write_cpu_memory(assembly, 0xc000)
    cpu.pc = 0xc000

    # Add some bytes
    oam_data = [0xca, 0xfe, 0xba, 0xbe]
    for i, d in enumerate(oam_data):
        cpu.memory.write(d, 0x0200 + i)
        assert ppu._oam._memory[i] != d

    cpu.next(
        pre_instruction_callback=ppu.before_cpu,
        post_instruction_callback=ppu.after_cpu,
    )
    cpu.next(
        pre_instruction_callback=ppu.before_cpu,
        post_instruction_callback=ppu.after_cpu,
    )

    # At this point the memory should've bene transferred over
    # to PPU OAM memory.
    for i, d in enumerate(oam_data):
        assert ppu._oam._memory[i] == d
