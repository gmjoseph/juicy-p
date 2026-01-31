from pathlib import Path

import pytest

from clock import Clock
from io_db import IO_DB
from oam import OAM
from ppu import PPU
from ppu_utils import _background_colour_for_pixel


def test_title_frame():
    """
    Uses the title screen of Donkey Kong as a seed for the memory
    of the nametable, pattern table, attribute table and palettes
    to produce one single frame in colour.
    """
    # TODO
    # Add the OAM dump and render the sprite as well.
    clock = Clock()
    ppu = PPU(clock=clock, bus=IO_DB(), oam=OAM())

    path_and_memory_location = [
        ('../roms/donkey_kong/donkey_kong_title_nametable.bin', 0x2000, 0x2400),
        ('../roms/donkey_kong/donkey_kong_title_palette.bin', 0x3f00, 0x3f20),
        ('../roms/donkey_kong/donkey_kong_title_pattern.bin', 0x0, 0x2000),
    ]
    
    for p, start, _ in path_and_memory_location:
        path = Path(__file__).parent.joinpath(p)
        with open(path, 'rb') as f:
            data = f.read()
            ppu.memory.write_ppu_memory(data, start)

    # Force the PPU to run some number of cycles.
    clock.ppu_cycles_next = 10000
    # Use the 0x1000+ pattern table.
    ppu._PPUCTRL = 0x10

    while ppu._frames < 1:
        ppu.next()

    # TODO
    # It should've written a frame to disk but it helps to confirm
    # that the pixel buffer was filled with the right contents and
    # can be compared to a hash of the contents.
    # import hashlib
    # m = hashlib.md5()
    # m.update(bytearray(128).decode('latin-1'))


def test_demo_frame():
    """
    Uses the demo screen of Donkey Kong as a seed for the memory
    of the nametable, pattern table, attribute table and palettes
    to produce one single frame in colour.
    """
    clock = Clock()
    ppu = PPU(clock=clock, bus=IO_DB(), oam=OAM())

    path_and_memory_location = [
        ('../roms/donkey_kong/donkey_kong_demo_nametable.bin', 0x2000, 0x2400),
        ('../roms/donkey_kong/donkey_kong_demo_palette.bin', 0x3f00, 0x3f20),
        ('../roms/donkey_kong/donkey_kong_demo_pattern.bin', 0x0, 0x2000),
    ]

    for p, start, _ in path_and_memory_location:
        path = Path(__file__).parent.joinpath(p)
        with open(path, 'rb') as f:
            data = f.read()
            ppu.memory.write_ppu_memory(data, start)

    # Force the PPU to run some number of cycles.
    clock.ppu_cycles_next = 10000
    # Use the 0x1000+ pattern table.
    ppu._PPUCTRL = 0x10

    while ppu._frames < 1:
        ppu.next()


@pytest.mark.parametrize(
    ('x', 'y', 'expected_colour'),
    [
        (12, 0, 0xf),
        (126, 23, 0x2c),
        (0, 0, 0xf),
        (255, 239, 0x2c),
        (128, 120, 0xf),
        (56, 120, 0xf),
        (72, 128, 0xf),
        (83, 200, 0xf),
        (83, 204, 0xf),
        (83, 214, 0x30),
    ]
)
def test_ppu_background_colour_for_pixel(x, y, expected_colour):
    """
    For a combo of x, y pixel inputs and the PPU memory dumps,
    test whether the right palette byte was given back.
    """
    clock = Clock()
    ppu = PPU(clock=clock, bus=IO_DB(), oam=OAM())

    path_and_memory_location = [
        ('../roms/donkey_kong/donkey_kong_title_nametable.bin', 0x2000, 0x2400),
        ('../roms/donkey_kong/donkey_kong_title_palette.bin', 0x3f00, 0x3f20),
        ('../roms/donkey_kong/donkey_kong_title_pattern.bin', 0x0, 0x2000),
    ]

    for p, start, _ in path_and_memory_location:
        path = Path(__file__).parent.joinpath(p)
        with open(path, 'rb') as f:
            data = f.read()
            ppu.memory.write_ppu_memory(data, start)

    colour = _background_colour_for_pixel(ppu, x, y, use_cache=False)
    assert colour == expected_colour
