#ifndef CONSTANTS_H
#define CONSTANTS_H

#include <string>
#include <unistd.h>

enum class Mnemonic {
    ADC,
    AND,
    ASL,
    BCC,
    BCS,
    BEQ,
    BIT,
    BMI,
    BNE,
    BPL,
    BRK,
    BVC,
    BVS,
    CLC,
    CLD,
    CLV,
    CMP,
    CPX,
    CPY,
    DCP,
    DEC,
    DEX,
    DEY,
    EOR,
    INC,
    INX,
    INY,
    ISB,
    JMP,
    JSR,
    LAX,
    LDA,
    LDX,
    LDY,
    LSR,
    NOP,
    ORA,
    PHA,
    PHP,
    PLA,
    PLP,
    RLA,
    ROL,
    ROR,
    RRA,
    RTI,
    RTS,
    SAX,
    SBC,
    SEC,
    SED,
    SEI,
    SLO,
    SRE,
    STA,
    STX,
    STY,
    TAX,
    TAY,
    TSX,
    TXA,
    TXS,
    TYA
};

enum class AddressingMode {
    ABSOLUTE,
    // "The address to be accessed by an instruction using X
    // register indexed absolute addressing is computed by taking
    // the 16 bit address from the instruction and added the
    // contents of the X register."
    // "For example if X contains $92 then an STA $2000,X instruction
    // will store the accumulator at $2092 (e.g. $2000 + $92).""
    ABSOLUTE_X,
    // "The Y register indexed absolute addressing mode is the same
    // as the previous mode only with the contents of the Y register
    // added to the 16 bit address from the instruction."
    ABSOLUTE_Y,
    ACCUMULATOR,
    IMMEDIATE,
    IMPLIED,
    // "JMP is the only 6502 instruction to support indirection.
    // The instruction contains a 16 bit address which identifies
    // the location of the least significant byte of another 16
    // bit memory address which is the real target of the
    // instruction."
    // "For example if location $0120 contains $FC and location
    // $0121 contains $BA then the instruction JMP ($0120) will
    // cause the next instruction execution to occur at $BAFC
    // (e.g. the contents of $0120 and $0121)."
    INDIRECT,
    // "Indexed indirect addressing is normally used in conjunction
    // with a table of address held on zero page. The address of
    // the table is taken from the instruction and the X register
    // added to it (with zero page wrap around) to give the location
    // of the least significant byte of the target address."
    // Or in simpler terms, it's just a pointer to another address
    // where we can get the pointer to the real data.
    INDIRECT_X,
    // "Indirect indirect addressing is the most common indirection
    // mode used on the 6502. In instruction contains the zero page
    // location of the least significant byte of 16 bit address. The
    // Y register is dynamically added to this value to generated
    // the actual target address for operation."
    INDIRECT_Y,
    RELATIVE,
    ZEROPAGE,
    // "The address to be accessed by an instruction using indexed
    // zero page addressing is calculated by taking the 8 bit zero
    // page address from the instruction and adding the current
    // value of the X register to it. For example if the X register
    // contains $0F and the instruction LDA $80,X is executed then
    // the accumulator will be loaded from $008F
    // (e.g. $80 + $0F => $8F)."
    // "NB:
    // The address calculation wraps around if the sum of the base
    // address and the register exceed $FF. If we repeat the last
    // example but with $FF in the X register then the accumulator
    // will be loaded from $007F (e.g. $80 + $FF => $7F) and not
    // $017F."
    ZEROPAGE_X,
    // "The address to be accessed by an instruction using indexed
    // zero page addressing is calculated by taking the 8 bit zero
    // page address from the instruction and adding the current
    // value of the Y register to it. This mode can only be used
    // with the LDX and STX instructions.
    ZEROPAGE_Y
};

enum class PPUAddress {
    // PPU Registers are memory-mapped. In other words, they're
    // backed by locations in the CPU memory. That said, the PPU
    // also has its own memory.
    PPUCTRL_ADDRESS = 0x2000,
    PPUMASK_ADDRESS = 0x2001,
    PPUSTATUS_ADDRESS = 0x2002,
    OAMADDR_ADDRESS = 0x2003,
    OAMDATA_ADDRESS = 0x2004,
    PPUSCROLL_ADDRESS = 0x2005,
    PPUADDR_ADDRESS = 0x2006,
    PPUDATA_ADDRESS = 0x2007,
    // This one is technically a port on the CPU.
    OAMDMA_ADDRESS = 0x4014
};

enum class PPURegister {
    PPUCTRL,
    PPUMASK,
    PPUSTATUS,
    OAMADDR,
    OAMDATA,
    PPUSCROLL,
    PPUADDR,
    PPUDATA,
    OAMDMA,
    NONE
};

enum class JoypadAddress {
    JOYPAD1 = 0x4016,
    JOYPAD2 = 0x4017,
};

inline bool
IsBranchingMnemonic(Mnemonic mnemonic) {
    // Another option for this is a LUT, but most of the entires
    // would be false.
    switch (mnemonic) {
        case Mnemonic::BRK:
        case Mnemonic::JMP:
        case Mnemonic::JSR:
        case Mnemonic::RTI:
        // Because these can result in page crossing penalties
        // depending on where the PC is pointing to, we need
        // to handle the final PC address all together in the
        // instruction handler. This is kind of unfortunate
        // but oh well...
        case Mnemonic::BEQ:
            return true;
        default:
            return false;
    }
}

const static uint16_t PPUCyclesPerScanline = 341;
// 3 PPU cycles per CPU cycle.
const static uint16_t PPUCyclesPerCPUCycle = 3;
const static uint16_t PPUMaxScanline = 261;
const static uint16_t PPUVBlankScanline = 241;

// Assuming _store_data_for_mode is only ever writing 1 byte.
// That might need to be changed for multiple value writing is
// supported.
inline bool
IsUnsupportedStorageAddressModes(AddressingMode mode) {
    // Another option for this is a LUT, but most of the entires
    // would be false.
    switch (mode) {
        case AddressingMode::IMMEDIATE:
        case AddressingMode::IMPLIED:
        case AddressingMode::INDIRECT:
        case AddressingMode::RELATIVE:
            return true;
        default:
            return false;
    }
}

const static uint16_t NametableSize = 0x400;

enum class NametableMirroring {
    HORIZONTAL,
    VERTICAL,
    NONE
};

// https://stackoverflow.com/questions/746171/efficient-algorithm-for-bit-reversal-from-msb-lsb-to-lsb-msb-in-c
static const unsigned char ByteReverseTable[] = {
    0x00, 0x80, 0x40, 0xC0, 0x20, 0xA0, 0x60, 0xE0, 0x10, 0x90, 0x50, 0xD0, 0x30, 0xB0, 0x70, 0xF0,
    0x08, 0x88, 0x48, 0xC8, 0x28, 0xA8, 0x68, 0xE8, 0x18, 0x98, 0x58, 0xD8, 0x38, 0xB8, 0x78, 0xF8,
    0x04, 0x84, 0x44, 0xC4, 0x24, 0xA4, 0x64, 0xE4, 0x14, 0x94, 0x54, 0xD4, 0x34, 0xB4, 0x74, 0xF4,
    0x0C, 0x8C, 0x4C, 0xCC, 0x2C, 0xAC, 0x6C, 0xEC, 0x1C, 0x9C, 0x5C, 0xDC, 0x3C, 0xBC, 0x7C, 0xFC,
    0x02, 0x82, 0x42, 0xC2, 0x22, 0xA2, 0x62, 0xE2, 0x12, 0x92, 0x52, 0xD2, 0x32, 0xB2, 0x72, 0xF2,
    0x0A, 0x8A, 0x4A, 0xCA, 0x2A, 0xAA, 0x6A, 0xEA, 0x1A, 0x9A, 0x5A, 0xDA, 0x3A, 0xBA, 0x7A, 0xFA,
    0x06, 0x86, 0x46, 0xC6, 0x26, 0xA6, 0x66, 0xE6, 0x16, 0x96, 0x56, 0xD6, 0x36, 0xB6, 0x76, 0xF6,
    0x0E, 0x8E, 0x4E, 0xCE, 0x2E, 0xAE, 0x6E, 0xEE, 0x1E, 0x9E, 0x5E, 0xDE, 0x3E, 0xBE, 0x7E, 0xFE,
    0x01, 0x81, 0x41, 0xC1, 0x21, 0xA1, 0x61, 0xE1, 0x11, 0x91, 0x51, 0xD1, 0x31, 0xB1, 0x71, 0xF1,
    0x09, 0x89, 0x49, 0xC9, 0x29, 0xA9, 0x69, 0xE9, 0x19, 0x99, 0x59, 0xD9, 0x39, 0xB9, 0x79, 0xF9,
    0x05, 0x85, 0x45, 0xC5, 0x25, 0xA5, 0x65, 0xE5, 0x15, 0x95, 0x55, 0xD5, 0x35, 0xB5, 0x75, 0xF5,
    0x0D, 0x8D, 0x4D, 0xCD, 0x2D, 0xAD, 0x6D, 0xED, 0x1D, 0x9D, 0x5D, 0xDD, 0x3D, 0xBD, 0x7D, 0xFD,
    0x03, 0x83, 0x43, 0xC3, 0x23, 0xA3, 0x63, 0xE3, 0x13, 0x93, 0x53, 0xD3, 0x33, 0xB3, 0x73, 0xF3,
    0x0B, 0x8B, 0x4B, 0xCB, 0x2B, 0xAB, 0x6B, 0xEB, 0x1B, 0x9B, 0x5B, 0xDB, 0x3B, 0xBB, 0x7B, 0xFB,
    0x07, 0x87, 0x47, 0xC7, 0x27, 0xA7, 0x67, 0xE7, 0x17, 0x97, 0x57, 0xD7, 0x37, 0xB7, 0x77, 0xF7,
    0x0F, 0x8F, 0x4F, 0xCF, 0x2F, 0xAF, 0x6F, 0xEF, 0x1F, 0x9F, 0x5F, 0xDF, 0x3F, 0xBF, 0x7F, 0xFF
};

enum class Input {
    A,
    B,
    SELECT,
    START,
    UP,
    DOWN,
    LEFT,
    RIGHT
};

static const char* INPUT_A =      "A";
static const char* INPUT_B =      "B";
static const char* INPUT_SELECT = "SELECT";
static const char* INPUT_START =  "START";
static const char* INPUT_UP =     "UP";
static const char* INPUT_DOWN =   "DOWN";
static const char* INPUT_LEFT =   "LEFT";
static const char* INPUT_RIGHT =  "RIGHT";

inline static const char*
InputToString(Input input) {
    switch (input) {
        case Input::A: return INPUT_A;
        case Input::B: return INPUT_B;
        case Input::SELECT: return INPUT_SELECT;
        case Input::START: return INPUT_START;
        case Input::UP: return INPUT_UP;
        case Input::DOWN: return INPUT_DOWN;
        case Input::LEFT: return INPUT_LEFT;
        case Input::RIGHT: return INPUT_RIGHT;
    }
}
#endif
