import ctypes
from typing import Any
from typing import Optional
from typing import Tuple

from constants import AddressingMode
from constants import PPURegister
from ppu_utils import resolve_register


def _is_bit_n_set(value: int, bit: int) -> int:
    """
    If a bit at a given offset is set, return True
    otherwise False.

    Example: value: 0x80:, bit: 7
    # 1 0 0 0 0 0 0 0
    # 0 0 0 0 0 0 0 1

    Example: value: 0x02:, bit: 1
    # 0 0 0 0 0 0 1 0
    # 0 0 0 0 0 0 0 1
    """
    return value & (2 << (bit - 1))


def _crossed_page(address: int, next_address: int) -> bool:
    # Addresses all fit into some page. Pages are bins of 256
    # bytes. So address 0x0 will reference the first page (the first
    # bin). 0x100 is past the first 256 bytes so it'll be in the
    # next page, and so on.
    # If we divide by 0x100 without remainders, we can figure out
    # which page an address belongs to. If `address` and
    # `next_address` aren't in the same page then we've crossed
    # pages.
    # Dividing by 0x100 (256) is the same as shifting right by 8
    # (since 2^8 is 256)
    page_index_a = address >> 8
    page_index_b = next_address >> 8
    return page_index_a != page_index_b


def _get_zero_page_address(instruction_bytes: bytearray) -> int:
    # Assumes that we have enough data from the operand to
    # get uint8.
    address = instruction_bytes[1]
    return address


def _get_absolute_address(instruction_bytes: bytearray) -> int:
    # Assumes that we have enough data from the operand to
    # get uint16.
    low = instruction_bytes[1]
    high = instruction_bytes[2] << 0x8
    address = high + low
    return address


def _get_absolute_x(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> Tuple[int, int]:
    address = _get_absolute_address(instruction_bytes)
    next_address = address + cpu.x
    # Not all page crossings involve a penalty.
    has_page_crossing_penalty = 'page_crossing_cycles' in instruction
    if _crossed_page(address, next_address) and has_page_crossing_penalty:
        # Potential penalty for page crossing for all absolute_x
        # instructions. It may seem architecturally strange to do
        # this mutation of the cycles here, but this is exactly
        # where we can capture all this information (at address
        # resolution time).
        cpu._clock.cpu_cycles += instruction['page_crossing_cycles']

    # TODO
    # Watch for overflow. This would be better replaced with integers
    # that handle the overflow themselves...
    next_address &= 0xffff
    return next_address, cpu.memory.read_one(next_address)


def _get_absolute_y(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> Tuple[int, int]:
    address = _get_absolute_address(instruction_bytes)
    next_address = address + cpu.y
    # Not all page crossings involve a penalty.
    has_page_crossing_penalty = 'page_crossing_cycles' in instruction
    if _crossed_page(address, next_address) and has_page_crossing_penalty:
        # Potential penalty for page crossing for all absolute_y
        # instructions. It may seem architecturally strange to do
        # this mutation of the cycles here, but this is exactly
        # where we can capture all this information (at address
        # resolution time).
        cpu._clock.cpu_cycles += instruction['page_crossing_cycles']

    # TODO
    # Watch for overflow. This would be better replaced with integers
    # that handle the overflow themselves...
    next_address &= 0xffff
    return next_address, cpu.memory.read_one(next_address)


def _get_indirect_x(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> int:
    # We need to compute the where the pointer is stored,
    # grab the pointer, then use it to look up the actual
    # value.
    base = _get_zero_page_address(instruction_bytes)
    pointer_address = base + cpu.x
    return pointer_address


def _get_indirect_y(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> int:
    # Example functionality:
    # At d922 we need to read
    # * instruction includes: 0x89
    # * read address at 0x89: 0x00 0x03 (0x0300 for endianness)
    # * read one byte from 0x300 + y (where y is 0)
    # * byte should be 0x89

    # At D940 we need to read
    # * instruction includes: 0x97
    # * read address at 0x97: 0xff 0xff (0xffff for endianness)
    # * read one byte from 0xffff + y (where y is 34)
    # * byte should be 0xa3 after we end up wrapping around
    # to read from 0x33

    pointer_address = _get_zero_page_address(instruction_bytes)
    # Should be uint16.
    address = cpu.memory.read_from_zero_page_uint16(pointer_address)
    next_address = address + cpu.y
    has_page_crossing_penalty = 'page_crossing_cycles' in instruction
    if _crossed_page(address, next_address) and has_page_crossing_penalty:
        # Potential penalty for page crossing for all indirect_y
        # instructions. It may seem architecturally strange to do
        # this mutation of the cycles here, but this is exactly
        # where we can capture all this information (at address
        # resolution time).
        cpu._clock.cpu_cycles += instruction['page_crossing_cycles']
    # Handle wrap around.
    next_address &= 0xffff
    return next_address


def _data_for_mode(
    cpu: Any,
    instruction: dict,
    instruction_bytes: bytearray,
) -> Tuple[int, int]:
    """
    Given an addressing_mode and the data that came with the opcode
    (its operand[s]), figure out what data is being operated on by
    the instruction and where. I.e. do we need to look in memory for
    the data? Is it provided inline with the opcode?
    """
    # TODO
    # There is a fair amount of time spent here.

    address = None
    value = None
    addressing_mode = instruction['addressing_mode']

    if addressing_mode == AddressingMode.ABSOLUTE:
        address = _get_absolute_address(instruction_bytes)
        value = cpu.memory.read_one(address)
    elif addressing_mode == AddressingMode.ABSOLUTE_X:
        address, value = _get_absolute_x(cpu, instruction, instruction_bytes)
    elif addressing_mode == AddressingMode.ABSOLUTE_Y:
        address, value = _get_absolute_y(cpu, instruction, instruction_bytes)
    elif addressing_mode == AddressingMode.ACCUMULATOR:
        value = cpu.a
    elif addressing_mode == AddressingMode.INDIRECT:
        address = _get_absolute_address(instruction_bytes)
        # Overwrite the address of where we actually want to jump to.
        address = cpu.memory.read_two(address)
    elif addressing_mode == AddressingMode.INDIRECT_X:
        # It's indexed by the x register.
        pointer_address = _get_indirect_x(cpu, instruction, instruction_bytes)
        address = cpu.memory.read_from_zero_page_uint16(pointer_address)
        value = cpu.memory.read_one(address)
    elif addressing_mode == AddressingMode.INDIRECT_Y:
        # # It's indexed by the y register.
        address = _get_indirect_y(cpu, instruction, instruction_bytes)
        value = cpu.memory.read_one(address)
    elif addressing_mode == AddressingMode.IMMEDIATE:
        # It's inline.
        value = instruction_bytes[1]
    elif addressing_mode == AddressingMode.ZEROPAGE:
        address = _get_zero_page_address(instruction_bytes)
        value = cpu.memory.read_one(address)
    elif addressing_mode == AddressingMode.ZEROPAGE_X:
        address = _get_zero_page_address(instruction_bytes)
        address += cpu.x
        # TODO
        # Watch for overflow. This would be better replaced with integers
        # that handle the overflow themselves...
        address &= 0xff
        value = cpu.memory.read_from_zero_page_uint8(address)
    elif addressing_mode == AddressingMode.ZEROPAGE_Y:
        address = _get_zero_page_address(instruction_bytes)
        address += cpu.y
        # TODO
        # Watch for overflow. This would be better replaced with integers
        # that handle the overflow themselves...
        address &= 0xff
        value = cpu.memory.read_from_zero_page_uint8(address)

    return value, address


def _store_data_for_mode(
    cpu: Any,
    instruction: dict,
    value: int,
    address: int,
) -> None:
    """
    Similar to _data_for_mode, if we need to do something with the
    result of an instruction, this handles it. Some operations and
    addressing modes don't make any sense for this, so we should error
    if it's ever called with those.
    """
    # TODO
    # There is a fair amount of time spent here.

    addressing_mode = instruction['addressing_mode']

    # Assuming this is only ever writing 1 byte. That might
    # need to be changed for multiple value writing is supported.
    not_supported = {
        AddressingMode.IMMEDIATE,
        AddressingMode.IMPLIED,
        AddressingMode.INDIRECT,
        AddressingMode.RELATIVE,
    }
    if addressing_mode in not_supported:
        raise Exception(cpu.pc, addressing_mode)

    if addressing_mode == AddressingMode.ACCUMULATOR:
        cpu.a = value
        return

    cpu.memory.write(value, address)


# Anything that reads or writes from the _bus object on the CPU is
# doing it for the following reason:
# https://wiki.nesdev.com/w/index.php/PPU_programmer_reference#Ports
# "The PPU has an internal data bus that it uses for communication
# with the CPU. This bus, called _io_db in Visual 2C02 and PPUGenLatch
# in FCEUX,[1] behaves as an 8-bit dynamic latch due to capacitance
# of very long traces that run to various parts of the PPU. Writing
# any value to any PPU port, even to the nominally read-only PPUSTATUS,
# will fill this latch. Reading any readable port (PPUSTATUS, OAMDATA,
# or PPUDATA) also fills the latch with the bits read. Reading a
# nominally "write-only" register returns the latch's current value,
# as do the unused bits of PPUSTATUS. This value begins to decay after
# a frame or so, faster once the PPU has warmed up, and it is likely
# that values with alternating bit patterns (such as $55 or $AA) will
# decay faster.[2]


def _ADC(cpu: Any, instruction: dict, value: int) -> None:
    # TODO
    # Find a better way to implement add-with-carry that lets us do it
    # the proper way with 2's complements and saner overflow/negatives
    # handling and all that.

    # If we have a carry bit we want to account for it in the next
    # addition. This is because the carry bit may have been set
    # by previous ADCs and we need to keep 'carry'ing that bit forward.
    carry = int(cpu._carry)

    # Is cpu.a negative?
    # Is the value we're adding negative?
    # If both are positive, neither will have the negative
    # bit set.
    positive_operands = not _is_bit_n_set(value, 0x7) and not _is_bit_n_set(cpu.a, 0x7)
    cpu.a += (value + carry)

    # We overflowed into the negative bit if we tried to add
    # two positive numbers and ended up with the highest bit
    # (bit 7) set to 1.
    overflowed = positive_operands and _is_bit_n_set(cpu.a, 0x7)
    cpu._set_overflow(overflowed)

    # The 9th bit of the result is stored in the carry flag.
    # (If we're starting at 0 it's the 8th bit)
    cpu._set_carry(_is_bit_n_set(cpu.a, 0x8))
    cpu._set_negative(_is_bit_n_set(cpu.a, 0x7))

    # Clear any bits that would result in a being greater
    # than 1 byte, which ensures that we clear out any
    # overflowed value.
    cpu.a &= 0xff

    # Now that we've fixed any overflowed value putting a back
    # in the range of 0->255, we can see if it's zero. This makes
    # sense when we overflowed into the 8th bit (i.e. a byte isn't
    # enough to hold the result).
    # that a is within the [0, 255]
    cpu._set_zero(cpu.a == 0)


def _resolve_displacement(instruction_bytes: bytearray) -> int:
    displacement = instruction_bytes[1]
    # Displacement can be forwards and backwards. For this reason we need
    # to treat this as a signed value.
    if displacement > 0x7f:
        return ((0x100 - displacement) * -1)
    else:
        return displacement

def _AND(cpu: Any, instruction: dict, value: int) -> None:
    cpu.a &= value
    cpu._set_zero(cpu.a == 0)
    cpu._set_negative(_is_bit_n_set(cpu.a, 0x7))


def _ASL(cpu: Any, instruction: dict, value: int) -> int:
    cpu._set_carry(_is_bit_n_set(value, 0x7))
    value <<= 1
    # In case we multiplied over the storage of 1 byte.
    value &= 0xff
    cpu._set_zero(value == 0)
    cpu._set_negative(_is_bit_n_set(value, 0x7))
    return value


def _CMP(cpu: Any, instruction: dict, value: int) -> None:
    temp = cpu.a - value
    cpu._set_carry(cpu.a >= value)
    cpu._set_zero(cpu.a == value)
    cpu._set_negative(_is_bit_n_set(temp, 7))


def _CPX(cpu: Any, instruction: dict, value: int) -> None:
    temp = cpu.x - value
    cpu._set_carry(cpu.x >= value)
    cpu._set_zero(cpu.x == value)
    cpu._set_negative(_is_bit_n_set(temp, 7))


def _CPY(cpu: Any, instruction: dict, value: int) -> None:
    temp = cpu.y - value
    cpu._set_carry(cpu.y >= value)
    cpu._set_zero(cpu.y == value)
    cpu._set_negative(_is_bit_n_set(temp, 7))


def _DEC(cpu: Any, instruction: dict, address: int) -> None:
    # TODO
    # This may have to support uint16s.
    value = cpu.memory.read_one(address)
    value -= 1

    # I believe this supports underflows (e.g. 0 - 1 = 0xff) in
    # the 1-byte case. If we need support for 2 bytes it'll
    # have to change.
    value &= 0xff
    cpu._set_zero(value == 0)
    cpu._set_negative(_is_bit_n_set(value, 0x7))
    cpu.memory.write(value, address)


def _DCP(cpu: Any, instruction: dict, address: int) -> None:
    # Undocumented instruction:
    # "Equivalent to DEC value then CMP value, except supporting
    # more addressing modes. LDA #$FF followed by DCP can be used
    # to check if the decrement underflows, which is useful for
    # multi-byte decrements."

    # Grab the decremented value from where we wrote it after _DEC.
    _DEC(cpu, instruction, address)
    value = cpu.memory.read_one(address)

    # Let CMP do its job and also increment the pc register.
    return _CMP(cpu, instruction, value)


def _EOR(cpu: Any, instruction: dict, value: int) -> None:
    cpu.a ^= value
    cpu._set_zero(cpu.a == 0)
    cpu._set_negative(_is_bit_n_set(cpu.a, 7))


def _INC(cpu: Any, instruction: dict, address: int) -> None:
    # TODO
    # This may have to support uint16s.
    value = cpu.memory.read_one(address)
    value += 1
    value &= 0xff
    cpu._set_zero(value == 0)
    cpu._set_negative(_is_bit_n_set(value, 0x7))
    cpu.memory.write(value, address)


def _ISB(cpu: Any, instruction: dict, address: int) -> None:
    # Undocumented instruction:
    # "Equivalent to INC value then SBC value, except supporting
    # more addressing modes."

    _INC(cpu, instruction, address)

    # Need to read back the value that was stored during _INC
    value = cpu.memory.read_one(address)

    # Let SBC do its job and also increment the pc register.
    _SBC(cpu, instruction, value)

    # Check the status again of the value and set flags
    # accordingly. This part is repeated from SBC.
    cpu._set_zero(cpu.a == 0)
    cpu._set_negative(_is_bit_n_set(cpu.a, 0x7))
    return value


def _LAX(cpu: Any, instruction: dict, value: int) -> None:
    _LDA(cpu, instruction, value)
    _TAX(cpu, instruction)


def _LDA(cpu: Any, instruction: dict, value: int) -> None:
    cpu.a = value
    cpu._set_zero(cpu.a == 0)
    cpu._set_negative(_is_bit_n_set(cpu.a, 0x7))


def _LDX(cpu: Any, instruction: dict, value: int) -> None:
    cpu.x = value
    cpu._set_zero(cpu.x == 0)
    cpu._set_negative(_is_bit_n_set(cpu.x, 0x7))


def _LDY(cpu: Any, instruction: dict, value: int) -> None:
    cpu.y = value
    cpu._set_zero(cpu.y == 0)
    cpu._set_negative(_is_bit_n_set(cpu.y, 0x7))


def _LSR(cpu: Any, instruction: dict, value: int) -> None:
    cpu._set_carry(bool(value & 0x1))
    value >>= 1
    cpu._set_zero(value == 0)
    cpu._set_negative(_is_bit_n_set(value, 0x7))
    return value


def _ORA(cpu: Any, instruction: dict, value: int) -> None:
    cpu.a |= value
    cpu._set_zero(cpu.a == 0)
    cpu._set_negative(_is_bit_n_set(cpu.a, 7))


def _ROL(cpu: Any, instruction: dict, value: int) -> int:
    carry = cpu._carry
    next_carry = _is_bit_n_set(value, 0x7)
    value <<= 1
    if carry:
        value |= 0x01
    else:
        value &= 0xfe
    cpu._set_carry(next_carry)
    # In case we multiplied over the storage of 1 byte.
    value &= 0xff
    cpu._set_zero(value == 0)
    cpu._set_negative(_is_bit_n_set(value, 0x7))
    return value


def _RLA(cpu: Any, instruction: dict, value: int) -> int:
    # Undocumented instruction:
    # "Equivalent to ROL value then AND value, except supporting
    # more addressing modes. LDA #$FF followed by RLA is an efficient
    # way to rotate a variable while also loading it in A."

    value = _ROL(cpu, instruction, value)
    _AND(cpu, instruction, value)
    return value


def _ROR(cpu: Any, instruction: dict, value: int) -> int:
    carry = cpu._carry
    next_carry = value & 0x1
    value >>= 1
    # Set or unset the seventh bit if the carry was set.
    if carry:
        value |= 0x80
    else:
        value &= 0x7f
    cpu._set_carry(next_carry)
    cpu._set_zero(value == 0)
    cpu._set_negative(_is_bit_n_set(value, 0x7))
    return value


def _RRA(cpu: Any, instruction: dict, value: int) -> int:
    # Undocumented instruction:
    # "Equivalent to ROR value then ADC value, except supporting
    # more addressing modes. Essentially this computes A + value / 2,
    # where value is 9-bit and the division is rounded up."

    value = _ROR(cpu, instruction, value)
    _ADC(cpu, instruction, value)
    return value


def _SAX(cpu: Any, instruction: dict, address: int) -> None:
    # Undocumented instruction:
    # "Stores the bitwise AND of A and X. As with STA and STX, no
    # flags are affected."
    cpu.memory.write(cpu.x & cpu.a, address)


def _SBC(cpu: Any, instruction: dict, value: int) -> None:
    # TODO
    # Find a better way to implement subtract-with-carry that lets us do it
    # the proper way with 2's complements and saner overflow/negatives
    # handling and all that.

    def maybe_set_overflow(a: int, b: int, carry: int) -> int:
        # Signed subtraction, these are overflow cases becuse
        # with 0x0 -> 0xFF we get -128 -> 127, any value
        # that doesn't fall in that range is overflowed. Of course,
        # to see this, we now need to treat our values as though
        # they were signed to begin with. This let's us treat
        # both values as signed 8-bit integers so we can then
        # properly subtract them.
        # TODO
        # This should be replaced with a class as described in the
        # TODO.md document so that we can just subtract the values
        # as signed 8-bit integers without needing this conversion.
        s_a = ctypes.c_int8(a).value
        s_b = ctypes.c_int8(b).value
        outcome = s_a - s_b - carry
        cpu._set_overflow(outcome < -128 or outcome > 127)

    maybe_set_overflow(cpu.a, value, int(not cpu._carry))

    # TODO
    # Wraps around possibly. Fixing that is handled below
    # but it should just be done in its own class.
    cpu.a -= value
    cpu.a -= int(not cpu._carry)

    # "The carry flag is set if the result is greater than or
    # equal to 0. The carry flag is reset when the result is
    # less than 0, indicating a borrow."
    cpu._set_carry(cpu.a >= 0)

    # "The negative flag is set if the result in the accumulator
    # has bit 7 on, otherwise it is reset."
    cpu._set_negative(cpu.a < 0)
    cpu._set_zero(cpu.a == 0)

    # Back to unsigned form where we're just dealing with
    # byte values between 0x0 and 0xff. This fixes any
    # wraparound we'd have gotten from cpu.a -= value above.
    cpu.a &= 0xff


def _SLO(cpu: Any, instruction: dict, value: int) -> int:
    # Undocumented instruction:
    # "Equivalent to ASL value then ORA value, except supporting
    # more addressing modes. LDA #0 followed by SLO is an efficient
    # way to shift a variable while also loading it in A."

    value = _ASL(cpu, instruction, value)
    _ORA(cpu, instruction, value)
    return value


def _SRE(cpu: Any, instruction: dict, value: int) -> int:
    # Undocumented instruction:
    # "Equivalent to LSR value then EOR value, except supporting
    # more addressing modes. LDA #0 followed by SRE is an efficient
    # way to shift a variable while also loading it in A."

    value = _LSR(cpu, instruction, value)
    _EOR(cpu, instruction, value)
    return value


def _STA(cpu: Any, instruction: dict, address: int) -> None:
    ppu_register = resolve_register(address)
    if ppu_register is not None:
        # PPU is handling this one, so we need to put it in the bus
        # instead of in memory
        if ppu_register == PPURegister.OAMDMA:
            # OAMDMA is handled differently from other data sharing
            # with the PPU.
            cpu.upload_oamdma_data(cpu.a)
        else:
            cpu._bus.data = cpu.a
    else:
        cpu.memory.write(cpu.a, address)


def _STX(cpu: Any, instruction: dict, address: int) -> None:
    ppu_register = resolve_register(address)
    if ppu_register is not None:
        # PPU is handling this one, so we need to put it in the bus
        # instead of in memory
        if ppu_register == PPURegister.OAMDMA:
            # OAMDMA is handled differently from other data sharing
            # with the PPU.
            cpu.upload_oamdma_data(cpu.x)
        else:
            cpu._bus.data = cpu.x
    else:
        cpu.memory.write(cpu.x, address)


def _STY(cpu: Any, instruction: dict, address: int) -> None:
    ppu_register = resolve_register(address)
    if ppu_register is not None:
        # PPU is handling this one, so we need to put it in the bus
        # instead of in memory
        if ppu_register == PPURegister.OAMDMA:
            # OAMDMA is handled differently from other data sharing
            # with the PPU.
            cpu.upload_oamdma_data(cpu.y)
        else:
            cpu._bus.data = cpu.y
    else:
        cpu.memory.write(cpu.y, address)


def _TAX(cpu: Any, instruction: dict) -> None:
    cpu.x = cpu.a
    cpu._set_zero(cpu.x == 0)
    cpu._set_negative(_is_bit_n_set(cpu.x, 0x7))


def op_ADC(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, _ = _data_for_mode(cpu, instruction, instruction_bytes)
    return _ADC(cpu, instruction, value)


def op_AND(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, _ = _data_for_mode(cpu, instruction, instruction_bytes)
    return _AND(cpu, instruction, value)


def op_ASL(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, address = _data_for_mode(cpu, instruction, instruction_bytes)
    next_value = _ASL(cpu, instruction, value)
    # If the addressing mode is ACCUMULATOR, then the target will
    # be cpu.a, otherwise it's performed on the value.
    _store_data_for_mode(cpu, instruction, next_value, address)


def op_BCC(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    if not cpu._carry:
        displacement = _resolve_displacement(instruction_bytes)
        cpu.pc += displacement
        # An additional cycle if the branch succeeds.
        cpu._clock.cpu_cycles += instruction['branch_cycles']


def op_BCS(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    if cpu._carry:
        displacement = _resolve_displacement(instruction_bytes)
        cpu.pc += displacement
        # An additional cycle if the branch succeeds.
        cpu._clock.cpu_cycles += instruction['branch_cycles']


def op_BEQ(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    # WARNING:
    # This is super finicky. We need to test for page crossing
    # after already moving the PC forward. If we don't, we may
    # get a false positive for page crossing when the PC wasn't
    # moved forward already. This happens at cycle 2605 on nestest
    # because there is a crossing as the PC is incremented but
    # not as a result of just the displacement alone which is what
    # we're really interested in.
    # TODO
    # I imagine it's possible for other branching instructions
    # to have tehse page crossing issues, so watch out for this
    # in other roms.
    cpu.pc += instruction['bytes']
    previous_pc = cpu.pc
    if cpu._zero:
        displacement = _resolve_displacement(instruction_bytes)
        cpu.pc += displacement
        if _crossed_page(previous_pc, cpu.pc):
            # The program counter is also looking at locations in memory
            # and displacing it could cause it to point to a new page.
            # As a result, even these branching instructions can have
            # page penalties.
            cpu._clock.cpu_cycles += instruction['page_crossing_cycles']
        else:
            # An additional cycle if the branch succeeds. It seems like
            # the page crossing penalty cycle and the branching cycle
            # are mutualyl exclusive because in either case it's a
            # branch.
            cpu._clock.cpu_cycles += instruction['branch_cycles']


def op_BIT(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    if cpu._bus.has_data:
        value = cpu._bus.data
    else:
        _, address = _data_for_mode(cpu, instruction, instruction_bytes)
        value = cpu.memory.read_one(address)
    temp = cpu.a & value
    cpu._set_zero(temp == 0)
    cpu._set_overflow(_is_bit_n_set(value, 0x6))
    cpu._set_negative(_is_bit_n_set(value, 0x7))


def op_BNE(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    if not cpu._zero:
        displacement = _resolve_displacement(instruction_bytes)
        cpu.pc += displacement
        # An additional cycle if the branch succeeds.
        cpu._clock.cpu_cycles += instruction['branch_cycles']


def op_BMI(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    if cpu._negative:
        displacement = _resolve_displacement(instruction_bytes)
        cpu.pc += displacement
        # An additional cycle if the branch succeeds.
        cpu._clock.cpu_cycles += instruction['branch_cycles']


def op_BPL(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    if not cpu._negative:
        displacement = _resolve_displacement(instruction_bytes)
        cpu.pc += displacement
        # An additional cycle if the branch succeeds.
        cpu._clock.cpu_cycles += instruction['branch_cycles']


def op_BRK(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    # "The BRK instruction forces the generation of an interrupt request.
    # The program counter and processor status are pushed on the stack then
    # the IRQ interrupt vector at $FFFE/F is loaded into the PC and the break
    # flag in the status set to one."
    # From: http://users.telenet.be/kim1-6502/6502/proman.html#90
    #       The break command causes the microprocessor to go through an inter-
    #  rupt sequence under program control.  This means that the program counter
    #  of the second byte after the BRK is automatically stored on the stack
    #  along with the processor status at the beginning of the break instruction.
    #  The microprocessor then transfers control to the interrupt vector.

    # As the description above says: push the PC that's two bytes after
    # the call to break. This is despite break only being 1 byte as far
    # as instructions go.
    cpu.pc += 2
    cpu.sp = cpu._stack.push(cpu.memory, cpu.sp, cpu.pc)
    cpu.sp = cpu._stack.push(cpu.memory, cpu.sp, cpu.p)
    low = cpu.memory.read_one(0xfffe)
    high = cpu.memory.read_one(0xffff)
    high <<= 8
    cpu.pc = low + high
    cpu._set_bit_5(True)


def op_BVC(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    if not cpu._overflow:
        displacement = _resolve_displacement(instruction_bytes)
        cpu.pc += displacement
        # An additional cycle if the branch succeeds.
        cpu._clock.cpu_cycles += instruction['branch_cycles']


def op_BVS(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    if cpu._overflow:
        displacement = _resolve_displacement(instruction_bytes)
        cpu.pc += displacement
        # An additional cycle if the branch succeeds.
        cpu._clock.cpu_cycles += instruction['branch_cycles']


def op_CLC(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu._set_carry(False)


def op_CLD(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu._set_decimal(False)


def op_CLV(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu._set_overflow(False)


def op_CMP(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, _ = _data_for_mode(cpu, instruction, instruction_bytes)
    return _CMP(cpu, instruction, value)


def op_CPX(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, _ = _data_for_mode(cpu, instruction, instruction_bytes)
    return _CPX(cpu, instruction, value)


def op_CPY(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, _ = _data_for_mode(cpu, instruction, instruction_bytes)
    return _CPY(cpu, instruction, value)


def op_DEC(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    # We're reading and writing to the address, we're not interesed
    # in the existing value there other than to increment it.
    _, address = _data_for_mode(cpu, instruction, instruction_bytes)
    return _DEC(cpu, instruction, address)


def op_DEX(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.x -= 1
    cpu._set_zero(cpu.x == 0)
    cpu._set_negative(_is_bit_n_set(cpu.x, 7))


def op_DEY(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.y -= 1
    cpu._set_zero(cpu.y == 0)
    cpu._set_negative(_is_bit_n_set(cpu.y, 7))


def op_DCP(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    # We're reading and writing to the address, we're not interesed
    # in the existing value there other than to increment it.
    _, address = _data_for_mode(cpu, instruction, instruction_bytes)
    return _DCP(cpu, instruction, address)


def op_EOR(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, _ = _data_for_mode(cpu, instruction, instruction_bytes)
    return _EOR(cpu, instruction, value)


def op_INC(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    # We're reading and writing to the address, we're not interesed
    # in the existing value there other than to increment it.
    _, address = _data_for_mode(cpu, instruction, instruction_bytes)
    return _INC(cpu, instruction, address)


def op_INX(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.x += 1
    cpu._set_zero(cpu.x == 0)
    cpu._set_negative(_is_bit_n_set(cpu.x, 7))


def op_INY(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.y += 1
    cpu._set_zero(cpu.y == 0)
    cpu._set_negative(_is_bit_n_set(cpu.y, 7))


def op_ISB(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    # We're reading and writing to the address, we're not interesed
    # in the existing value there other than to increment it.
    _, address = _data_for_mode(cpu, instruction, instruction_bytes)
    return _ISB(cpu, instruction, address)


def op_JMP(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    # We either read the value directly from the instruction bytes.
    # Or, it was placed in an indirect spot and we had to dereference
    # to get it.
    _, address = _data_for_mode(cpu, instruction, instruction_bytes)
    # Jump the program counter to an absolute location given
    # by the operand.
    cpu.pc = address


def op_JSR(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    # TODO
    # Could add frames to this (for stack traces?)
    return_address = cpu.pc + instruction['bytes'] - 1
    cpu.sp = cpu._stack.push(cpu.memory, cpu.sp, return_address)
    low = instruction_bytes[1]
    high = instruction_bytes[2] << 0x8
    address = high + low
    cpu.pc = address


def op_LAX(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    # From https://wiki.nesdev.com/w/index.php/Programming_with_unofficial_opcodes
    # "Shortcut for LDA value then TAX. Saves a byte and two cycles
    # and allows use of the X register with the (d),Y addressing mode.
    # Notice that the immediate is missing; the opcode that would have
    # been LAX is affected by line noise on the data bus. MOS 6502:
    # even the bugs have bugs."
    # Undocumented instruction that combines two steps into 1.
    # We either read the value directly from the instruction bytes.
    # Or, it was placed in an indirect spot and we had to dereference
    # to get it.
    value, address = _data_for_mode(cpu, instruction, instruction_bytes)
    return _LAX(cpu, instruction, value)


def op_LDA(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    if cpu._bus.has_data:
        value = cpu._bus.data
    else:
        value, _ = _data_for_mode(cpu, instruction, instruction_bytes)
    return _LDA(cpu, instruction, value)


def op_LDX(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    if cpu._bus.has_data:
        value = cpu._bus.data
    else:
        value, _ = _data_for_mode(cpu, instruction, instruction_bytes)
    return _LDX(cpu, instruction, value)


def op_LDY(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    if cpu._bus.has_data:
        value = cpu._bus.data
    else:
        value, _ = _data_for_mode(cpu, instruction, instruction_bytes)
    return _LDY(cpu, instruction, value)


def op_LSR(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, address = _data_for_mode(cpu, instruction, instruction_bytes)
    next_value = _LSR(cpu, instruction, value)
    # If the addressing mode is ACCUMULATOR, then the target will
    # be cpu.a, otherwise it's performed on the value.
    _store_data_for_mode(cpu, instruction, next_value, address)


def op_NOP(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    # It may be weird that we're actually doing something in a NOP
    # but some NOPs have cycle penalties for page crossing (e.g.
    # 0x1c), so they have conditional impact on CPU cycles.
    _, _ = _data_for_mode(cpu, instruction, instruction_bytes)


def op_ORA(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, _ = _data_for_mode(cpu, instruction, instruction_bytes)
    return _ORA(cpu, instruction, value)


def op_PHA(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.sp = cpu._stack.push(cpu.memory, cpu.sp, cpu.a)


def op_PHP(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.sp = cpu._stack.push(cpu.memory, cpu.sp, cpu.p)


def op_PLA(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.sp, cpu.a = cpu._stack.pop(cpu.memory, cpu.sp, 1)
    cpu._set_zero(cpu.a == 0)
    cpu._set_negative(_is_bit_n_set(cpu.a, 0x7))


def op_PLP(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    # TODO:
    # Implement these learnings from http://nesdev.com/6502_cpu.txt
    #    1 unused flag
    #         To the current knowledge, this flag is always 1.
    #    B Break flag
    #         This flag is used to distinguish software (BRK)
    #         interrupts from hardware interrupts (IRQ or NMI). The B
    #         flag is always set except when the P register is being
    #         pushed on stack when jumping to an interrupt routine to
    #         process only a hardware interrupt.
    # https://wiki.nesdev.com/w/index.php/Status_flags#The_B_flag
    cpu.sp, cpu.p = cpu._stack.pop(cpu.memory, cpu.sp, 1)
    # Even if we're writing in 0xff it looks like we should still make
    # sure to unset the usused flag at bit 4 (from 0 to 7) because the
    # test relies on this behaviour.
    cpu._set_bit_4(False)
    # TODO
    # Also looks like we need to flip the bit_5 flag (the BRK flag?)
    # to on based on the tests.
    cpu._set_bit_5(True)


def op_RLA(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, address = _data_for_mode(cpu, instruction, instruction_bytes)
    next_value = _RLA(cpu, instruction, value)
    _store_data_for_mode(cpu, instruction, next_value, address)


def op_ROR(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, address = _data_for_mode(cpu, instruction, instruction_bytes)
    next_value = _ROR(cpu, instruction, value)
    # If the addressing mode is ACCUMULATOR, then the target will
    # be cpu.a, otherwise it's performed on the value.
    _store_data_for_mode(cpu, instruction, next_value, address)


def op_ROL(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, address = _data_for_mode(cpu, instruction, instruction_bytes)
    next_value = _ROL(cpu, instruction, value)
    # If the addressing mode is ACCUMULATOR, then the target will
    # be cpu.a, otherwise it's performed on the value.
    _store_data_for_mode(cpu, instruction, next_value, address)


def op_RRA(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, address = _data_for_mode(cpu, instruction, instruction_bytes)
    next_value = _RRA(cpu, instruction, value)
    _store_data_for_mode(cpu, instruction, next_value, address)


def op_RTI(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.sp, cpu.p = cpu._stack.pop(cpu.memory, cpu.sp, 1)
    cpu.sp, cpu.pc = cpu._stack.pop(cpu.memory, cpu.sp, 2)
    # Need to set the B flag which should always be True (i.e. set)
    # in all cases except for:
    # "When the P register [stack pointer] is being pushed onto the
    # stack when jumping to an interrupt routine to process only a
    # hardware interrupt."
    cpu._set_bit_5(True)


def op_RTS(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    # TODO
    # Could add frames to this (for stack traces?)
    cpu.sp, return_address = cpu._stack.pop(cpu.memory, cpu.sp, 2)
    # We subtracted one from the address that was pushed to the stack
    # so when we increment PC by the instruction size of 1 we'll get
    # to the right place.
    cpu.pc = return_address


def op_SAX(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    _, address = _data_for_mode(cpu, instruction, instruction_bytes)
    return _SAX(cpu, instruction, address)


def op_SBC(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, _ = _data_for_mode(cpu, instruction, instruction_bytes)
    return _SBC(cpu, instruction, value)


def op_SEC(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu._set_carry(True)


def op_SED(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu._set_decimal(True)


def op_SEI(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu._set_interrupt_disabled(True)


def op_SLO(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, address = _data_for_mode(cpu, instruction, instruction_bytes)
    next_value = _SLO(cpu, instruction, value)
    _store_data_for_mode(cpu, instruction, next_value, address)


def op_SRE(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    value, address = _data_for_mode(cpu, instruction, instruction_bytes)
    next_value = _SRE(cpu, instruction, value)
    _store_data_for_mode(cpu, instruction, next_value, address)


def op_STA(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    _, address = _data_for_mode(cpu, instruction, instruction_bytes)
    # We're reading and writing to the address, we're not interesed
    # in the existing value there other than to increment it.
    return _STA(cpu, instruction, address)


def op_STX(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    _, address = _data_for_mode(cpu, instruction, instruction_bytes)
    return _STX(cpu, instruction, address)


def op_STY(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    _, address = _data_for_mode(cpu, instruction, instruction_bytes)
    return _STY(cpu, instruction, address)


def op_TAX(cpu: Any, instruction: dict, _instruction_bytes: bytearray) -> None:
    return _TAX(cpu, instruction)


def op_TAY(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.y = cpu.a
    cpu._set_zero(cpu.y == 0)
    cpu._set_negative(_is_bit_n_set(cpu.y, 0x7))


def op_TSX(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.x = cpu.sp
    cpu._set_zero(cpu.x == 0)
    cpu._set_negative(_is_bit_n_set(cpu.x, 0x7))              


def op_TXA(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.a = cpu.x
    cpu._set_zero(cpu.a == 0)
    cpu._set_negative(_is_bit_n_set(cpu.a, 0x7))


def op_TYA(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.a = cpu.y
    cpu._set_zero(cpu.a == 0)
    cpu._set_negative(_is_bit_n_set(cpu.a, 0x7))


def op_TXS(cpu: Any, instruction: dict, instruction_bytes: bytearray) -> None:
    cpu.sp = cpu.x


def NMI(cpu: Any) -> None:
    """
    Not an actual operation but handles the NMI interrupt.
    """
    # TODO
    # Not sure if this is the right way to handle the interrupt.
    # It may need to push status flugs and the previous program
    # counter to the stack.
    nmi_low = cpu.memory.read_one(0xFFFA)
    nmi_high = cpu.memory.read_one(0xFFFB)
    nmi_address = (nmi_high << 8) + nmi_low

    # I believe the assumption is that whatever handles the NMI
    # ultimately ends with an RTI (return from interrupt) so that
    # it goes back to where it should've gone. At that point it
    # wants to recover the address and flag state. I wonder if
    # other registers should also be restored (a, x, y?)
    cpu.sp = cpu._stack.push(cpu.memory, cpu.sp, cpu.pc)
    cpu.sp = cpu._stack.push(cpu.memory, cpu.sp, cpu.p)
    cpu.pc = nmi_address


cpu_operations = {
    'ADC': op_ADC,
    'AND': op_AND,
    'ASL': op_ASL,
    'BCC': op_BCC,
    'BCS': op_BCS,
    'BEQ': op_BEQ,
    'BIT': op_BIT,
    'BMI': op_BMI,
    'BNE': op_BNE,
    'BPL': op_BPL,
    'BRK': op_BRK,
    'BVC': op_BVC,
    'BVS': op_BVS,
    'CLC': op_CLC,
    'CLD': op_CLD,
    'CLV': op_CLV,
    'CMP': op_CMP,
    'CPX': op_CPX,
    'CPY': op_CPY,
    'DCP': op_DCP,
    'DEC': op_DEC,
    'DEX': op_DEX,
    'DEY': op_DEY,
    'EOR': op_EOR,
    'INC': op_INC,
    'INX': op_INX,
    'INY': op_INY,
    'ISB': op_ISB,
    'JMP': op_JMP,
    'JSR': op_JSR,
    'LAX': op_LAX,
    'LDA': op_LDA,
    'LDX': op_LDX,
    'LDY': op_LDY,
    'LSR': op_LSR,
    'NOP': op_NOP,
    'ORA': op_ORA,
    'PHA': op_PHA,
    'PHP': op_PHP,
    'PLA': op_PLA,
    'PLP': op_PLP,
    'RLA': op_RLA,
    'ROL': op_ROL,
    'ROR': op_ROR,
    'RRA': op_RRA,
    'RTI': op_RTI,
    'RTS': op_RTS,
    'SAX': op_SAX,
    'SBC': op_SBC,
    'SEC': op_SEC,
    'SED': op_SED,
    'SEI': op_SEI,
    'SLO': op_SLO,
    'SRE': op_SRE,
    'STA': op_STA,
    'STX': op_STX,
    'STY': op_STY,
    'TAX': op_TAX,
    'TAY': op_TAY,
    'TSX': op_TSX,
    'TXA': op_TXA,
    'TXS': op_TXS,
    'TYA': op_TYA,
}
