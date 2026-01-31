from typing import Any


# TODO
# For the moment most of these are write-only. We'll need to support
# possibly read handler versions of some of these.

# TODO
# We're blindly letting any register be read to/written from. This
# isn't how it's supposed to work but apparently some badly behaved
# games will do this anyways (after all, you just need the right
# assembly instruction and operands).

def _handler_PPUCTRL(ppu: Any, bus_data: int) -> None:
    ppu.PPUCTRL = bus_data


def _handler_PPUMASK(ppu: Any, bus_data: int) -> None:
    # 7  bit  0
    # ---- ----
    # BGRs bMmG
    # |||| ||||
    # |||| |||+- Greyscale (0: normal color, 1: produce a greyscale display)
    # |||| ||+-- 1: Show background in leftmost 8 pixels of screen, 0: Hide
    # |||| |+--- 1: Show sprites in leftmost 8 pixels of screen, 0: Hide
    # |||| +---- 1: Show background
    # |||+------ 1: Show sprites
    # ||+------- Emphasize red
    # |+-------- Emphasize green
    # +--------- Emphasize blue
    ppu.PPUMASK = bus_data


def _handler_PPUSTATUS(ppu: Any) -> None:
    # Will write to the bus for now from ppu status
    # print("WRITING 0x80 TO BUS DATA TO FAKE VBLANK READY FOR CPU!")
    status = ppu.PPUSTATUS
    ppu._bus.data = status


def _handler_OAMADDR(ppu: Any, bus_data: int) -> None:
    # Will write to the OAMADDR register
    ppu.OAMADDR = bus_data


def _handler_OAMDATA(ppu: Any, bus_data: int) -> None:
    """
    NOTE: Only handles writes at the moment.
    "For emulation purposes, it is probably best to completely ignore
    writes during rendering.
    https://wiki.nesdev.com/w/index.php/PPU_programmer_reference#OAMADDR
    """
    # FIXME
    # Going off VBLANK to determine if rendering or not, this
    # might be wrong timing-wise.
    if ppu.rendering:
        print("WARNING writing to OAMDATA while rendering.")
        return

    # FIXME
    # This should write to OAMDMA?
    ppu.memory.write(bus_data, ppu.OAMDATA)
    ppu._increment_OAMADDR()

    # FIXME
    # This may need to support a read mode with auto incrementing
    # but that may be internal to the PPU only...


def _handler_PPUSCROLL(ppu: Any, bus_data: int) -> None:
    ppu.PPUSCROLL = bus_data


def _handler_PPUADDR(ppu: Any, bus_data: int) -> None:
    ppu.PPUADDR = bus_data


def _handler_PPUDATA(ppu: Any, bus_data: int) -> None:
    # Do this only if we're writing to the PPU memory.
    # Read PPUSTATUS but do nothing with the result. This forces
    # a bit to be cleared.
    _ = ppu.PPUSTATUS
    ppu.memory.write(bus_data, ppu.PPUADDR)

    # Shouldn't be a need for this after the CPU handles the
    # instruction but if so we can move it there.
    ppu._increment_PPUADDR()


# FIXME
# If this is exported it assumes OAMDMA can be handled on the PPU
# side which then expects bus data even though there won't be any.
# def _handler_OAMDMA(ppu: Any, bus_data: int) -> None:
#     # NOP
#     pass


ppu_operations = {
    '_handler_PPUCTRL': _handler_PPUCTRL,
    '_handler_PPUMASK': _handler_PPUMASK,
    '_handler_PPUSTATUS': _handler_PPUSTATUS,
    '_handler_OAMADDR': _handler_OAMADDR,
    '_handler_OAMDATA': _handler_OAMDATA,
    '_handler_PPUSCROLL': _handler_PPUSCROLL,
    '_handler_PPUADDR': _handler_PPUADDR,
    '_handler_PPUDATA': _handler_PPUDATA,
    # '_handler_OAMDMA': _handler_OAMDMA,
}
