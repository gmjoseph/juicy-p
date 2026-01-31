import struct
from pathlib import Path
from typing import Any

from constants import NametableMirroring


# TODO
# Move to constants?
_MAGIC_NUMBER = b'NES\x1a'
_HEADER_SIZE = 16
# 16kb
_ROM_SIZE = 0x4000
# 8kb
_PALETTE_SIZE = 0x2000

# https://wiki.nesdev.com/w/index.php/Mapper
# On where to map the physical data to virtual memory.
_mappers = {
    0x0: {
        # TODO
        # Distinguish between NROM-128 and NROM-256.
        # https://wiki.nesdev.com/w/index.php/NROM
        # "Your program is mapped into $8000-$FFFF (NROM-256) or both $8000-$BFFF and
        # $C000-$FFFF (NROM-128). Most NROM-128 games actually run in $C000-$FFFF rather
        # than $8000-$BFFF because it makes the program easier to assemble and link"
        # CPU $C000-$FFFF: Last 16 KB of ROM (NROM-256) or mirror of $8000-$BFFF (NROM-128).
        # For a mapper of type '0' (NROM-256)...
        # We're dealing with NROM-128 for the testing ROM because it's only 16kb
        # (128kilobit i.e. 128/8 = 16kb), so let's just hardcode that for now.
        'name': 'NROM',
        'low': 0x8000,
        'high': 0xc000,
    },
    0x3: {
        # TODO
        # Bank switching isn't even implemented. Probably none of these values
        # are even right...
        'name': 'CNROM',
        'low': 0x8000,
        'high': 0xc000,
    },
}

class Header:
    # Description of these properties:
    # 76543210
    # ||||||||
    # |||||||+- Mirroring: 0: horizontal (vertical arrangement) (CIRAM A10 = PPU A11)
    # |||||||              1: vertical (horizontal arrangement) (CIRAM A10 = PPU A10)
    # ||||||+-- 1: Cartridge contains battery-backed PRG RAM ($6000-7FFF) or other persistent memory
    # |||||+--- 1: 512-byte trainer at $7000-$71FF (stored before PRG data)
    # ||||+---- 1: Ignore mirroring control or above mirroring bit; instead provide four-screen VRAM
    # ++++----- Lower nybble of mapper number
    @property
    def nametable_mirroring(self) -> str:
        # This works for NROMs, there are more possible
        # mirroring configurations.
        NametableMirroring.HORIZONTAL if bool(self.flags_6 & 0x1) else NametableMirroring.VERTICAL

    @property
    def _battery_backed_memory(self) -> bool:
        return bool(self.flags_6 & 0x2)

    @property
    def _trainer(self) -> bool:
        return bool(self.flags_6 & 0x4)

    def __init__(self, file_header: bytes) -> None:
        self.magic_number = file_header[0:4]
        # Number of 16kb (pages) ROM Banks
        self.prg_rom_size = struct.unpack_from(">B", file_header, offset=4)[0]
        # Number of 8kb (pages) VROM banks
        # So if it's 1, we have 1 8kb VROM bank page.
        self.chr_rom_size = struct.unpack_from(">B", file_header, offset=5)[0]
        # TODO
        # Handle flags 6-10
        # https://wiki.nesdev.com/w/index.php/INES#Flags_6
        # For now assuming there's no trainer due to the test file but if
        # we want to handle the trainer, we'll need to look at flags 6
        # not sure which bit.
        #  (flag6) bit 4-7   Four lower bits of ROM Mapper Type.
        self.flags_6 = struct.unpack_from(">B", file_header, offset=6)[0]
        #  (flag7) bit 4-7   Four higher bits of ROM Mapper Type.
        self.flags_7 = struct.unpack_from(">B", file_header, offset=7)[0]
        self.flags_8 = struct.unpack_from(">B", file_header, offset=8)[0]
        self.flags_9 = struct.unpack_from(">B", file_header, offset=9)[0]
        self.flags_10 = struct.unpack_from(">B", file_header, offset=10)[0]
        self.padding = file_header[11:16]
        self._check_magic_number()

    def _check_magic_number(self):
        if _MAGIC_NUMBER != self.magic_number:
            raise Exception("This is not an NES file.")

    def rom_type(self) -> int:
        """
        Using the values in flags 6 and 7, gets us the rom type so we know
        how to map this file into memory.
        """
        low = self.flags_6 >> 4
        high = self.flags_7 >> 4
        return low + (high << 4)


class Cartridge:
    def __init__(self, filepath: Path) -> None:
        data = self._load(filepath)
        self.data = data
        self._header = Header(data[0:_HEADER_SIZE])
        # Take 16kb hardcoded for 1 page for now, we'll have to then reverse it.
        # This is because I'm assuming 128kilobit for NROM-128 (128/8 = 16kb).
        # Past the header.
        start = _HEADER_SIZE 

        # Then ROM Banks (if there is no trainer, that's what we're assuming for now)
        # in ascending order. Otherwise, if there is a trainer, it's 512 bytes further.
        # After ROM banks we have VROM banks in ascending order.
        # So in this case the VROM is starting at 0x3e90 (0x10 for the header + 0x3e80
        # for the ROM banks (ascending)).   
        end = _HEADER_SIZE + _ROM_SIZE
        self._rom = data[start:end]

    def _load(self, filepath: Path) -> bytes:
        with open(filepath, mode='rb') as file:
            # Load the entire file into memory.
            file_data = file.read()
        return file_data

    def store_rom(self, memory: Any) -> None:
        # We'll be doing this:
        # https://wiki.nesdev.com/w/index.php/NROM#Banks
        # CPU $8000-$BFFF: First 16 KB of ROM.
        # CPU $C000-$FFFF: Last 16 KB of ROM (NROM-256) or mirror of $8000-$BFFF (NROM-128).
        # That is, since we're hardcoding this to NROM-128, 0x8000-0xBFFF
        # and 0xC000-0xFFFF should be duplicates of each other.
        mapper = _mappers[self._header.rom_type()]
        # TODO
        # We may need a function per mapper strategy. This might not be needed
        # depending on how much in common there is between mappers and how
        # much can be derived from the configuration data.
        memory.write_cpu_memory(self._rom, mapper['low'])
        memory.write_cpu_memory(self._rom, mapper['high'])

    def store_palette(self, memory: Any) -> None:
        print("TODO - load palette table from chr_rom area.")
        if self._header.chr_rom_size > 0:
            start = _HEADER_SIZE + _ROM_SIZE
            end = start + _PALETTE_SIZE
            palette = self.data[start:end]
            memory.write_ppu_memory(palette, 0)
