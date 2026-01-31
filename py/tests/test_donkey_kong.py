from pathlib import Path

import pytest

from nes import NES


def test_donkey_kong():
    rom_path = Path(__file__).parent.joinpath(
        '../roms/donkey_kong/donkey_kong.nes'
    )

    nes = NES(rom_path)
    # Running for 5 frames is enough to get to the title screen,
    # which should be good enough as a test so far.
    while nes.ppu._frames < 5:
        nes.run()
