from typing import Any
from typing import Optional

from constants import PPUMemoryMap
from constants import NametableMirroring

# PPU memory map from:
# https://wiki.nesdev.com/w/index.php/PPU_memory_map
# Address range 	Size 	Description
# $0000-$0FFF 	$1000 	Pattern table 0
# $1000-$1FFF 	$1000 	Pattern table 1
# $2000-$23FF 	$0400 	Nametable 0
# $2400-$27FF 	$0400 	Nametable 1
# $2800-$2BFF 	$0400 	Nametable 2
# $2C00-$2FFF 	$0400 	Nametable 3
# $3000-$3EFF 	$0F00 	Mirrors of $2000-$2EFF
# $3F00-$3F1F 	$0020 	Palette RAM indexes
# $3F20-$3FFF 	$00E0 	Mirrors of $3F00-$3F1F

class PPUMemory:

    @property
    def pattern_table_0(self) -> bytearray:
        start, end = PPUMemoryMap['pattern_table_0']
        return self._ppu_memory[start:end + 1]
    
    @property
    def pattern_table_1(self) -> bytearray:
        start, end = PPUMemoryMap['pattern_table_1']
        return self._ppu_memory[start:end + 1]

    @property
    def palette_ram_indexes(self) -> bytearray:
        start, end = PPUMemoryMap['palette_ram_indexes']
        return self._ppu_memory[start:end + 1]

    def __init__(self):
        self._ppu_memory = bytearray(0x4000)
        self._oam_memory = bytearray(0x100)
        # Because all addresses get processed before being read from,
        # we can save time by caching the processing.
        self._address_cache = {}
        # TODO
        # This is being updated from the cartridge as everything is being
        # initialized but this is a lame pattern. It should be derivable.
        self._nametable_mirroring = None

    @property
    def nametable_mirroring(self) -> NametableMirroring:
        return self._nametable_mirroring

    @nametable_mirroring.setter
    def nametable_mirroring(self, what: NametableMirroring) -> None:
        print(f"PPU Memory setting mirroring to {what}")
        self._nametable_mirroring = what
        # Gotta clear the cache because now what we're mirroring
        # between has changed.
        self._address_cache = {}

    def _run_address_preprocessors(self, address: int) -> int:
        # Lots of potential places for mirroring, so each address needs
        # to be processed to find its physical location.
        original_address = address

        _, end = PPUMemoryMap['ppu_memory_range']
        if address >= end:
            # The valid range of addresses we can write to on the PPU is
            # 0x0 -> 0x3fff, higher addresses are mirrored down which just
            # means in terms of the implementation that we can wrap them
            # back around.
            print(f"Warning, got an address more than 0x4000: {hex(address)}")
            address %= end

        # Circular import
        from ppu_utils import maybe_resolve_nametable_address
        address = maybe_resolve_nametable_address(address, self._nametable_mirroring)

        # Circular import
        from ppu_utils import maybe_resolve_palette_address
        address = maybe_resolve_palette_address(address)

        # Cache it so we don't have to do this again.
        self._address_cache[original_address] = address
        return address

    def read_one(self, at_address: int) -> int:
        """
        Reads 1 byte worth of data.
        """
        if at_address in self._address_cache:
            address = self._address_cache[at_address]
        else:
            address = self._run_address_preprocessors(at_address)
        return self._ppu_memory[address]

    def write(self, what: int, at_address: int) -> None:
        """
        Supports writing one byte of data at a time to an absolute
        address.
        what: a byte of data.
        address: an absolute address.
        """
        if at_address in self._address_cache:
            address = self._address_cache[at_address]
        else:
            address = self._run_address_preprocessors(at_address)
        self._ppu_memory[address] = what

    def write_ppu_memory(self, what: bytearray, at_address: int) -> None:
        """
        Supports writing a big chunk of PPU memory at
        once. Used only in cartridge loading.
        """
        self._ppu_memory[at_address:len(what)] = what

    def background_palette(self, which: int) -> bytearray:
        """
        Returns a background palette for a given index. There are three
        colours in each palette.
        """
        # TODO
        # This could be improved

        # TODO
        # Confirm:
        # This only gives 3 bytes but it's expected that the palette have
        # four values. This is because one value comes from the universal
        # background colour at 0x3f00 which is always byte 0 i believe?
        if not (0 <= which <= 3):
            raise Exception(f"Background palettes are indexed 0-3. Got {which}")
        elif which == 0:
            b = self._ppu_memory[0x3F01:0x3F04]
        elif which == 1:
            b = self._ppu_memory[0x3F05:0x3F08]
        elif which == 2:
            b = self._ppu_memory[0x3F09:0x3F0C]
        elif which == 3:
            b = self._ppu_memory[0x3F0D:0x3F10]
        b = self._ppu_memory[0x3F00:0x3F01] + b
        return b

    def sprite_palette(self, which: int) -> bytearray:
        """
        Returns a sprite palette for a given index. There are three
        colours in each palette.
        """
        # TODO
        # This could be improved

        # TODO
        # Confirm:
        # This only gives 3 bytes but it's expected that the palette have
        # four values. This is because one value comes from the universal
        # background colour at 0x3f00 which is always byte 0 i believe?
        if not (4 <= which <= 7):
            raise Exception(f"Sprite palettes are indexed 4-7. Got {which}")
        elif which == 4:
            b = self._ppu_memory[0x3F11:0x3F14]
        elif which == 5:
            b = self._ppu_memory[0x3F15:0x3F18]
        elif which == 6:
            b = self._ppu_memory[0x3F19:0x3F1C]
        elif which == 7:
            b = self._ppu_memory[0x3F1D:0x3F20]
        b = self._ppu_memory[0x3F00:0x3F01] + b
        return b