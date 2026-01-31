#include "CPUOperations.h"
#include "CPU.h"
#include <exception>
#include <stdexcept>
#include <set>
#include <unistd.h>
#include "Constants.h"
#include "Opcodes.h"
#include "PPUUtils.h"

// Prototypes for some functions that aren't declared in order.
void _LDA(CPU&, Instruction, uint8_t);
void _SBC(CPU&, Instruction, uint8_t);
void _TAX(CPU&, Instruction);
bool is_joypad_address(uint16_t);

bool
_is_bit_n_set(uint16_t value, uint16_t bit) {
    /*
     * If a bit at a given offset is set, return True
     * otherwise False.
     * 
     * Example: value: 0x80:, bit: 7
     * // 1 0 0 0 0 0 0 0
     * // 0 0 0 0 0 0 0 1
     * 
     * Example: value: 0x02:, bit: 1
     * // 0 0 0 0 0 0 1 0
     * // 0 0 0 0 0 0 0 1
    */
    return value & (2 << (bit - 1));
}

bool
_crossed_page(uint16_t address, uint16_t next_address) {
    // Addresses all fit into some page. Pages are bins of 256
    // bytes. So address 0x0 will reference the first page (the first
    // bin). 0x100 is past the first 256 bytes so it'll be in the
    // next page, and so on.
    // If we divide by 0x100 without remainders, we can figure out
    // which page an address belongs to. If `address` and
    // `next_address` aren't in the same page then we've crossed
    // pages.
    // Dividing by 0x100 (256) is the same as shifting right by 8
    // (since 2^8 is 256)
    uint16_t page_index_a = address >> 8;
    uint16_t page_index_b = next_address >> 8;
    return page_index_a != page_index_b;
}

uint8_t
_get_zero_page_address(uint8_t* instruction_bytes) {
    // Assumes that we have enough data from the operand to
    // get uint8.
    uint8_t address = instruction_bytes[1];
    return address;
}

uint16_t
_get_absolute_address(uint8_t* instruction_bytes) {
    // Assumes that we have enough data from the operand to
    // get uint16.
    uint8_t low = instruction_bytes[1];
    uint16_t high = instruction_bytes[2] << 0x8;
    return high + low;
}

struct AddressValue {
    uint16_t address;
    uint8_t value;
};

AddressValue
_get_absolute_x(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    uint16_t address = _get_absolute_address(instruction_bytes);
    uint16_t next_address = address + cpu.x;
    // Not all page crossings involve a penalty.
    bool has_page_crossing_penalty = instruction.page_crossing_cycles != 0;
    if (_crossed_page(address, next_address) && has_page_crossing_penalty) {
        // Potential penalty for page crossing for all absolute_x
        // instructions. It may seem architecturally strange to do
        // this mutation of the cycles here, but this is exactly
        // where we can capture all this information (at address
        // resolution time).
        cpu.clock.cpu_cycle(instruction.page_crossing_cycles);
    }

    // TODO
    // Watch for overflow.
    // next_address &= 0xffff;
    return { next_address, cpu.memory.read_one(next_address) };
}

AddressValue 
_get_absolute_y(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    uint16_t address = _get_absolute_address(instruction_bytes);
    uint16_t next_address = address + cpu.y;
    // Not all page crossings involve a penalty.
    bool has_page_crossing_penalty = instruction.page_crossing_cycles != 0;
    if (_crossed_page(address, next_address) && has_page_crossing_penalty) {
        // Potential penalty for page crossing for all absolute_y
        // instructions. It may seem architecturally strange to do
        // this mutation of the cycles here, but this is exactly
        // where we can capture all this information (at address
        // resolution time).
        cpu.clock.cpu_cycle(instruction.page_crossing_cycles);
    }
    // TODO
    // Watch for overflow.
    // next_address &= 0xffff;
    return { next_address, cpu.memory.read_one(next_address) };
}

uint16_t
_get_indirect_x(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // We need to compute the where the pointer is stored,
    // grab the pointer, then use it to look up the actual
    // value.
    uint16_t base = _get_zero_page_address(instruction_bytes);
    uint16_t pointer_address = base + cpu.x;
    return pointer_address;
}

uint16_t
_get_indirect_y(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // Example functionality:
    // At d922 we need to read
    // * instruction includes: 0x89
    // * read address at 0x89: 0x00 0x03 (0x0300 for endianness)
    // * read one byte from 0x300 + y (where y is 0)
    // * byte should be 0x89

    // At D940 we need to read
    // * instruction includes: 0x97
    // * read address at 0x97: 0xff 0xff (0xffff for endianness)
    // * read one byte from 0xffff + y (where y is 34)
    // * byte should be 0xa3 after we end up wrapping around
    // to read from 0x33

    uint16_t pointer_address = _get_zero_page_address(instruction_bytes);
    // Should be uint16.
    uint16_t address = cpu.memory.read_from_zero_page_uint16(pointer_address);
    uint16_t next_address = address + cpu.y;
    bool has_page_crossing_penalty = instruction.page_crossing_cycles != 0;
    if (_crossed_page(address, next_address) && has_page_crossing_penalty) {
        // Potential penalty for page crossing for all indirect_y
        // instructions. It may seem architecturally strange to do
        // this mutation of the cycles here, but this is exactly
        // where we can capture all this information (at address
        // resolution time).
        cpu.clock.cpu_cycle(instruction.page_crossing_cycles);
    }
    // Handle wrap around.
    next_address &= 0xffff;
    return next_address;
}

AddressValue
_data_for_mode(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // FIXME
    // we're calling this to get data but it's also being used to get an
    // address. Those two responsibilities should be split up.
    // This should also be inlined because it's so frequently called.
    // That way, we won't read data for cases like STA/STX/STY which
    // are storing things, not reading data back from somewhere.

    /* 
     * Given an addressing_mode and the data that came with the opcode
     * (its operand[s]), figure out what data is being operated on by
     * the instruction and where. I.e. do we need to look in memory for
     * the data? Is it provided inline with the opcode?
     */

    // FIXME
    // Maybe pick different default values?
    uint16_t address = 0;
    uint8_t value = 0;
    AddressingMode addressing_mode = instruction.addressing_mode;

    if (addressing_mode == AddressingMode::ABSOLUTE) {
        address = _get_absolute_address(instruction_bytes);
        value = cpu.memory.read_one(address);
    } else if (addressing_mode == AddressingMode::ABSOLUTE_X) {
        auto av = _get_absolute_x(cpu, instruction, instruction_bytes);
        address = av.address;
        value = av.value;
    } else if (addressing_mode == AddressingMode::ABSOLUTE_Y) {
        auto av = _get_absolute_y(cpu, instruction, instruction_bytes);
        address = av.address;
        value = av.value;
    } else if (addressing_mode == AddressingMode::ACCUMULATOR) {
        value = cpu.a;
    } else if (addressing_mode == AddressingMode::INDIRECT) {
        address = _get_absolute_address(instruction_bytes);
        // Overwrite the address of where we actually want to jump to.
        address = cpu.memory.read_two(address);
    } else if (addressing_mode == AddressingMode::INDIRECT_X) {
        // It's indexed by the x register.
        uint16_t pointer_address = _get_indirect_x(cpu, instruction, instruction_bytes);
        address = cpu.memory.read_from_zero_page_uint16(pointer_address);
        value = cpu.memory.read_one(address);
    } else if (addressing_mode == AddressingMode::INDIRECT_Y) {
        // // It's indexed by the y register.
        address = _get_indirect_y(cpu, instruction, instruction_bytes);
        value = cpu.memory.read_one(address);
    } else if (addressing_mode == AddressingMode::IMMEDIATE) {
        // It's inline.
        value = instruction_bytes[1];
    } else if (addressing_mode == AddressingMode::ZEROPAGE) {
        address = _get_zero_page_address(instruction_bytes);
        value = cpu.memory.read_one(address);
    } else if (addressing_mode == AddressingMode::ZEROPAGE_X) {
        address = _get_zero_page_address(instruction_bytes);
        address += cpu.x;
        // TODO
        // Watch for overflow. This would be better replaced with integers
        // that handle the overflow themselves...
        address &= 0xff;
        value = cpu.memory.read_from_zero_page_uint8(address);
    } else if (addressing_mode == AddressingMode::ZEROPAGE_Y) {
        address = _get_zero_page_address(instruction_bytes);
        address += cpu.y;
        // TODO
        // Watch for overflow. This would be better replaced with integers
        // that handle the overflow themselves...
        address &= 0xff;
        value = cpu.memory.read_from_zero_page_uint8(address);
    }

    return { address, value };
}

bool
is_joypad_address(uint16_t address) {
    switch (address) {
        case (uint16_t)JoypadAddress::JOYPAD1:
        case (uint16_t)JoypadAddress::JOYPAD2:
            return true;
        default:
            return false;
    }
}

void
_store_data_for_mode(
    CPU& cpu,
    Instruction instruction,
    uint8_t value,
    uint16_t address
) {
    /*
     * Similar to _data_for_mode, if we need to do something with the
     * result of an instruction, this handles it. Some operations and
     * addressing modes don't make any sense for this, so we should error
     * if it's ever called with those.
     */
    // TODO
    // There is a fair amount of time spent here.

    AddressingMode addressing_mode = instruction.addressing_mode;

    if (IsUnsupportedStorageAddressModes(addressing_mode)) {
        // It means this function was called with a mode that shouldn't
        // be trying to store this data.
        printf("%x %d\n", cpu.pc, addressing_mode);
        std::throw_with_nested(
            std::runtime_error("Invalid addressing mode for storage.\n")
        );
    }

    if (addressing_mode == AddressingMode::ACCUMULATOR) {
        cpu.a = value;
        return;
    }

    cpu.memory.write(value, address);
}

// Anything that reads or writes from the _bus object on the CPU is
// doing it for the following reason:
// https://wiki.nesdev.com/w/index.php/PPU_programmer_reference#Ports
// "The PPU has an internal data bus that it uses for communication
// with the CPU. This bus, called _io_db in Visual 2C02 and PPUGenLatch
// in FCEUX,[1] behaves as an 8-bit dynamic latch due to capacitance
// of very long traces that run to various parts of the PPU. Writing
// any value to any PPU port, even to the nominally read-only PPUSTATUS,
// will fill this latch. Reading any readable port (PPUSTATUS, OAMDATA,
// or PPUDATA) also fills the latch with the bits read. Reading a
// nominally "write-only" register returns the latch's current value,
// as do the unused bits of PPUSTATUS. This value begins to decay after
// a frame or so, faster once the PPU has warmed up, and it is likely
// that values with alternating bit patterns (such as $55 or $AA) will
// decay faster.[2]


int16_t
_resolve_displacement(uint8_t* instruction_bytes) {
    // TODO
    // Figure out the signed vs. unsigned int stuff
    int8_t displacement = instruction_bytes[1];
    // Displacement can be forwards and backwards. For this reason we need
    // to treat this as a signed value.
    if (displacement > 0x7f) {
        return ((0x100 - displacement) * -1);
    }
    return displacement;
}

void
_ADC(CPU& cpu, Instruction instruction, uint8_t value) {
    // TODO
    // Find a better way to implement add-with-carry that lets us do it
    // the proper way with 2's complements and saner overflow/negatives
    // handling and all that.

    // If we have a carry bit we want to account for it in the next
    // addition. This is because the carry bit may have been set
    // by previous ADCs and we need to keep 'carry'ing that bit forward.
    uint8_t carry = cpu.carry();

    // Is cpu.a negative?
    // Is the value we're adding negative?
    // If both are positive, neither will have the negative
    // bit set.
    bool positive_operands = !_is_bit_n_set(value, 0x7) && !_is_bit_n_set(cpu.a, 0x7);
    // Need more storage to determine if we overflowed
    // or whether there was a carry operation.
    uint16_t temp = cpu.a + value + carry;

    // We overflowed into the negative bit if we tried to add
    // two positive numbers and ended up with the highest bit
    // (bit 7) set to 1.
    bool overflowed = positive_operands && _is_bit_n_set(temp, 0x7);
    cpu.set_overflow(overflowed);

    // The 9th bit of the result is stored in the carry flag.
    // (If we're starting at 0 it's the 8th bit)
    cpu.set_carry(_is_bit_n_set(temp, 0x8));
    cpu.set_negative(_is_bit_n_set(temp, 0x7));

    // Clear any bits that would result in a being greater
    // than 1 byte, which ensures that we clear out any
    // overflowed value.
    cpu.a = (uint8_t)(temp & 0xff);

    // Now that we've fixed any overflowed value putting a back
    // in the range of 0->255, we can see if it's zero. This makes
    // sense when we overflowed into the 8th bit (i.e. a byte isn't
    // enough to hold the result).
    // that a is within the [0, 255]
    cpu.set_zero(cpu.a == 0);
}

void
_AND(CPU& cpu, Instruction instruction, uint8_t value) {
    cpu.a &= value;
    cpu.set_zero(cpu.a == 0);
    cpu.set_negative(_is_bit_n_set(cpu.a, 0x7));
}

uint8_t
_ASL(CPU& cpu, Instruction instruction, uint8_t value) {
    cpu.set_carry(_is_bit_n_set(value, 0x7));
    value <<= 1;
    // In case we multiplied over the storage of 1 byte.
    // TODO shouldn't be needed.
    value &= 0xff;
    cpu.set_zero(value == 0);
    cpu.set_negative(_is_bit_n_set(value, 0x7));
    return value;
}

void
_CMP(CPU& cpu, Instruction instruction, uint8_t value) {
    uint8_t temp = cpu.a - value;
    cpu.set_carry(cpu.a >= value);
    cpu.set_zero(cpu.a == value);
    cpu.set_negative(_is_bit_n_set(temp, 7));
}

void
_CPX(CPU& cpu, Instruction instruction, uint8_t value) {
    uint8_t temp = cpu.x - value;
    cpu.set_carry(cpu.x >= value);
    cpu.set_zero(cpu.x == value);
    cpu.set_negative(_is_bit_n_set(temp, 7));
}

void
_CPY(CPU& cpu, Instruction instruction, uint8_t value) {
    uint8_t temp = cpu.y - value;
    cpu.set_carry(cpu.y >= value);
    cpu.set_zero(cpu.y == value);
    cpu.set_negative(_is_bit_n_set(temp, 7));
}

void
_DEC(CPU& cpu, Instruction instruction, uint16_t address) {
    // TODO
    // This may have to support uint16s.
    uint8_t value = cpu.memory.read_one(address);
    value--;

    // I believe this supports underflows (e.g. 0 - 1 = 0xff) in
    // the 1-byte case. If we need support for 2 bytes it'll
    // have to change.
    value &= 0xff;
    cpu.set_zero(value == 0);
    cpu.set_negative(_is_bit_n_set(value, 0x7));
    cpu.memory.write(value, address);
}

void
_DCP(CPU& cpu, Instruction instruction, uint16_t address) {
    // Undocumented instruction:
    // "Equivalent to DEC value then CMP value, except supporting
    // more addressing modes. LDA #$FF followed by DCP can be used
    // to check if the decrement underflows, which is useful for
    // multi-byte decrements."

    // Grab the decremented value from where we wrote it after _DEC.
    _DEC(cpu, instruction, address);
    uint8_t value = cpu.memory.read_one(address);

    // Let CMP do its job and also increment the pc register.
    return _CMP(cpu, instruction, value);
}

void
_EOR(CPU& cpu, Instruction instruction, uint8_t value) {
    cpu.a ^= value;
    cpu.set_zero(cpu.a == 0);
    cpu.set_negative(_is_bit_n_set(cpu.a, 7));
}

void
_INC(CPU& cpu, Instruction instruction, uint16_t address) {
    // TODO
    // This may have to support uint16s.
    uint8_t value = cpu.memory.read_one(address);
    value++;
    value &= 0xff;
    cpu.set_zero(value == 0);
    cpu.set_negative(_is_bit_n_set(value, 0x7));
    cpu.memory.write(value, address);
}

uint8_t
_ISB(CPU& cpu, Instruction instruction, uint16_t address) {
    // Undocumented instruction:
    // "Equivalent to INC value then SBC value, except supporting
    // more addressing modes."
    _INC(cpu, instruction, address);

    // Need to read back the value that was stored during _INC
    uint8_t value = cpu.memory.read_one(address);

    // Let SBC do its job and also increment the pc register.
    _SBC(cpu, instruction, value);

    // Check the status again of the value and set flags
    // accordingly. This part is repeated from SBC.
    cpu.set_zero(cpu.a == 0);
    cpu.set_negative(_is_bit_n_set(cpu.a, 0x7));
    return value;
}

void
_LAX(CPU& cpu, Instruction instruction, uint8_t value) {
    _LDA(cpu, instruction, value);
    _TAX(cpu, instruction);
}

void
_LDA(CPU& cpu, Instruction instruction, uint8_t value) {
    cpu.a = value;
    cpu.set_zero(cpu.a == 0);
    cpu.set_negative(_is_bit_n_set(cpu.a, 0x7));
}

void
_LDX(CPU& cpu, Instruction instruction, uint8_t value) {
    cpu.x = value;
    cpu.set_zero(cpu.x == 0);
    cpu.set_negative(_is_bit_n_set(cpu.x, 0x7));
}

void
_LDY(CPU& cpu, Instruction instruction, uint8_t value) {
    cpu.y = value;
    cpu.set_zero(cpu.y == 0);
    cpu.set_negative(_is_bit_n_set(cpu.y, 0x7));
}

uint8_t
_LSR(CPU& cpu, Instruction instruction, uint8_t value) {
    cpu.set_carry(bool(value & 0x1));
    value >>= 1;
    cpu.set_zero(value == 0);
    cpu.set_negative(_is_bit_n_set(value, 0x7));
    return value;
}

void
_ORA(CPU& cpu, Instruction instruction, uint8_t value) {
    cpu.a |= value;
    cpu.set_zero(cpu.a == 0);
    cpu.set_negative(_is_bit_n_set(cpu.a, 7));
}

uint8_t
_ROL(CPU& cpu, Instruction instruction, uint8_t value) {
    uint8_t carry = cpu.carry();
    uint8_t next_carry = _is_bit_n_set(value, 0x7);
    value <<= 1;
    value = carry ? value | 0x01 : value & 0xfe;
    cpu.set_carry(next_carry);
    // In case we multiplied over the storage of 1 byte.
    value &= 0xff;
    cpu.set_zero(value == 0);
    cpu.set_negative(_is_bit_n_set(value, 0x7));
    return value;
}

uint8_t
_RLA(CPU& cpu, Instruction instruction, uint8_t value) {
    // Undocumented instruction:
    // "Equivalent to ROL value then AND value, except supporting
    // more addressing modes. LDA #$FF followed by RLA is an efficient
    // way to rotate a variable while also loading it in A."
    value = _ROL(cpu, instruction, value);
    _AND(cpu, instruction, value);
    return value;
}

uint8_t
_ROR(CPU& cpu, Instruction instruction, uint8_t value) {
    uint8_t carry = cpu.carry();
    uint8_t next_carry = value & 0x1;
    value >>= 1;
    // Set or unset the seventh bit if the carry was set.
    value = carry ? value | 0x80 : value & 0x7f;
    cpu.set_carry(next_carry);
    cpu.set_zero(value == 0);
    cpu.set_negative(_is_bit_n_set(value, 0x7));
    return value;
}

uint8_t
_RRA(CPU& cpu, Instruction instruction, uint8_t value) {
    // Undocumented instruction:
    // "Equivalent to ROR value then ADC value, except supporting
    // more addressing modes. Essentially this computes A + value / 2,
    // where value is 9-bit and the division is rounded up."
    value = _ROR(cpu, instruction, value);
    _ADC(cpu, instruction, value);
    return value;
}

void
_SAX(CPU& cpu, Instruction instruction, uint16_t address) {
    // Undocumented instruction:
    // "Stores the bitwise AND of A and X. As with STA and STX, no
    // flags are affected."
    cpu.memory.write(cpu.x & cpu.a, address);
}

void
_SBC(CPU& cpu, Instruction instruction, uint8_t value) {
    // TODO
    // Find a better way to implement subtract-with-carry that lets us do it
    // the proper way with 2's complements and saner overflow/negatives
    // handling and all that.
    
    // maybe_set_overflow
    {
        // Signed subtraction, these are overflow cases becuse
        // with 0x0 -> 0xFF we get -128 -> 127, any value
        // that doesn't fall in that range is overflowed. Of course,
        // to see this, we now need to treat our values as though
        // they were signed to begin with. This let's us treat
        // both values as signed 8-bit integers so we can then
        // properly subtract them.
        // TODO
        // This should be replaced with a class as described in the
        // TODO.md document so that we can just subtract the values
        // as signed 8-bit integers without needing this conversion.
        int8_t s_a = (int8_t)cpu.a;
        int8_t s_b = (int8_t)value;
        int8_t cpu_carry = (int8_t)(!cpu.carry());
        int16_t outcome = s_a - s_b - cpu_carry;
        cpu.set_overflow(outcome < -128 || outcome > 127);
    }

    // Wraps around possibly.
    uint8_t start_a = cpu.a;
    cpu.a -= value;
    cpu.a -= cpu.carry() ? 0 : 1;

    // "The carry flag is set if the result is greater than or
    // equal to 0. The carry flag is reset when the result is
    // less than 0, indicating a borrow."
    // In other words, this can only be set if we know
    // cpu.a - value will be >= 0, which will only happen if
    // cpu.a >= value.
    cpu.set_carry(start_a >= value);

    // "The negative flag is set if the result in the accumulator
    // has bit 7 on, otherwise it is reset."
    cpu.set_negative(_is_bit_n_set(cpu.a, 0x7));
    cpu.set_zero(cpu.a == 0);
}

uint8_t
_SLO(CPU& cpu, Instruction instruction, uint8_t value) {
    // Undocumented instruction:
    // "Equivalent to ASL value then ORA value, except supporting
    // more addressing modes. LDA #0 followed by SLO is an efficient
    // way to shift a variable while also loading it in A."
    value = _ASL(cpu, instruction, value);
    _ORA(cpu, instruction, value);
    return value;
}

uint8_t
_SRE(CPU& cpu, Instruction instruction, uint8_t value) {
    // Undocumented instruction:
    // "Equivalent to LSR value then EOR value, except supporting
    // more addressing modes. LDA #0 followed by SRE is an efficient
    // way to shift a variable while also loading it in A."
    value = _LSR(cpu, instruction, value);
    _EOR(cpu, instruction, value);
    return value;
}

void
_STA(CPU& cpu, Instruction instruction, uint16_t address) {
    PPURegister ppu_register = resolve_register(address);
    if (ppu_register != PPURegister::NONE) {
        // PPU is handling this one, so we need to put it in the bus
        // instead of in memory
        if (ppu_register == PPURegister::OAMDMA) {
            // OAMDMA is handled differently from other data sharing
            // with the PPU.
            cpu.upload_oamdma_data(cpu.a);
        } else {
            cpu.bus.set_data(cpu.a, ppu_register);
        }
    } else {
        if (is_joypad_address(address)) {
            cpu.nes_controller.handle_signal(cpu.a);
        } else {
            cpu.memory.write(cpu.a, address);
        }
    }
}

void
_STX(CPU& cpu, Instruction instruction, uint16_t address) {
    PPURegister ppu_register = resolve_register(address);
    if (ppu_register != PPURegister::NONE) {
        // PPU is handling this one, so we need to put it in the bus
        // instead of in memory
        if (ppu_register == PPURegister::OAMDMA) {
            // OAMDMA is handled differently from other data sharing
            // with the PPU.
            cpu.upload_oamdma_data(cpu.x);
        } else {
            cpu.bus.set_data(cpu.x, ppu_register);
        }
    } else {
        if (is_joypad_address(address)) {
            cpu.nes_controller.handle_signal(cpu.x);
        } else {
            cpu.memory.write(cpu.x, address);
        }
    }
}

void
_STY(CPU& cpu, Instruction instruction, uint16_t address) {
    PPURegister ppu_register = resolve_register(address);
    if (ppu_register != PPURegister::NONE) {
        // PPU is handling this one, so we need to put it in the bus
        // instead of in memory
        if (ppu_register == PPURegister::OAMDMA) {
            // OAMDMA is handled differently from other data sharing
            // with the PPU.
            cpu.upload_oamdma_data(cpu.y);
        } else {
            cpu.bus.set_data(cpu.y, ppu_register);
        }
    } else {
        if (is_joypad_address(address)) {
            cpu.nes_controller.handle_signal(cpu.y);
        } else {
            cpu.memory.write(cpu.y, address);
        }
    }
}

void
_TAX(
    CPU& cpu,
    Instruction instruction
) {
    cpu.x = cpu.a;
    cpu.set_zero(cpu.x == 0);
    cpu.set_negative(_is_bit_n_set(cpu.x, 0x7));
}

void
op_ADC(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _ADC(cpu, instruction, av.value);
}

void
op_AND(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _AND(cpu, instruction, av.value);
}

void
op_ASL(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    uint8_t next_value = _ASL(cpu, instruction, av.value);
    // If the addressing mode is ACCUMULATOR, then the target will
    // be cpu.a, otherwise it's performed on the value.
    _store_data_for_mode(cpu, instruction, next_value, av.address);
}

void
op_BCC(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    if (!cpu.carry()) {
        int16_t displacement = _resolve_displacement(instruction_bytes);
        cpu.pc += displacement;
        // An additional cycle if the branch succeeds.
        cpu.clock.cpu_cycle(instruction.branch_cycles);
    }
}

void
op_BCS(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    if (cpu.carry()) {
        int16_t displacement = _resolve_displacement(instruction_bytes);
        cpu.pc += displacement;
        // An additional cycle if the branch succeeds.
        cpu.clock.cpu_cycle(instruction.branch_cycles);
    }
}

void
op_BEQ(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // WARNING:
    // This is super finicky. We need to test for page crossing
    // after already moving the PC forward. If we don't, we may
    // get a false positive for page crossing when the PC wasn't
    // moved forward already. This happens at cycle 2605 on nestest
    // because there is a crossing as the PC is incremented but
    // not as a result of just the displacement alone which is what
    // we're really interested in.
    // TODO
    // I imagine it's possible for other branching instructions
    // to have tehse page crossing issues, so watch out for this
    // in other roms.
    cpu.pc += instruction.bytes;
    uint16_t previous_pc = cpu.pc;
    if (cpu.zero()) {
        int16_t displacement = _resolve_displacement(instruction_bytes);
        cpu.pc += displacement;
        if (_crossed_page(previous_pc, cpu.pc)) {
            // The program counter is also looking at locations in memory
            // and displacing it could cause it to point to a new page.
            // As a result, even these branching instructions can have
            // page penalties.
            cpu.clock.cpu_cycle(instruction.page_crossing_cycles);
        } else {
            // An additional cycle if the branch succeeds. It seems like
            // the page crossing penalty cycle and the branching cycle
            // are mutualyl exclusive because in either case it's a
            // branch.
            cpu.clock.cpu_cycle(instruction.branch_cycles);
        }
    }
}

void
op_BIT(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    uint8_t value = 0;
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    PPURegister ppu_register = resolve_register(av.address);
    if (ppu_register != PPURegister::NONE) {
        value = cpu.bus.data(ppu_register);
    } else {
        value = cpu.memory.read_one(av.address);
    }
    uint8_t temp = cpu.a & value;
    cpu.set_zero(temp == 0);
    cpu.set_overflow(_is_bit_n_set(value, 0x6));
    cpu.set_negative(_is_bit_n_set(value, 0x7));
}

void
op_BNE(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    if (!cpu.zero()) {
        int16_t displacement = _resolve_displacement(instruction_bytes);
        cpu.pc += displacement;
        // An additional cycle if the branch succeeds.
        cpu.clock.cpu_cycle(instruction.branch_cycles);
    }
}

void
op_BMI(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    if (cpu.negative()) {
        int16_t displacement = _resolve_displacement(instruction_bytes);
        cpu.pc += displacement;
        // An additional cycle if the branch succeeds.
        cpu.clock.cpu_cycle(instruction.branch_cycles);
    }
}

void
op_BPL(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    if (!cpu.negative()) {
        int16_t displacement = _resolve_displacement(instruction_bytes);
        cpu.pc += displacement;
        // An additional cycle if the branch succeeds.
        cpu.clock.cpu_cycle(instruction.branch_cycles);
    }
}

void
op_BRK(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // "The BRK instruction forces the generation of an interrupt request.
    // The program counter and processor status are pushed on the stack then
    // the IRQ interrupt vector at $FFFE/F is loaded into the PC and the break
    // flag in the status set to one."
    // From: http://users.telenet.be/kim1-6502/6502/proman.html#90
    //       The break command causes the microprocessor to go through an inter-
    //  rupt sequence under program control.  This means that the program counter
    //  of the second byte after the BRK is automatically stored on the stack
    //  along with the processor status at the beginning of the break instruction.
    //  The microprocessor then transfers control to the interrupt vector.

    // As the description above says: push the PC that's two bytes after
    // the call to break. This is despite break only being 1 byte as far
    // as instructions go.
    cpu.pc += 2;
    cpu.stack.push_16(cpu.memory, cpu.sp, cpu.pc);
    cpu.stack.push_8(cpu.memory, cpu.sp, cpu.p);
    uint8_t low = cpu.memory.read_one(0xfffe);
    uint16_t high = cpu.memory.read_one(0xffff);
    high <<= 8;
    cpu.pc = low + high;
    cpu.set_bit_5(true);
}

void
op_BVC(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    if (!cpu.overflow()) {
        uint16_t displacement = _resolve_displacement(instruction_bytes);
        cpu.pc += displacement;
        // An additional cycle if the branch succeeds.
        cpu.clock.cpu_cycle(instruction.branch_cycles);
    }
}

void
op_BVS(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    if (cpu.overflow()) {
        uint16_t displacement = _resolve_displacement(instruction_bytes);
        cpu.pc += displacement;
        // An additional cycle if the branch succeeds.
        cpu.clock.cpu_cycle(instruction.branch_cycles);
    }
}

inline void
op_CLC(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.set_carry(false);
}

inline void
op_CLD(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.set_decimal(false);
}

inline void
op_CLV(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.set_overflow(false);
}

void
op_CMP(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _CMP(cpu, instruction, av.value);
}

void
op_CPX(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _CPX(cpu, instruction, av.value);
}

void
op_CPY(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _CPY(cpu, instruction, av.value);
}

void
op_DEC(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // We're reading and writing to the address, we're not interesed
    // in the existing value there other than to increment it.
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _DEC(cpu, instruction, av.address);
}

void
op_DEX(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.x = cpu.x - 1;
    cpu.set_zero(cpu.x == 0);
    cpu.set_negative(_is_bit_n_set(cpu.x, 7));
}

void
op_DEY(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.y = cpu.y - 1;
    cpu.set_zero(cpu.y == 0);
    cpu.set_negative(_is_bit_n_set(cpu.y, 7));
}

void
op_DCP(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // We're reading and writing to the address, we're not interesed
    // in the existing value there other than to increment it.
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _DCP(cpu, instruction, av.address);
}

void
op_EOR(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _EOR(cpu, instruction, av.value);
}

void
op_INC(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // We're reading and writing to the address, we're not interesed
    // in the existing value there other than to increment it.
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _INC(cpu, instruction, av.address);
}

void
op_INX(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.x = cpu.x + 1;
    cpu.set_zero(cpu.x == 0);
    cpu.set_negative(_is_bit_n_set(cpu.x, 7));
}

void
op_INY(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.y = cpu.y + 1;
    cpu.set_zero(cpu.y == 0);
    cpu.set_negative(_is_bit_n_set(cpu.y, 7));
}

void
op_ISB(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // We're reading and writing to the address, we're not interesed
    // in the existing value there other than to increment it.
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    _ISB(cpu, instruction, av.address);
}

void
op_JMP(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // We either read the value directly from the instruction bytes.
    // Or, it was placed in an indirect spot and we had to dereference
    // to get it.
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    // Jump the program counter to an absolute location given
    // by the operand.
    cpu.pc = av.address;
}

void
op_JSR(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // TODO
    // Could add frames to this (for stack traces?)
    uint16_t return_address = cpu.pc + instruction.bytes - 1;
    cpu.stack.push_16(cpu.memory, cpu.sp, return_address);
    uint8_t low = instruction_bytes[1];
    uint16_t high = instruction_bytes[2] << 0x8;
    uint16_t address = high + low;
    cpu.pc = address;
}

void
op_LAX(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // From https://wiki.nesdev.com/w/index.php/Programming_with_unofficial_opcodes
    // "Shortcut for LDA value then TAX. Saves a byte and two cycles
    // and allows use of the X register with the (d),Y addressing mode.
    // Notice that the immediate is missing; the opcode that would have
    // been LAX is affected by line noise on the data bus. MOS 6502:
    // even the bugs have bugs."
    // Undocumented instruction that combines two steps into 1.
    // We either read the value directly from the instruction bytes.
    // Or, it was placed in an indirect spot and we had to dereference
    // to get it.
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _LAX(cpu, instruction, av.value);
}

void
op_LDA(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    uint8_t value = 0;
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    PPURegister ppu_register = resolve_register(av.address);
    if (ppu_register != PPURegister::NONE) {
        value = cpu.bus.data(ppu_register);
    } else {
        value = av.value;
    }
    if (is_joypad_address(av.address)) {
        value = cpu.nes_controller.read_next();
    }
    return _LDA(cpu, instruction, value);
}

void
op_LDX(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    uint8_t value = 0;
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    PPURegister ppu_register = resolve_register(av.address);
    if (ppu_register != PPURegister::NONE) {
        value = cpu.bus.data(ppu_register);
    } else {
        value = av.value;
    }
    if (is_joypad_address(av.address)) {
        value = cpu.nes_controller.read_next();
    }
    return _LDX(cpu, instruction, value);
}

void
op_LDY(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    uint8_t value = 0;
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    PPURegister ppu_register = resolve_register(av.address);
    if (ppu_register != PPURegister::NONE) {
        value = cpu.bus.data(ppu_register);
    } else {
        value = av.value;
    }
    if (is_joypad_address(av.address)) {
        value = cpu.nes_controller.read_next();
    }
    return _LDY(cpu, instruction, value);
}

void
op_LSR(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    uint8_t next_value = _LSR(cpu, instruction, av.value);
    // If the addressing mode is ACCUMULATOR, then the target will
    // be cpu.a, otherwise it's performed on the value.
    _store_data_for_mode(cpu, instruction, next_value, av.address);
}

void
op_NOP(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // It may be weird that we're actually doing something in a NOP
    // but some NOPs have cycle penalties for page crossing (e.g.
    // 0x1c), so they have conditional impact on CPU cycles.
    _data_for_mode(cpu, instruction, instruction_bytes);
}

void
op_ORA(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _ORA(cpu, instruction, av.value);
}

inline void
op_PHA(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.stack.push_8(cpu.memory, cpu.sp, cpu.a);
}

inline void
op_PHP(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.stack.push_8(cpu.memory, cpu.sp, cpu.p);
}

void
op_PLA(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.a = cpu.stack.pop_8(cpu.memory, cpu.sp);
    cpu.set_zero(cpu.a == 0);
    cpu.set_negative(_is_bit_n_set(cpu.a, 0x7));
}

void
op_PLP(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // TODO:
    // Implement these learnings from http://nesdev.com/6502_cpu.txt
    //    1 unused flag
    //         To the current knowledge, this flag is always 1.
    //    B Break flag
    //         This flag is used to distinguish software (BRK)
    //         interrupts from hardware interrupts (IRQ or NMI). The B
    //         flag is always set except when the P register is being
    //         pushed on stack when jumping to an interrupt routine to
    //         process only a hardware interrupt.
    // https://wiki.nesdev.com/w/index.php/Status_flags#The_B_flag
    cpu.p = cpu.stack.pop_8(cpu.memory, cpu.sp);
    // Even if we're writing in 0xff it looks like we should still make
    // sure to unset the usused flag at bit 4 (from 0 to 7) because the
    // test relies on this behaviour.
    cpu.set_bit_4(false);
    // TODO
    // Also looks like we need to flip the bit_5 flag (the BRK flag?)
    // to on based on the tests.
    cpu.set_bit_5(true);
}

void
op_RLA(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    uint16_t address = av.address;
    uint8_t value = av.value;
    uint8_t next_value = _RLA(cpu, instruction, value);
    _store_data_for_mode(cpu, instruction, next_value, address);
}

void
op_ROR(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    uint16_t address = av.address;
    uint8_t value = av.value;
    uint8_t next_value = _ROR(cpu, instruction, value);
    // If the addressing mode is ACCUMULATOR, then the target will
    // be cpu.a, otherwise it's performed on the value.
    _store_data_for_mode(cpu, instruction, next_value, address);
}

void
op_ROL(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    uint16_t address = av.address;
    uint8_t value = av.value;
    uint8_t next_value = _ROL(cpu, instruction, value);
    // If the addressing mode is ACCUMULATOR, then the target will
    // be cpu.a, otherwise it's performed on the value.
    _store_data_for_mode(cpu, instruction, next_value, address);
}

void
op_RRA(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    uint16_t address = av.address;
    uint8_t value = av.value;
    uint8_t next_value = _RRA(cpu, instruction, value);
    _store_data_for_mode(cpu, instruction, next_value, address);
}

void
op_RTI(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.p = cpu.stack.pop_8(cpu.memory, cpu.sp);
    cpu.pc = cpu.stack.pop_16(cpu.memory, cpu.sp);
    // Need to set the B flag which should always be True (i.e. set)
    // in all cases except for:
    // "When the P register [stack pointer] is being pushed onto the
    // stack when jumping to an interrupt routine to process only a
    // hardware interrupt."
    cpu.set_bit_5(true);
}

void
op_RTS(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // TODO
    // Could add frames to this (for stack traces?)
    uint16_t return_address = cpu.stack.pop_16(cpu.memory, cpu.sp);
    // We subtracted one from the address that was pushed to the stack
    // so when we increment PC by the instruction size of 1 we'll get
    // to the right place.
    cpu.pc = return_address;
}

void
op_SAX(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _SAX(cpu, instruction, av.address);
}

void
op_SBC(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _SBC(cpu, instruction, av.value);
}

inline void
op_SEC(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.set_carry(true);
}

inline void
op_SED(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.set_decimal(true);
}

inline void
op_SEI(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.set_interrupt_disabled(true);
}

void
op_SLO(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    uint16_t address = av.address;
    uint8_t value = av.value;
    uint8_t next_value = _SLO(cpu, instruction, value);
    _store_data_for_mode(cpu, instruction, next_value, address);
}

void
op_SRE(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    uint16_t address = av.address;
    uint8_t value = av.value;
    uint8_t next_value = _SRE(cpu, instruction, value);
    _store_data_for_mode(cpu, instruction, next_value, address);
}

void
op_STA(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    // We're reading and writing to the address, we're not interesed
    // in the existing value there other than to increment it.
    return _STA(cpu, instruction, av.address);
}

void
op_STX(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _STX(cpu, instruction, av.address);
}

void
op_STY(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    AddressValue av = _data_for_mode(cpu, instruction, instruction_bytes);
    return _STY(cpu, instruction, av.address);
}

void
op_TAX(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    return _TAX(cpu, instruction);
}

void
op_TAY(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.y = cpu.a;
    cpu.set_zero(cpu.y == 0);
    cpu.set_negative(_is_bit_n_set(cpu.y, 0x7));
}

void
op_TSX(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.x = cpu.sp;
    cpu.set_zero(cpu.x == 0);
    cpu.set_negative(_is_bit_n_set(cpu.x, 0x7));
}

void
op_TXA(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.a = cpu.x;
    cpu.set_zero(cpu.a == 0);
    cpu.set_negative(_is_bit_n_set(cpu.a, 0x7));
}

void
op_TYA(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.a = cpu.y;
    cpu.set_zero(cpu.a == 0);
    cpu.set_negative(_is_bit_n_set(cpu.a, 0x7));
}

void
op_TXS(
    CPU& cpu,
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    cpu.sp = cpu.x;
}

void
NMI(CPU& cpu) {
    /*
     * Not an actual operation but handles the NMI interrupt.
     */
    // TODO
    // Not sure if this is the right way to handle the interrupt.
    // It may need to push status flugs and the previous program
    // counter to the stack.
    uint8_t nmi_low = cpu.memory.read_one(0xFFFA);
    uint16_t nmi_high = cpu.memory.read_one(0xFFFB);
    uint16_t nmi_address = (nmi_high << 8) + nmi_low;

    // I believe the assumption is that whatever handles the NMI
    // ultimately ends with an RTI (return from interrupt) so that
    // it goes back to where it should've gone. At that point it
    // wants to recover the address and flag state. I wonder if
    // other registers should also be restored (a, x, y?)
    cpu.stack.push_16(cpu.memory, cpu.sp, cpu.pc);
    cpu.stack.push_8(cpu.memory, cpu.sp, cpu.p);
    cpu.pc = nmi_address;
}

void
handle_instruction(
    CPU& cpu,
    Instruction& instruction,
    uint8_t* instruction_bytes
) {
    switch(instruction.mnemonic) {
        case Mnemonic::ADC: return op_ADC(cpu, instruction, instruction_bytes);
        case Mnemonic::AND: return op_AND(cpu, instruction, instruction_bytes);
        case Mnemonic::ASL: return op_ASL(cpu, instruction, instruction_bytes);
        case Mnemonic::BCC: return op_BCC(cpu, instruction, instruction_bytes);
        case Mnemonic::BCS: return op_BCS(cpu, instruction, instruction_bytes);
        case Mnemonic::BEQ: return op_BEQ(cpu, instruction, instruction_bytes);
        case Mnemonic::BIT: return op_BIT(cpu, instruction, instruction_bytes);
        case Mnemonic::BMI: return op_BMI(cpu, instruction, instruction_bytes);
        case Mnemonic::BNE: return op_BNE(cpu, instruction, instruction_bytes);
        case Mnemonic::BPL: return op_BPL(cpu, instruction, instruction_bytes);
        case Mnemonic::BRK: return op_BRK(cpu, instruction, instruction_bytes);
        case Mnemonic::BVC: return op_BVC(cpu, instruction, instruction_bytes);
        case Mnemonic::BVS: return op_BVS(cpu, instruction, instruction_bytes);
        case Mnemonic::CLC: return op_CLC(cpu, instruction, instruction_bytes);
        case Mnemonic::CLD: return op_CLD(cpu, instruction, instruction_bytes);
        case Mnemonic::CLV: return op_CLV(cpu, instruction, instruction_bytes);
        case Mnemonic::CMP: return op_CMP(cpu, instruction, instruction_bytes);
        case Mnemonic::CPX: return op_CPX(cpu, instruction, instruction_bytes);
        case Mnemonic::CPY: return op_CPY(cpu, instruction, instruction_bytes);
        case Mnemonic::DCP: return op_DCP(cpu, instruction, instruction_bytes);
        case Mnemonic::DEC: return op_DEC(cpu, instruction, instruction_bytes);
        case Mnemonic::DEX: return op_DEX(cpu, instruction, instruction_bytes);
        case Mnemonic::DEY: return op_DEY(cpu, instruction, instruction_bytes);
        case Mnemonic::EOR: return op_EOR(cpu, instruction, instruction_bytes);
        case Mnemonic::INC: return op_INC(cpu, instruction, instruction_bytes);
        case Mnemonic::INX: return op_INX(cpu, instruction, instruction_bytes);
        case Mnemonic::INY: return op_INY(cpu, instruction, instruction_bytes);
        case Mnemonic::ISB: return op_ISB(cpu, instruction, instruction_bytes);
        case Mnemonic::JMP: return op_JMP(cpu, instruction, instruction_bytes);
        case Mnemonic::JSR: return op_JSR(cpu, instruction, instruction_bytes);
        case Mnemonic::LAX: return op_LAX(cpu, instruction, instruction_bytes);
        case Mnemonic::LDA: return op_LDA(cpu, instruction, instruction_bytes);
        case Mnemonic::LDX: return op_LDX(cpu, instruction, instruction_bytes);
        case Mnemonic::LDY: return op_LDY(cpu, instruction, instruction_bytes);
        case Mnemonic::LSR: return op_LSR(cpu, instruction, instruction_bytes);
        case Mnemonic::NOP: return op_NOP(cpu, instruction, instruction_bytes);
        case Mnemonic::ORA: return op_ORA(cpu, instruction, instruction_bytes);
        case Mnemonic::PHA: return op_PHA(cpu, instruction, instruction_bytes);
        case Mnemonic::PHP: return op_PHP(cpu, instruction, instruction_bytes);
        case Mnemonic::PLA: return op_PLA(cpu, instruction, instruction_bytes);
        case Mnemonic::PLP: return op_PLP(cpu, instruction, instruction_bytes);
        case Mnemonic::RLA: return op_RLA(cpu, instruction, instruction_bytes);
        case Mnemonic::ROL: return op_ROL(cpu, instruction, instruction_bytes);
        case Mnemonic::ROR: return op_ROR(cpu, instruction, instruction_bytes);
        case Mnemonic::RRA: return op_RRA(cpu, instruction, instruction_bytes);
        case Mnemonic::RTI: return op_RTI(cpu, instruction, instruction_bytes);
        case Mnemonic::RTS: return op_RTS(cpu, instruction, instruction_bytes);
        case Mnemonic::SAX: return op_SAX(cpu, instruction, instruction_bytes);
        case Mnemonic::SBC: return op_SBC(cpu, instruction, instruction_bytes);
        case Mnemonic::SEC: return op_SEC(cpu, instruction, instruction_bytes);
        case Mnemonic::SED: return op_SED(cpu, instruction, instruction_bytes);
        case Mnemonic::SEI: return op_SEI(cpu, instruction, instruction_bytes);
        case Mnemonic::SLO: return op_SLO(cpu, instruction, instruction_bytes);
        case Mnemonic::SRE: return op_SRE(cpu, instruction, instruction_bytes);
        case Mnemonic::STA: return op_STA(cpu, instruction, instruction_bytes);
        case Mnemonic::STX: return op_STX(cpu, instruction, instruction_bytes);
        case Mnemonic::STY: return op_STY(cpu, instruction, instruction_bytes);
        case Mnemonic::TAX: return op_TAX(cpu, instruction, instruction_bytes);
        case Mnemonic::TAY: return op_TAY(cpu, instruction, instruction_bytes);
        case Mnemonic::TSX: return op_TSX(cpu, instruction, instruction_bytes);
        case Mnemonic::TXA: return op_TXA(cpu, instruction, instruction_bytes);
        case Mnemonic::TXS: return op_TXS(cpu, instruction, instruction_bytes);
        case Mnemonic::TYA: return op_TYA(cpu, instruction, instruction_bytes);
        default: {
            printf("Unhandled mnemonic %d\n", instruction.mnemonic);
            std::throw_with_nested(
                std::runtime_error("Unhandled mnemonic.\n")
            );
        }
    }
}
