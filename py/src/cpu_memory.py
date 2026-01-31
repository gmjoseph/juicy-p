from typing import Any
from typing import Optional

from constants import PPUAddressValues


# TODO
# Update to handle mirroring in various parts of the
# non-PPU address space:
# https://wiki.nesdev.com/w/index.php/CPU_memory_map
# Probably treat this like virtual memory access that knows
# how to do the mapping.

class CPUMemory():

    def __init__(self):
        self._cpu_memory = bytearray(0x10000)

    def read(self, at_address: int, amount: int) -> bytearray:
        """
        Reads some number of bytes at the start address.
        """
        # if at_address in PPUAddressValues:
        #     print(f"Warning, reading from the PPU reserved address in the CPU memory: {hex(at_address)}.")
        return self._cpu_memory[at_address:at_address + amount]

    def read_one(self, at_address: int) -> int:
        """
        Reads 1 byte worth of data with no conversion.
        """
        # if at_address in PPUAddressValues:
        #     print(f"Warning, reading from the PPU reserved address in the CPU memory: {hex(at_address)}.")
        return self._cpu_memory[at_address]

    def read_two(self, at_address: int) -> int:
        """
        Reads 2 bytes worth of data and converts to an integer.
        """
        # TODO
        # Handles wrap around at any page boundary. For example if
        # we're at 0x2ff and we read two values, the first comes from
        # 0x2ff and the second comes from 0x200.

        # TODO
        # Might need to revisit this depending on where page boundaries
        # are.

        # TODO
        # Find a better way to read a little endian short.
        # value = int.from_bytes(self._cpu_memory[at_address:at_address+2], 'little')
        if at_address & 0xff == 0xff:
            # we're at the page boundary and need to pick one value at
            # the boundary and then wrap around to get the next.
            low = self.read_one(at_address)
            high = self.read_one(at_address - 0xff)
        else:
            # No wrap around.
            low = self.read_one(at_address)
            high = self.read_one(at_address + 1)
        high <<= 8
        value = high + low
        return value

    def read_from_zero_page_uint8(self, at_address: int) -> int:
        """
        Lets us read from the zero page while taking wraparound
        into account. Similar to read_from_zero_page, but I'm not
        sure we actually ever wrap around because we're only going
        to read one byte.
        """
        return self.read_from_zero_page_uint16(at_address) & 0xff

    def read_from_zero_page_uint16(self, at_address: int) -> int:
        """
        Lets us read from the zero page while taking wraparound
        into account. For example, if we're reading from 0xff
        and then 0xff + 1, we should read from 0x0 instead (
        wrapped around to lowest byte at the beginning). This
        applies even in cases where it's far beyond 0xff.
        So 0x101 should read from 0x101-0xff and 0x101-0xff-0x1
        for the high and low bytes respectively.
        """
        if at_address > 0xff:
            # Both are wrapped around, so we look one backwards
            # from the high bit.
            low = self.read_one(at_address - 0xff - 1)
            high = self.read_one(at_address - 0xff)
        elif at_address == 0xff:
            # Edge case, the high is wrapped but the low isn't.
            low = self.read_one(at_address)
            high = self.read_one(at_address - 0xff)
        else:
            # No wrap around.
            low = self.read_one(at_address)
            high = self.read_one(at_address + 1)
        high <<= 8
        value = high + low
        return value

    def write(self, what: int, at_address: int) -> None:
        """
        Supports writing one byte of data at a time to an absolute
        address.
        Certain 'at_address' values are special and involve writing to
        PPU memory. This is the case when the at_address is 0x2000 to
        0x2007 and 0x4014. These are all probably handled specifically
        in the PPU and in PPU memory but I've left this in to write
        to them for now because I don't think there's much harm in it.
        See the printed warning below.
        address: an absolute address.
        """
        if at_address in PPUAddressValues:
            print(f"Warning, writing to the PPU reserved address in the CPU memory: {hex(at_address)}.")

        self._cpu_memory[at_address] = what

    def write_cpu_memory(self, what: bytearray, at_address: int) -> None:
        """
        Supports overwriting buffers of data into the memory buffer.
        Only used by ROM loading for now, so maybe it's replaceable.
        what: some data
        address: an absolute address
        """
        self._cpu_memory[at_address:len(what)] = what

    def _debug_read_using_disk_addr(self, at_address: int) -> None:
        # Temporary to read a value from memory by using the
        # address of the data in the file on disk.
        # This means we need to convert the address to where
        # it may be loaded and also subtract the header.
        real_address = at_address + 0x8000
        real_address -= 0x10
        value = self._cpu_memory[at_address]
        print(value)
