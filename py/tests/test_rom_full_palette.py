from pathlib import Path

import pytest

from nes import NES


@pytest.mark.skip
def test_full_palette():
    rom_path = Path(__file__).parent.joinpath(
        '../roms/full_palette/full_palette.nes'
    )

    nes = NES(rom_path)
    # Looks like this doesn't start from the RESET vector.
    nes.cpu.pc = 0xc000
    # for _ in range(10000):
    # This also works, it's just that we'll never leave the test.
    while True:
        nes.run()
        # At cpu_cycles of ~58859 we should start getting
        # some usable colour data in the nametable and
        # attribute tables.
        # The PPUADDR is also at 0x4000 i imagine by that
        # point because the CPU finished filling the buffers...?

    # TODO
    # Writes 0xf to 3fe0 in PPU memory assert that it is there 0x20 (32)
    # times.
    # TODO
    # Assert something about the PPU state (memroy, registers, etc.?)
    assert False
