import sys
from pathlib import Path

from clock import Clock
from io_db import IO_DB
from ppu import PPU
from ppu import _colour_for_pixel


def renderer():
    # PPU memory should already be loaded with data.
    clock = Clock()
    bus = IO_DB()
    ppu = PPU(clock=clock, bus=bus, oam=None)

    path_and_memory_location = [
        ('../roms/donkey_kong/donkey_kong_nametable.bin', 0x2000, 0x2400),
        ('../roms/donkey_kong/donkey_kong_palette.bin', 0x3f00, 0x3f20),
        ('../roms/donkey_kong/donkey_kong_pattern.bin', 0x0, 0x2000),
    ]
    
    for p, start, _ in path_and_memory_location:
        path = Path(__file__).parent.joinpath(p)
        with open(path, 'rb') as f:
            data = f.read()
            ppu.memory.write_ppu_memory(data, start)

    # Force the clock to be on the first cycle so it
    # starts to compute pixels immediately on _cycle().
    clock.ppu_cycles = 1

    # Use the 0x1000+ pattern table.
    ppu._PPUCTRL = 0x10

    # Now the PPU's pixel buffer should be full of data. I think
    # it's pretty limited for now so we can just do our lookups like
    # this.
    lut = {
        # Black
        0x0f: 0,
        # Dark blue
        0x12: 26,
        # Pink?
        0x25: 207,
        # Orange
        0x27: 208,
        # Light blue
        0x2c: 45,
        # White
        0x30: 15,
        # Brownish
        0x38: 173,
    }

    while ppu._frames < 1:
        # Need to call these manually because using ppu.next() will run it
        # in a loop based on the amount of ppu_cycles_next from the clock
        # which won't let it output all we need per-pixel.
        ppu._cycle()
        ppu._post_cycle()

    print()
    for i, p in enumerate(ppu._pixels):
        if p not in lut:
            raise Exception(
                f"Attempting to output a colour that isn't in the LUT {hex(p)}"
            )
        code = str(lut[p])
        sys.stdout.write(u"\u001b[38;5;" + code + "m" + '■ ')
        sys.stdout.flush()
        if i > 0 and i % 256 == 0:
            sys.stdout.write('\n')
            sys.stdout.flush()
    print()

if __name__ == "__main__":
    renderer()
