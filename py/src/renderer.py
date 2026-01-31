import sys
from datetime import datetime
from pathlib import Path
from time import time

from palettes import LUT


_PATH = '_frames/'
# Allows for 'debouncing' frame disk writes.
_FILE_PER_FRAMES = 1

_RENDERER_TYPE = 'file'
# _RENDERER_TYPE = 'memory'

class Renderer():
    """
    Takes the entire pixel buffer for one frame and renders it.
    """

    def __init__(self) -> None:
        self.renderer_type = _RENDERER_TYPE
        self._start_dt = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        self._frames = 0
        self._last_frame = time()

    def _file_render(self, pixels: bytearray) -> None:
        if self._frames % _FILE_PER_FRAMES != 0:
            return
        filepath = f'{_PATH}{self._start_dt}-frame_{self._frames}.ppm'
        with open(filepath, 'w') as f:
            f.write('P3\n')
            f.write('256 240\n')
            f.write('255\n')
            for y in range(240):
                # Go row by row.
                for x in range(256):
                    # Each column in the row.
                    idx = x + y * 256
                    pixel_lookup = pixels[idx]
                    try:
                        r, g, b = LUT[pixel_lookup]
                        f.write(f'{r} {g} {b} ')
                    except:
                        f.write(f'0 0 0 ')
                f.write('\n')

    def _terminal_render(self, pixels: bytearray) -> None:
        # Lookup for pixel codes to terminal colours. We'd need
        # a terminal-oriented palette for this that isn't really RGB.
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
        print()
        for i, p in enumerate(pixels):
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

    def render(self, pixels: bytearray) -> None:
        self._frames += 1
        if self.renderer_type == 'terminal':
            return self._terminal_render(pixels)
        elif self.renderer_type == 'file':
            return self._file_render(pixels)
        elif self.renderer_type == 'memory':
            n = time()
            d = n - self._last_frame
            self._last_frame = n
            print(d)
            return None
