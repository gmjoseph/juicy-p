from pathlib import Path

import pytest

from nes import NES


def _parse_log_entry(entry: str) -> dict:
    # TODO
    # For now just grab the address, register states, and cycles
    # for the CPU. In future we can look at instructions, operands
    # and opcode bytes, as well as PPU.
    entry = entry.rstrip('\n')
    pc = int(entry[0:4], base=16)
    a = int(entry[50:52], base=16)
    x = int(entry[55:57], base=16)
    y = int(entry[60:62], base=16)
    p = int(entry[65:67], base=16)
    sp = int(entry[71:73], base=16)
    ppu_cycles = int(entry[78:81])
    scanline = int(entry[82:85])
    cpu_cycles = int(entry[90:len(entry)])

    return {
        'pc': pc,
        'a': a,
        'x': x,
        'y': y,
        'p': p,
        'sp': sp,
        'ppu_cycles': ppu_cycles,
        'scanline': scanline,
        'cpu_cycles': cpu_cycles,
    }

def test_nestest():
    """
    Runs the nestest ROM, comparing the CPU and memory states
    to the nestest.log. This tests the CPU directly without looking
    at the PPU at all.
    """

    rom_path = Path(__file__).parent.joinpath('../roms/nestest/nestest.nes')
    log_path = Path(__file__).parent.joinpath('../roms/nestest/nestest.log')

    with open(log_path) as file:
        log_entries = [_parse_log_entry(line) for _, line in enumerate(file)]

    nes = NES(rom_path)
    # Start here, not where the RESET vector says.
    nes.cpu.pc = 0xc000

    for i, entry in enumerate(log_entries):
        assert nes.cpu.a == entry['a']
        assert nes.cpu.x == entry['x']
        assert nes.cpu.y == entry['y']
        assert nes.cpu.p == entry['p']
        assert nes.cpu.pc == entry['pc']
        assert nes.cpu.sp == entry['sp']
        assert nes.cpu._clock.cpu_cycles == entry['cpu_cycles']
        assert nes.ppu._clock.ppu_cycles == entry['ppu_cycles']
        assert nes.ppu.scanline == entry['scanline']

        # We're always 1 behind cpu.next i believe, so if we run into
        # an error on an entry it's because the previous instruction
        # failed and as a result this entry's state isn't what the
        # last instruction should've caused.
        nes.run()
