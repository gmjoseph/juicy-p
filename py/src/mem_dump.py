import struct
from typing import Any


def dump_ppu_nametable_and_attribute(ppu: Any) -> None:

    with open('dump_ppu_nametable_and_attribute.bin', 'wb') as f:
        for b in ppu.memory._ppu_memory[0x2000:0x2400]:
            as_byte = struct.pack('B', b)
            f.write(as_byte)


def dump_ppu_palettes(ppu: Any) -> None:

    with open('dump_ppu_palettes.bin', 'wb') as f:
        for b in ppu.memory._ppu_memory[0x3f00:0x3f20]:
            as_byte = struct.pack('B', b)
            f.write(as_byte)


def dump_ppu_patterns(ppu: Any) -> None:

    with open('dump_ppu_patterns.bin', 'wb') as f:
        for b in ppu.memory._ppu_memory[0x0:0x2000]:
            as_byte = struct.pack('B', b)
            f.write(as_byte)


def create_patterns_viz(ppu: Any) -> None:
    grid = []
    row = 0
    i = 0

    # 32 patterns per row of 8 pixels each, once we can divide i
    # by this with no remainder it's time to increase the row we're
    # on for the next series of sprites.
    sprites_per_row = 0x8 * 0x20
    while i < 0x2000:
        # Each iteration produces a 8x8 field of colours but
        # that's not practical for writing because we want several
        # sprites on one row.
        for j in range(8):
            # Handling the high and low byte
            row_for_pixels = row + j
            if row_for_pixels >= len(grid):
                grid.append([])
            low_byte = ppu.memory._ppu_memory[i + j]
            high_byte = ppu.memory._ppu_memory[i + j + 0x8]

            for k in range(8):
                # Now we're handling the bits from the high and low byte
                # Start from the left hand most side and read to the right.
                high_bit = (high_byte >> (7 - k)) & 0x1
                high_bit <<= 1
                low_bit = (low_byte >> (7 - k)) & 0x1
                bits = high_bit + low_bit
                grid[row_for_pixels].append(bits)

        # 16 bytes at a time.
        i += 0x10
        if i % sprites_per_row == 0:
            # We have 8 rows of pixels per grid row.
            row += 0x8

    with open('ppu_patterns_viz.ppm', 'w') as f:
        f.write('P3\n')
        # The width is just the length of each list in the grid.
        # The height is the total number of lists in the grid.
        f.write('128 256\n')
        f.write('255\n')
        # Show patterns as 16x16 pixel chunks (chunks of 8 high
        # bytes and 8 low bytes but we use the high bytes as
        # a high bit )
        # 16 patterns of 8 pixels each on a row.
        for row in grid:
            # Go row by row.
            for bits in row:
                # Each column in the row.
                if bits == 0:
                    f.write('0 0 0 ')
                if bits == 1:
                    f.write('255 255 255 ')
                if bits == 2:
                    f.write('171 171 171 ')
                if bits == 3:
                    f.write('85 85 85 ')
            f.write('\n')
