from typing import Any
from typing import Callable
from typing import Optional
from typing import Tuple

from ppu_operations import ppu_operations
from constants import AddressingMode
from constants import NametableMirroring
from constants import NametableSize
from constants import PPUAddress
from constants import PPUMemoryMap
from constants import PPURegister
from constants import ReadMnemonicValues
from constants import WriteMnemonicValues


###########################################################################
# PPU Memory Utils
###########################################################################

def resolve_register_from_instruction(
    instruction: dict,
    instruction_bytes: bytearray,
) -> Optional[PPURegister]:
    # TODO
    # PPU registers are only ever accessed with absolute addressing modes
    # because of how they're memory mapped on the CPU?
    if AddressingMode.ABSOLUTE == instruction['addressing_mode']:
        low = instruction_bytes[1]
        high = instruction_bytes[2] << 0x8
        address = high + low
        return resolve_register(address), address
    return None, None


def resolve_register(address: int) -> Optional[PPURegister]:
    # If the instruction is referencing a PPU address, this will
    # determine if so and which one.

    # "The PPU exposes eight memory-mapped registers to the CPU.
    # These nominally sit at $2000 through $2007 in the CPU's address
    # space, but because they're incompletely decoded, they're
    # mirrored in every 8 bytes from $2008 through $3FFF, so a write
    # to $3456 is the same as a write to $2006. "
    # Probably with modulo and a check on the range
    # A nice way to handle this is (target_address - register_address) % 8 == 0.
    # If that's true, then we're writing to a certain register.
    # For instance, if 0x3456 is meant to write to 0x2006, then
    # (0x3456-0x2006) % 0x8 should be zero. Any of the other registers
    # shouldn't work:
    # (0x3456 - 0x2000) % 8 == 6
    # (0x3456 - 0x2001) % 8 == 5
    # (0x3456 - 0x2002) % 8 == 4
    # (0x3456 - 0x2003) % 8 == 3
    # (0x3456 - 0x2004) % 8 == 2
    # (0x3456 - 0x2005) % 8 == 1
    # (0x3456 - 0x2006) % 8 == 0 <--
    # (0x3456 - 0x2007) % 8 == 7
    # etc.
    #
    # That said, this can all be replaced by masking with the original
    # address and seeing if the address, after applying the mask, is still
    # the original address.
    # E.g.:
    # 0x3000 & 0x2000 == 0x2000 ? it does.
    # 0x3ff8 & 0x2000 == 0x2000 ? it does.
    # 0x3ff8 & 0x2001 == 0x2001 ? it doesn't.

    register = None

    # Special case, technically resides in the CPU but the data must be
    # transferred to internal PPU memory.
    if address == PPUAddress.OAMDMA_ADDRESS:
        return PPURegister.OAMDMA

    if address < 0x2000 or address >= 0x4000:
        # We don't map addresses in this range to any register in particular,
        # see the comment above.
        return register

    # FIXME
    # Returning early or if/elsing here breaks a tonne of tests, namely to do
    # with writing to certain registers. This should be fixed. Maybe multiple
    # conditions end up being met which causes problems?
    # The reason this fails at times is for NON MIRRORED addresses, where
    # for example 0x2001 & 0x2000 will be 0x2000 so we'll think that PPUMASK
    # is for PPUCTRL, which is why we need this 'fall through' behaviour.
    # This could be fixed by a lookup or maybe some kind of normalization?
    if address & PPUAddress.PPUCTRL_ADDRESS == PPUAddress.PPUCTRL_ADDRESS:
        register = PPURegister.PPUCTRL

    if address & PPUAddress.PPUMASK_ADDRESS == PPUAddress.PPUMASK_ADDRESS:
        register = PPURegister.PPUMASK

    if address & PPUAddress.PPUSTATUS_ADDRESS == PPUAddress.PPUSTATUS_ADDRESS:
        register = PPURegister.PPUSTATUS

    if address & PPUAddress.OAMADDR_ADDRESS == PPUAddress.OAMADDR_ADDRESS:
        register = PPURegister.OAMADDR

    if address & PPUAddress.OAMDATA_ADDRESS == PPUAddress.OAMDATA_ADDRESS:
        register = PPURegister.OAMDATA

    if address & PPUAddress.PPUSCROLL_ADDRESS == PPUAddress.PPUSCROLL_ADDRESS:
        register = PPURegister.PPUSCROLL

    if address & PPUAddress.PPUADDR_ADDRESS == PPUAddress.PPUADDR_ADDRESS:
        register = PPURegister.PPUADDR

    if address & PPUAddress.PPUDATA_ADDRESS == PPUAddress.PPUDATA_ADDRESS:
        register = PPURegister.PPUDATA

    return register


def maybe_resolve_nametable_address(address: int, mirroring: NametableMirroring) -> int:
    # The full range of addresses. There could be multiple levels of mirroring,
    # e.g. the address is in the nametable_mirrors but then maps back to
    # an address that is horizontally mirrored from 0x2400 back to 0x2000.
    output_address = address
    start, end = PPUMemoryMap['nametable_range']

    if address < start or address > end:
        # Out of the nametable range.
        return output_address

    mirrors_start, mirrors_end = PPUMemoryMap['nametable_mirrors']
    if address >= mirrors_start and address <= mirrors_end:
        # Resolve the mirrored address to an actual nametable address.
        # Since this mirrors 0x2000 - 0x2EFF in 0x3000 to 0x3EFF
        # we can just subtract down.
        output_address = address - 0x1000

    # From this point on, check on output_address in case `address` was
    # a mirrored one.

    if mirroring == NametableMirroring.HORIZONTAL:
        # "Horizontal mirroring: $2000 equals $2400 and $2800 equals $2C00
        # (e.g. Kid Icarus)"
        # Top right and bottom right.
        check = ['nametable_1', 'nametable_3']
        for c in check:
            start, end = PPUMemoryMap[c]
            if start <= output_address <= end:
                # E.g. 0x2400 back to 0x2000 is a difference of the nametable
                # size.
                output_address -= NametableSize

    if mirroring == NametableMirroring.VERTICAL:
        # "Vertical mirroring: $2000 equals $2800 and $2400 equals $2C00
        # (e.g. Super Mario Bros.)"
        check = ['nametable_2', 'nametable_3']
        for c in check:
            start, end = PPUMemoryMap[c]
            if start <= output_address <= end:
                # E.g. 0x2800 back to 0x2000 is a difference of double
                # the name table size.
                output_address -= NametableSize * 2

    return output_address


def maybe_resolve_palette_address(address: int) -> int:
    """
    Two mirroring requirements: one is for addresses in
    the palette ram that map directly to one another address
    in the palette ram.
    The other is for a mirror of the entire contents of
    palette ram.
    """
    # "Addresses $3F10/$3F14/$3F18/$3F1C are mirrors of
    # $3F00/$3F04/$3F08/$3F0C. Note that this goes for writing
    # as well as reading. A symptom of not having implemented
    # this correctly in an emulator is the sky being black in
    # Super Mario Bros., which writes the backdrop color
    # through $3F10."
    if address == 0x3F10:
        address -= 0x10

    elif address == 0x3F14:
        address -= 0x10

    elif address == 0x3F18:
        address -= 0x10

    elif address == 0x3F1C:
        address -= 0x10

    start, end = PPUMemoryMap['palette_ram_mirrors']
    if start <= address <= end:
        # Repeats at every 0x20 intervals, or 7 times.
        indexes_start, _ = PPUMemoryMap['palette_ram_indexes']
        delta = address - indexes_start
        # Determines how many multipliers of 0x20 have been
        # added to the address.
        # 3f20 = 3f00 (0x20 * 1)
        # 3f40 = 3f00 (0x20 * 2)
        # 3f60 = 3f00 (0x20 * 3)
        # ...
        # 3fe0 = 3f00 (0x20 * 7)
        # delta // 0x20 is the same as delta >> 5
        multiplier = delta >> 5
        address = address - 0x20 * multiplier
    return address


###########################################################################
# PPU Instruction Utils
###########################################################################

def handler_for_read(
    instruction: dict,
    instruction_bytes: bytearray,
) -> Tuple[PPURegister, Optional[Callable]]:
    """
    Before the CPU executes certain instructions, it may need
    to read data from the PPU. As a result, the PPU gets a
    chance to do something with the instruction before the
    opcode is actually handled in the CPU. This determines
    whether for a given instruction the PPU can handle an attempted
    read.
    Think of this as interleaving PPU execution with CPU execution:
    - CPU decode
    - PPU handles
    - bus now has read data for CPU
    - CPU handles (with bus data)
    """
    register, address = resolve_register_from_instruction(instruction, instruction_bytes)

    # It means the operation is not targeting a PPU register and so
    # we don't have to handle it.
    if not register:
        return register, None

    _debug_unhanled_mnemonc(instruction, register)
    # We handle reads before the CPU gets a chance to execute its
    # instructions because the CPU is relying on the result of the
    # PPU read to execute the instruction.
    is_read = instruction['mnemonic'] in ReadMnemonicValues
    if not is_read:
        # TODO
        # Re-enable if execution isn't performing as intended, but it seems
        # like for sane programs that certain mnemonic + PPU register combinations
        # don't make any sense.
        # print(
        #     f"WARNING: unhandled mnemonic {instruction['mnemonic']}"
        #     f" for register {register}"
        #     f" for address {address}"
        #     f" for READ"
        # )
        # # Returning until we handle all the instructions we need to handle.
        return register, None

    handler = ppu_operations[f'_handler_{register.value}']
    return register, handler


def handler_for_write(
    instruction: dict,
    instruction_bytes: bytearray,
) -> Tuple[PPURegister, Optional[Callable]]:
    """
    Similar to `can_handle_read`, expect everything is opposite.
    In this case, the CPU is trying to write to either a PPU
    address or a PPU register (more accurately, all writes will
    be to a PPU register from the CPU's perspective, but PPUADDR
    is really storing data in PPU memory). For this to work, the
    CPU gets to handle the instruction first, including handling.
    The PPU then gets a chance afterwards to do something with
    the resulting data.
    Think of this as interleaving PPU execution with CPU execution:
    - CPU decode
    - CPU handles
    - bus now has write data for PPU
    - PPU handles (with bus data)
    """
    register, address = resolve_register_from_instruction(instruction, instruction_bytes)

    # It means the operation is not targeting a PPU register and so
    # we don't have to handle it.
    if not register:
        return register, None

    _debug_unhanled_mnemonc(instruction, register)
    is_write = instruction['mnemonic'] in WriteMnemonicValues
    if not is_write:
        # TODO
        # Re-enable if execution isn't performing as intended, but it seems
        # like for sane programs that certain mnemonic + PPU register combinations
        # don't make any sense.
        # print(
        #     f"WARNING: unhandled mnemonic {instruction['mnemonic']}"
        #     f" for register {register}"
        #     f" for address {address}"
        #     f" for WRITE"
        # )
        # Returning until we handle all the instructions we need to handle.
        return register, None

    if f'_handler_{register.value}' not in ppu_operations:
        # The only one at the moment for this is OAMDMA.
        # See the comment in ppu_oeprations why it isn't handled.
        # print(f"WARNING: no handler available for {register.value}")
        return register, None

    handler = ppu_operations[f'_handler_{register.value}']
    return register, handler


def _debug_unhanled_mnemonc(instruction: dict, register: PPURegister) -> None:
    """
    This checks if we encounter any program that tries to use
    a mnemonic with a PPU register that isn't handled in the
    read or write mnemonics. It means that it's perhaps badly
    behaved or it's just a shortcoming in the code and we should
    handle that combination of mnemonic and PPU register.
    """
    mnemonic = instruction['mnemonic']
    is_write = mnemonic in WriteMnemonicValues
    is_read = mnemonic in ReadMnemonicValues
    if is_write or is_read:
        return
    print(
        f"WARNING: unhandled mnemonic {instruction['mnemonic']}"
        f" for register {register}"
    )


###########################################################################
# PPU Background Pixel Colour Utils
###########################################################################

def _nametable_byte_from_pixel(ppu: Any, x: int, y: int) -> int:
    """
    "A nametable is a 1024 byte area of memory used by the PPU to
    lay out backgrounds. Each byte in the nametable controls one
    8x8 pixel character cell, and each nametable has 30 rows of
    32 tiles each, for 960 ($3C0) bytes; the rest is used by each
    nametable's attribute table. With each tile being 8x8 pixels,
    this makes a total of 256x240 pixels in one map, the same size
    as one full screen."
    Because we're operating on the lowest level of granularity,
    the pixel, we need to resolve it to the nametable tile, which
    is made up of 8x8 pixels.
    Summarized:
    * 8x8 pixel tiles.
    * 30 rows of 32 tiles each in a nametable.
    * 960 bytes (0x3c0).
    * each tile is 8x8 so 256x240 pixels in one map.
    """
    # This gives us the row, column of the tile in the 32x30
    # space of tiles, which we then need to convert into an address.
    # E.g. pixel (8, 0) =  tile (8 // 8, 8 // 0) = tile (1, 0).
    # Dividing by 8 is the same as shifting right 3 times (2^3).
    tile_x = x >> 3
    tile_y = y >> 3
    # tile_y increments imply that we've gone through a whole row
    # of tiles, each of which is a byte each. A row of pixels is
    # 256 pixels, so 256/8 bytes = 32 tiles or 32 bytes.
    tile_address_offset = tile_x + tile_y * 0x20
    nametable_address = ppu._base_nametable_address + tile_address_offset
    nametable_byte = ppu.memory.read_one(nametable_address)
    return nametable_byte


def _attribute_table_byte_from_pixel(ppu: Any, x: int, y: int) -> int:
    """
    See _nametable_byte_from_pixel.
    """
    # "Each byte controls the palette of a 32×32 pixel or 4×4 tile part
    # of the nametable and is divided into four 2-bit areas. Each area
    # covers 16×16 pixels or 2×2 tiles, the size of a [?] block in Super
    # Mario Bros. Given palette numbers topleft, topright, bottomleft,
    # bottomright, each in the range 0 to 3, the value of the byte is
    # ..."
    # Once we have the attribute table byte we can then figure out the
    # colour bits:
    # 7654 3210
    # |||| ||++- Color bits 3-2 for top left quadrant of this byte
    # |||| ++--- Color bits 3-2 for top right quadrant of this byte
    # ||++------ Color bits 3-2 for bottom left quadrant of this byte
    # ++-------- Color bits 3-2 for bottom right quadrant of this byte
    # https://wiki.nesdev.com/w/index.php/PPU_attribute_tables

    # It's at the end of the nametable, so if the nametable
    # starts at 0x2000, then the attribute table starts at
    # 0x23c0 and ends at 0x2400.
    # The attribute table is divided into an 8x8 grid giving us 64
    # bytes (0x40).

    # To figure out the x we just divide with rounding by 32 since we have
    # 32 tiles going horizontally.
    # E.g. 256/32 = 8 (the 8th tile for the last pixel) or 128/32 = 4
    # (the middle tile for the 128th pixel)
    # Dividing by 32 is the same as shifting right by 5 (2^5 = 32)
    attrib_x = x >> 5
    # Technically, we only have 240 pixels vertically which is 30 tiles
    # going down in the nametable. However, the attribute grid is 8x8,
    # we just dont need to lower bits of the attribute bytes on the last
    # row.
    attrib_y = y >> 5

    # 8 bytes per row, where an increment in attrib_y means we've gone
    # down an entire row.
    # So at x = 1, y = 1, we're on byte 9.
    # at x = 7, y = 7 we're on byte 63 (the last one).
    attribute_table_offset = attrib_x + attrib_y * 0x8

    # Don't forget to find the real address in memory by adding it to
    # the nametable base + the offset to the beginning of the attribute
    # table.
    attribute_table_address = ppu._base_nametable_address + 0x3C0
    attribute_table_address += attribute_table_offset
    if not 0x2000 <= attribute_table_address <= 0x3000:
        raise Exception(f'Bad attribute table address: {attribute_table_address}')
    attribute_table_byte = ppu.memory.read_one(attribute_table_address)
    return attribute_table_byte


def _pattern_table_bytes(ppu: Any, x: int, y: int) -> Tuple[int, int]:
    """
    Returns the high and low pattern table byte using the nametable byte's value
    as an index into the pattern table. This index tells us where in the pattern
    table we should get enough data for 16x16 pixels worth of information. Because
    each chunk of data is 16 bytes, we need to multiply the index by 0x10 (16) to
    get to the next chunk of 16 bytes.
    The PPUCTRL register also controls the base address of the pattern table so we
    need to account for that as well. Since a nametable tile is only for 8x8 pixels,
    we end up with more information than we need.
    We pull a high and low byte from the pattern table. This is enough for 8 pixels'
    worth of data since we need to combine the bytes together. The high byte's bits
    become the high bits for each of the 8 pixels, while the low byte's bits are
    the low ones.
    For example:
    high byte: 0x4, in binary: 0000 0100
    low byte: 0x3, inbinary: 0000 0011
    combine bits:
    0-0, 0-0, 0-0, 0-0 (upper 4 bits of high and low byte)
    0-0, 1-0, 0-1, 0-1 (lower 4 bits of high and low byte)

    The values that are produced from this combination are the indices into the
    background palettes. For example if at the pixel we got 0b10, then we know
    we need to access background palette 3 (0 indexed, so 0, 1, 2, 3).
    See here for more info:
    https://wiki.nesdev.com/w/index.php/PPU_programmer_reference#Pattern_tables
    """
    # This value should already be stored in the background_state.
    nametable_byte = ppu.background_state['nametable_byte']
    pattern_table_start = 0x1000 if ppu.PPUCTRL & 0x10 else 0x0
    pattern_table_byte_address = pattern_table_start + nametable_byte * 0x10

    # We know that the pixel is in one of 32x30 tiles, so if we divide
    # the pixel by 8 on x and y we get back to the tilespace coordinates
    # which we did for the nametable. The next step is to see what the
    # remainder of having done so is because that says how far we've stepped
    # pixelwise (of the 8x8 pixels) into the tile.

    # Also I thought initially it should be (0x1 << x_offset_into_tile)
    # for the mask where x_offset_into_tile is just x % 8 but that actually
    # mirrors every pattern defined in the byte because we then end up
    # reading from right to left, when we know the entire pattern is laid
    # out from left to right. So another option could be to reorder the byte's
    # bits from high -> low, to low -> high where low becomes the upper bits.
    # ANDing by the (modulus - 1) is the same thing as taking the modulus.
    modulus = 8 - 1
    x_offset_into_tile = 7 - (x & modulus)
    y_offset_into_tile = y & modulus

    # Get high and low byte so we can combine them together.
    # Most demonstrations show this as getting 16 bytes so
    # we can build a 4x4 (16 byte) grid, but we only need
    # one byte (if that) for the current pattern.
    pattern_low_byte = ppu.memory.read_one(pattern_table_byte_address + y_offset_into_tile)
    pattern_high_byte = ppu.memory.read_one(pattern_table_byte_address + y_offset_into_tile + 8)
    return pattern_high_byte, pattern_low_byte


def _get_pixel_bits_from_pattern_table(ppu: Any, x: int, y: int) -> int:
    # We know that the pixel is in one of 32x30 tiles, so if we divide
    # the pixel by 8 on x and y we get back to the tilespace coordinates
    # which we did for the nametable. The next step is to see what the
    # remainder of having done so is because that says how far we've stepped
    # pixelwise (of the 8x8 pixels) into the tile.

    # These values should already be in the state.
    pattern_high_byte = ppu.background_state['pattern_table_high_byte']
    pattern_low_byte = ppu.background_state['pattern_table_low_byte']

    # Also I thought initially it should be (0x1 << x_offset_into_tile)
    # for the mask where x_offset_into_tile is just x % 8 but that actually
    # mirrors every pattern defined in the byte because we then end up
    # reading from right to left, when we know the entire pattern is laid
    # out from left to right. So another option could be to reorder the byte's
    # bits from high -> low, to low -> high where low becomes the upper bits.
    # ANDing by the (modulus - 1) is the same thing as taking the modulus.
    modulus = 8 - 1
    x_offset_into_tile = 7 - (x & modulus)
    y_offset_into_tile = y & modulus

    pixel_low_bit = pattern_low_byte & (0x1 << x_offset_into_tile)
    pixel_high_bit = pattern_high_byte & (0x1 << x_offset_into_tile)
    # Now the pixel_high_bit needs to be shifted 1 and added
    # to the low bit so that it makes a value from 0 to 3 which is
    # an index into the palette
    pixel_high_bit <<= 1
    pixel_bits = pixel_low_bit + pixel_high_bit
    # Just one bit for now. Since we ANDed we can shift everything back
    # to get the lowest bit.
    pixel_bits >>= x_offset_into_tile

    # if pixel_bits > 3:
    #     raise Exception(f"Pixel bits is 3 at most, got {pixel_bits}.")

    return pixel_bits


def _palette_bytes_from_attribute_table(ppu: Any, x: int, y: int) -> int:
    """
    A nametable tile is subdivided into pixel quadrants of 4x4 pixels in size.
    Once we know which quadrant the pixel is in, it lets us know which of the
    four background palettes to use for that entire quadrant's pixels.
    After that we can take the 0-3 pixel bits as an index into the palette.
    Quadrants are the bits of the attribute_table_byte:

    0 2
    1 3

    So the top left will be the first 2 bits, which is at max 3 (but 4 values
    including 0) for any pixels in that quadrant.
    """
    # This value should already be in the state.
    attribute_table_byte = ppu.background_state['attribute_table_byte']

    # We know the attribute table gives us 8x8 tiles that are then subdivided
    # into these 4 quadrants. By diving by 16 (32 / 2) we'll get that
    # same subdivision on the pixel along the x axis. Only multiply by 2 because
    # there are only 2 quadrants going along x, and another 2 going along y.
    # We do the same thing for y, since we've divided y by 32 even if we're
    # only using 240 out of 256 pixels of data for it.
    # Dividing by 16 is the same as shifting right by 4 (2^4 = 16)
    quads_x = x >> 4
    quads_y = y >> 4

    # We know that along the x we alternate from quadrant 0 and I for even
    # rows, and II and III for odd rows:
    # row 1: 0, 1, 0, 1, 0, 1...
    # row 2: 2, 3, 2, 3, 1, 3...
    # Along the y axis is a similar story, except it's 0, II for even
    # columns and I and III for odd columns.
    # So if the row is odd and the column is odd it's in quadrant III
    # If row is even and column is odd it's in quadrant I.

    # quads_x % 2 == 0 is the same as just checking if the 1 bit is
    # set. Because any number that can't be divided evenly by 2 has
    # to have the 1 bit set since everything else is a 2^n (as is
    # 1, it's 2^0 but it's a special case here...)
    even_row = quads_x & 1 == 0
    even_column = quads_y & 1 == 0

    background_palette_index = None
    # FIXME
    # Could be done with bit operations: by figuring out even_row
    # and even_column we could then just use that value as the bit
    # shift to get the quadrant. It would just take some time
    # to figure out on paper.
    # ANDing with 0x3 makes sure to keep all bits that were already
    # set since anything ANDed with 0b11 will preserve the lowest
    # two bits.
    if even_row and even_column:
        top_left = attribute_table_byte & 0x3
        background_palette_index = top_left
    elif even_row and not even_column:
        top_right = (attribute_table_byte >> 0x4) & 0x3
        background_palette_index = top_right
    elif not even_row and even_column:
        bottom_left = (attribute_table_byte >> 0x2) & 0x3
        background_palette_index = bottom_left
    elif not even_row and not even_column:
        bottom_right = (attribute_table_byte >> 0x6) & 0x3
        background_palette_index = bottom_right
    else:
        # This should never happen.
        raise Exception("Impossible to get a background palette index.")

    # Now that we know which palette index to look at, return the bytes
    # at that index.
    palette_bytes = ppu.memory.background_palette(background_palette_index)
    return palette_bytes


def _background_colour_for_pixel(
    ppu: Any,
    x: int,
    y: int,
    use_cache: Optional[bool] = True
) -> int:
    # I'm not doing this, but it's totally possible
    # to reporduce this behaviour more faithfully (i.e.
    # store the value that was fetched for the duration that's
    # right and keep computing pixels off of it...):
    # "Conceptually, the PPU does this 33 times for each scanline:
    # Fetch a nametable entry from $2000-$2FBF.
    # Fetch the corresponding attribute table entry from $23C0-$2FFF and increment the current VRAM address within the same row.
    # Fetch the low-order byte of an 8x1 pixel sliver of pattern table from $0000-$0FF7 or $1000-$1FF7.
    # Fetch the high-order byte of this sliver from an address 8 bytes higher.
    # Turn the attribute data and the pattern table data into palette indices, and combine them with data from sprite data using priority.""

    # Elaborating on the above some more:
    # Based on NTSC timing:
    # It takes 8 cycles of work to fetch all the data that
    # we need to compute one pixel which is why they come in 8
    # byte chunks.
    # It's at the end of the current nametable and we also need to
    # offset it.

    if x & 7 == 0 or not use_cache:
        # Byte-size data can be cached for every 8 pixels in a row, since
        # each pixel is only using one bit of it. So at every x % 8 == 0
        # we'll need to fetch a new one rather than reusing them.
        # x & 7 is the same as x % 8 as far as testing for zero.
        nametable_byte = _nametable_byte_from_pixel(ppu, x, y)
        ppu.background_state['nametable_byte'] = nametable_byte

        attribute_table_byte = _attribute_table_byte_from_pixel(ppu, x, y)
        ppu.background_state['attribute_table_byte'] = attribute_table_byte

        pattern_high_byte, pattern_low_byte = _pattern_table_bytes(ppu, x, y)
        ppu.background_state['pattern_table_high_byte'] = pattern_high_byte
        ppu.background_state['pattern_table_low_byte'] = pattern_low_byte

    pixel_bits = _get_pixel_bits_from_pattern_table(ppu, x, y)
    palette_bytes = _palette_bytes_from_attribute_table(ppu, x, y)

    # We finally get the specific colour for this pixel from the palette
    # which then needs to be looked up anyways.
    # if x % 8 == 0 or y % 8 == 0:
    #     # Debug nametable grid with yellow.
    #     return 0x37
    # if x % 0x20 == 0 or y % 0x20 == 0:
    #     # Debug attribute grid with red.
    #     return 0x16
    # if x % 0x10 == 0 or y % 0x10 == 0:
    #     # Debug attributes quadrants with pink.
    #     return 0x25

    # TODO
    # Possibly use for debug colouring?
    # return [0xf0, 0x30, 0x11, 0x16][pixel_bits]
    return palette_bytes[pixel_bits]


def colour_for_pixel(ppu: Any, x: int, y: int) -> int:
    # TODO
    # Assuming everything is a BG pixel for now.
    # There is a way to prioritize which one to fetch:
    # https://wiki.nesdev.com/w/index.php/PPU_rendering#Preface
    # Check out the "Priority multiplexer decision table"
    # sprite_colour = _sprite_colour_for_pixel(ppu, x, y)
    # background_colour = _background_colour_for_pixel(ppu, x, y)
    # return background_colour if not sprite_colour else sprite_colour
    return _background_colour_for_pixel(ppu, x, y)


###########################################################################
# PPU Sprite Colour Utils
###########################################################################

def _get_pixel_bits_from_pattern_table_for_sprite(
    ppu: Any,
    sprite_tile: int
) -> list:
    # TODO
    # Get pattern for sprite's 'tile' value:
    # So first we need to know if it's 8x8 or 8x16, if it's 8x8 we just use
    # PPUCTRL for the base address.
    # If it's 8x16 here is the way to get the the sprite pattern:
    # https://wiki.nesdev.com/w/index.php/PPU_OAM#Byte_1
    # "For 8x16 sprites, the PPU ignores the pattern table selection and selects a pattern table from bit 0 of this number.

    # 76543210
    # ||||||||
    # |||||||+- Bank ($0000 or $1000) of tiles
    # +++++++-- Tile number of top of sprite (0 to 254; bottom half gets the next tile)

    # Thus, the pattern table memory map for 8x16 sprites looks like this:

    #     $00: $0000-$001F
    #     $01: $1000-$101F
    #     $02: $0020-$003F
    #     $03: $1020-$103F
    #     $04: $0040-$005F
    #     [...]
    #     $FE: $0FE0-$0FFF
    #     $FF: $1FE0-$1FFF"
    w, h = ppu._sprite_size
    if w != 8 and h != 8:
        raise Exception("Can't handle 8x16 sprites at the moment.")

    # NOTE
    # This is different from the background because that looks at
    # ppu.PPUCTRL & 0x10, not 0x8.
    # TODO
    # Move this to PPU property?
    pattern_table_start = 0x1000 if ppu.PPUCTRL & 0x8 else 0x0
    pattern_table_byte_address = pattern_table_start + sprite_tile * 0x10
    # Unlike the other bit functions we'll get the entire grid of
    # bits since we're just overwriting the existing bg bytes at
    # the end of the frame.

    grid = []
    for i in range(8):
        if i >= len(grid):
            grid.append([])
        low_byte = ppu.memory.read_one(pattern_table_byte_address + i)
        high_byte = ppu.memory.read_one(pattern_table_byte_address + i + 8)
        for j in range(8):
            # Deal with the high and low bits now.
            high_bit = (high_byte >> (7 - j)) & 0x1
            high_bit <<= 1
            low_bit = (low_byte >> (7 - j)) & 0x1
            bits = high_bit + low_bit
            grid[i].append(bits)
    return grid


def render_sprites(ppu: Any) -> None:
    # FIXME
    # This just renders over the background at the end of the frame. That is,
    # it's basically 'blitting' the sprite in over whatever we already rendered
    # from the BG which is inefficient and not how the PPU sprite rendering
    # even works.
    # In any case it should be good enough for now on the way to accuracy
    # and compatibility.

    # FIXME
    # Rendering the first sprite for now only
    sprite_bytes = ppu._oam.sprite_at_index(0)
    sprite_y, tile, attribute, sprite_x = sprite_bytes

    if sprite_y == 0xff:
        # There's nothing to be done with the sprite if this is the y value.
        return

    # if ppu._clock.cpu_cycles == 655183:
    #     breakpoint()

    # Get the palette:
    # Attributes
    # 76543210
    # ||||||||
    # ||||||++- Palette (4 to 7) of sprite
    # |||+++--- Unimplemented
    # ||+------ Priority (0: in front of background; 1: behind background)
    # |+------- Flip sprite horizontally
    # +-------- Flip sprite vertically
    # Two lowest bits, then shift
    palette_index = ((attribute & 0x3) + 0x4)
    palette_bytes = ppu.memory.sprite_palette(palette_index)

    # This is the pattern that then lets us know what to colour each
    # pixel. The sprite_x and sprite_y are the top left offset to let
    # us know where to start relative to the frame 'origin'.
    bits_grid = _get_pixel_bits_from_pattern_table_for_sprite(ppu, tile)

    pixel_x = sprite_x
    pixel_y = sprite_y

    for row in bits_grid:
        for palette_index in row:
            colour = palette_bytes[palette_index]
            # Where to draw the colour?
            pixel_index = pixel_x + pixel_y * 0x100
            # Set it to 0x3c for a debug value.
            ppu._pixels[pixel_index] = colour
            pixel_x += 1
        # Reset it to the beginning of where the sprite should be drawn
        # because a row of pixels was just coloured in.
        pixel_x = sprite_x
        pixel_y += 1

    # TODO
    # Handle priority between sprite and BG?
