#include "CPUMemory.h"
#include <stdio.h>
#include <string.h>

uint16_t
CPUMemory::read_two(uint16_t at_address) {
    /*
     * Reads 2 bytes worth of data and converts to an integer.
     */
    // TODO
    // Handles wrap around at any page boundary. For example if
    // we're at 0x2ff and we read two values, the first comes from
    // 0x2ff and the second comes from 0x200.

    // TODO
    // Might need to revisit this depending on where page boundaries
    // are.

    // TODO
    // Find a better way to read a little endian short.
    // value = int.from_bytes(self._cpu_memory[at_address:at_address+2], 'little')
    uint8_t low = 0;
    uint16_t high = 0;
    if ((at_address & 0xff) == 0xff) {
        // we're at the page boundary and need to pick one value at
        // the boundary and then wrap around to get the next.
        low = read_one(at_address);
        high = read_one(at_address - 0xff);
    } else {
        // No wrap around.
        low = read_one(at_address);
        high = read_one(at_address + 1);
    }
    high <<= 8;
    return high + low;
}

uint8_t
CPUMemory::read_from_zero_page_uint8(uint16_t at_address) {
    /* 
     * Lets us read from the zero page while taking wraparound
     * into account. Similar to read_from_zero_page, but I'm not
     * sure we actually ever wrap around because we're only going
     * to read one byte.
     */
    return (read_from_zero_page_uint16(at_address) & 0xff);
}

uint16_t
CPUMemory::read_from_zero_page_uint16(uint16_t at_address) {
    /*
     * Lets us read from the zero page while taking wraparound
     * into account. For example, if we're reading from 0xff
     * and then 0xff + 1, we should read from 0x0 instead (
     * wrapped around to lowest byte at the beginning). This
     * applies even in cases where it's far beyond 0xff.
     * So 0x101 should read from 0x101-0xff and 0x101-0xff-0x1
     * for the high and low bytes respectively.
     */
    uint8_t low = 0;
    uint16_t high = 0;

    if (at_address > 0xff) {
        // Both are wrapped around, so we look one backwards
        // from the high bit.
        low = read_one(at_address - 0xff - 1);
        high = read_one(at_address - 0xff);
    } else if (at_address == 0xff) {
        // Edge case, the high is wrapped but the low isn't.
        low = read_one(at_address);
        high = read_one(at_address - 0xff);
    } else {
        // No wrap around.
        low = read_one(at_address);
        high = read_one(at_address + 1);
    }
    high <<= 8;
    return high + low;
}

void
CPUMemory::read(uint16_t at_address, uint16_t amount, uint8_t* out_buffer) {
    /*
     * Reads some number of bytes at the start address. at_address
     * could accidentally be a memory-mapped PPU register but that SHOULD
     * never happen. Instead that would be handled in CPU instructions
     * which would request the data from the PPU.
     * at_address: an absolute address.
     */
    uint64_t cpu_memory_address = (uint64_t)cpu_memory;
    uint8_t* read_from = (uint8_t*)(cpu_memory_address + at_address);
    memcpy(out_buffer, read_from, amount);
}

void
CPUMemory::write(uint8_t what, uint16_t at_address) {
    /*
     * Supports writing one byte of data at a time to an absolute
     * address.
     * Certain 'at_address' values are special and involve writing to
     * PPU memory. This is the case when the at_address is 0x2000 to
     * 0x2007 and 0x4014 (and i believe their mirrors). These SHOULD
     * all be handled in CPU instructions.
     * at_address: an absolute address.
     */
    cpu_memory[at_address] = what;
}

void
CPUMemory::write_cpu_memory(uint16_t at_address, uint16_t amount, uint8_t* in_buffer) {
    /*
     * Supports overwriting buffers of data into the memory buffer.
     * Only used by ROM loading for now, so maybe it's replaceable.
     * what: some data
     * address: an absolute address
     */
    uint64_t cpu_memory_address = (uint64_t)(cpu_memory);
    uint8_t* write_to = (uint8_t*)(cpu_memory_address + at_address);
    memcpy(write_to, in_buffer, amount);
}

void
CPUMemory::_debug_read_using_disk_addr(uint16_t at_address) {
    // Temporary to read a value from memory by using the
    // address of the data in the file on disk.
    // This means we need to convert the address to where
    // it may be loaded and also subtract the header.
    uint16_t real_address = at_address + 0x8000;
    real_address -= 0x10;
    uint8_t value = cpu_memory[at_address];
    printf("%d\n", value);
}
