#ifndef OPCODES_H
#define OPCODES_H

#include <unordered_map>
#include "Constants.h"

struct Instruction {
    uint8_t opcode;
    Mnemonic mnemonic;
    uint8_t bytes;
    uint8_t cycles;
    AddressingMode addressing_mode;
    // Last two won't be set if there is no penalty on the
    // operation for crossing pages or for branching.
    uint8_t branch_cycles = 0;
    uint8_t page_crossing_cycles = 0;
public:
    // Allow an 'empty' construction just as a placeholder
    // for opcodes that aren't implemented. (We still want
    // to show the opcode for legibility purposes even at the
    // cost of a small amount of memory).
    Instruction(uint8_t opcode) : opcode(opcode) {}
    // FIXME
    // There's got to be a better way to do this.
    // Initializer base
    Instruction(
        uint8_t opcode,
        Mnemonic mnemonic,
        uint8_t bytes,
        uint8_t cycles,
        AddressingMode addressing_mode
    ) :
    opcode(opcode),
    mnemonic(mnemonic),
    bytes(bytes),
    cycles(cycles),
    addressing_mode(addressing_mode) {}

    // Initializer for branch_cycles
    Instruction(
        uint8_t opcode,
        Mnemonic mnemonic,
        uint8_t bytes,
        uint8_t cycles,
        AddressingMode addressing_mode,
        uint8_t branch_cycles
    ) :
    opcode(opcode),
    mnemonic(mnemonic),
    bytes(bytes),
    cycles(cycles),
    addressing_mode(addressing_mode),
    branch_cycles(branch_cycles) {}

    // Initializer for page_crossing_cycles
    Instruction(
        uint8_t opcode,
        Mnemonic mnemonic,
        uint8_t bytes,
        uint8_t cycles,
        AddressingMode addressing_mode,
        uint8_t branch_cycles,
        uint8_t page_crossing_cycles
    ) :
    opcode(opcode),
    mnemonic(mnemonic),
    bytes(bytes),
    cycles(cycles),
    addressing_mode(addressing_mode),
    branch_cycles(branch_cycles),
    page_crossing_cycles(page_crossing_cycles) {}
};

static Instruction Instructions[] = {
    { 0x0, Mnemonic::BRK, 1, 7, AddressingMode::IMPLIED },
    { 0x1, Mnemonic::ORA, 2, 6, AddressingMode::INDIRECT_X },
    { 0x2 },
    { 0x3, Mnemonic::SLO, 2, 8, AddressingMode::INDIRECT_X },
    { 0x4, Mnemonic::NOP, 2, 3, AddressingMode::ZEROPAGE },
    { 0x5, Mnemonic::ORA, 2, 3, AddressingMode::ZEROPAGE },
    { 0x6, Mnemonic::ASL, 2, 5, AddressingMode::ZEROPAGE },
    { 0x7, Mnemonic::SLO, 2, 5, AddressingMode::ZEROPAGE },
    { 0x8, Mnemonic::PHP, 1, 3, AddressingMode::IMPLIED },
    { 0x9, Mnemonic::ORA, 2, 2, AddressingMode::IMMEDIATE },
    { 0xa, Mnemonic::ASL, 1, 2, AddressingMode::ACCUMULATOR },
    { 0xb },
    { 0xc, Mnemonic::NOP, 3, 4, AddressingMode::ABSOLUTE },
    { 0xd, Mnemonic::ORA, 3, 4, AddressingMode::ABSOLUTE },
    { 0xe, Mnemonic::ASL, 3, 6, AddressingMode::ABSOLUTE },
    { 0xf, Mnemonic::SLO, 3, 6, AddressingMode::ABSOLUTE },
    // Conditional cycles: 2 is the base,
    // +1 if branch succeeds, +2 if there is a new page.
    { 0x10, Mnemonic::BPL, 2, 2, AddressingMode::RELATIVE, 1, 2 },
    // Conditional cycles: 5 is the base,
    // +1 if page crossed.
    { 0x11, Mnemonic::ORA, 2, 5, AddressingMode::INDIRECT_Y, 0, 1 },
    { 0x12 },
    { 0x13, Mnemonic::SLO, 2, 8, AddressingMode::INDIRECT_Y },
    { 0x14, Mnemonic::NOP, 2, 4, AddressingMode::ZEROPAGE },
    { 0x15, Mnemonic::ORA, 2, 4, AddressingMode::ZEROPAGE_X },
    { 0x16, Mnemonic::ASL, 2, 6, AddressingMode::ZEROPAGE_X },
    { 0x17, Mnemonic::SLO, 2, 6, AddressingMode::ZEROPAGE_X },
    { 0x18, Mnemonic::CLC, 1, 2, AddressingMode::IMPLIED },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0x19, Mnemonic::ORA, 3, 4, AddressingMode::ABSOLUTE_Y, 0, 1 },
    { 0x1a, Mnemonic::NOP, 1, 2, AddressingMode::IMPLIED },
    { 0x1b, Mnemonic::SLO, 3, 7, AddressingMode::ABSOLUTE_Y },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0x1c, Mnemonic::NOP, 3, 4, AddressingMode::ABSOLUTE_X, 0, 1 },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0x1d, Mnemonic::ORA, 3, 4, AddressingMode::ABSOLUTE_X, 0, 1 },
    { 0x1e, Mnemonic::ASL, 3, 7, AddressingMode::ABSOLUTE_X },
    { 0x1f, Mnemonic::SLO, 3, 7, AddressingMode::ABSOLUTE_X },
    { 0x20, Mnemonic::JSR, 3, 6, AddressingMode::ABSOLUTE },
    { 0x21, Mnemonic::AND, 2, 6, AddressingMode::INDIRECT_X },
    { 0x22 },
    { 0x23, Mnemonic::RLA, 2, 8, AddressingMode::INDIRECT_X },
    { 0x24, Mnemonic::BIT, 2, 3, AddressingMode::ZEROPAGE },
    { 0x25, Mnemonic::AND, 2, 3, AddressingMode::ZEROPAGE },
    { 0x26, Mnemonic::ROL, 2, 5, AddressingMode::ZEROPAGE },
    { 0x27, Mnemonic::RLA, 2, 5, AddressingMode::ZEROPAGE },
    { 0x28, Mnemonic::PLP, 1, 4, AddressingMode::IMPLIED },
    { 0x29, Mnemonic::AND, 2, 2, AddressingMode::IMMEDIATE },
    { 0x2a, Mnemonic::ROL, 1, 2, AddressingMode::ACCUMULATOR },
    { 0x2b },
    { 0x2c, Mnemonic::BIT, 3, 4, AddressingMode::ABSOLUTE },
    { 0x2d, Mnemonic::AND, 3, 4, AddressingMode::ABSOLUTE },
    { 0x2e, Mnemonic::ROL, 3, 6, AddressingMode::ABSOLUTE },
    { 0x2f, Mnemonic::RLA, 3, 6, AddressingMode::ABSOLUTE },
    // Conditional cycles: 2 is the base,
    // +1 if branch succeeds, +2 if there is a new page.
    // So basically if we want realism with the branching
    // we need to account for page in / out.
    { 0x30, Mnemonic::BMI, 2, 2, AddressingMode::RELATIVE, 1, 2 },
    // Conditional cycles: 5 is the base,
    // +1 if page crossed.
    { 0x31, Mnemonic::AND, 2, 5, AddressingMode::INDIRECT_Y, 0, 1 },
    { 0x32 },
    { 0x33, Mnemonic::RLA, 2, 8, AddressingMode::INDIRECT_Y },
    { 0x34, Mnemonic::NOP, 2, 4, AddressingMode::ZEROPAGE },
    { 0x35, Mnemonic::AND, 2, 4, AddressingMode::ZEROPAGE_X },
    { 0x36, Mnemonic::ROL, 2, 6, AddressingMode::ZEROPAGE_X },
    { 0x37, Mnemonic::RLA, 2, 6, AddressingMode::ZEROPAGE_X },
    { 0x38, Mnemonic::SEC, 1, 2, AddressingMode::IMPLIED },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0x39, Mnemonic::AND, 3, 4, AddressingMode::ABSOLUTE_Y, 0, 1 },
    { 0x3a, Mnemonic::NOP, 1, 2, AddressingMode::IMPLIED },
    { 0x3b, Mnemonic::RLA, 3, 7, AddressingMode::ABSOLUTE_Y },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0x3c, Mnemonic::NOP, 3, 4, AddressingMode::ABSOLUTE_X, 0, 1 },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0x3d, Mnemonic::AND, 3,  4, AddressingMode::ABSOLUTE_X, 0, 1 },
    { 0x3e, Mnemonic::ROL, 3, 7, AddressingMode::ABSOLUTE_X },
    { 0x3f, Mnemonic::RLA, 3, 7, AddressingMode::ABSOLUTE_X },
    { 0x40, Mnemonic::RTI, 1, 6, AddressingMode::IMPLIED },
    { 0x41, Mnemonic::EOR, 2, 6, AddressingMode::INDIRECT_X },
    { 0x42 },
    { 0x43, Mnemonic::SRE, 2, 8, AddressingMode::INDIRECT_X },
    { 0x44, Mnemonic::NOP, 2, 3, AddressingMode::ZEROPAGE },
    { 0x45, Mnemonic::EOR, 2, 3, AddressingMode::ZEROPAGE },
    { 0x46, Mnemonic::LSR, 2, 5, AddressingMode::ZEROPAGE },
    { 0x47, Mnemonic::SRE, 2, 5, AddressingMode::ZEROPAGE },
    { 0x48, Mnemonic::PHA, 1, 3, AddressingMode::IMPLIED },
    { 0x49, Mnemonic::EOR, 2, 2, AddressingMode::IMMEDIATE },
    { 0x4a, Mnemonic::LSR, 1, 2, AddressingMode::ACCUMULATOR },
    { 0x4b },
    { 0x4c, Mnemonic::JMP, 3, 3, AddressingMode::ABSOLUTE },
    { 0x4d, Mnemonic::EOR, 3, 4, AddressingMode::ABSOLUTE },
    { 0x4e, Mnemonic::LSR, 3, 6, AddressingMode::ABSOLUTE },
    { 0x4f, Mnemonic::SRE, 3, 6, AddressingMode::ABSOLUTE },
    // Conditional cycles: 2 is the base,
    // +1 if branch succeeds, +2 if there is a new page.
    { 0x50, Mnemonic::BVC, 2,  2, AddressingMode::RELATIVE, 1, 2 },
    // Conditional cycles: 5 is the base,
    // +1 if page crossed.
    { 0x51, Mnemonic::EOR, 2,  5, AddressingMode::INDIRECT_Y, 0, 1 },
    { 0x52 },
    { 0x53, Mnemonic::SRE, 2, 8, AddressingMode::INDIRECT_Y },
    { 0x54, Mnemonic::NOP, 2, 4, AddressingMode::ZEROPAGE },
    { 0x55, Mnemonic::EOR, 2, 4, AddressingMode::ZEROPAGE_X },
    { 0x56, Mnemonic::LSR, 2, 6, AddressingMode::ZEROPAGE_X },
    { 0x57, Mnemonic::SRE, 2, 6, AddressingMode::ZEROPAGE_X },
    { 0x58 },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0x59, Mnemonic::EOR, 3,  4, AddressingMode::ABSOLUTE_Y, 0, 1 },
    { 0x5a, Mnemonic::NOP, 1, 2, AddressingMode::IMPLIED },
    { 0x5b, Mnemonic::SRE, 3, 7, AddressingMode::ABSOLUTE_Y },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0x5c, Mnemonic::NOP, 3,  4, AddressingMode::ABSOLUTE_X, 0, 1 },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0x5d, Mnemonic::EOR, 3,  4, AddressingMode::ABSOLUTE_X, 0, 1 },
    { 0x5e, Mnemonic::LSR, 3, 7, AddressingMode::ABSOLUTE_X },
    { 0x5f, Mnemonic::SRE, 3, 7, AddressingMode::ABSOLUTE_X },
    // Conditional cycles: 2 is the base,
    // +1 if branch succeeds, +2 if there is a new page.
    // So basically if we want realism with the branching
    // we need to account for page in / out.
    { 0x60, Mnemonic::RTS, 1,  6, AddressingMode::IMPLIED },
    { 0x61, Mnemonic::ADC, 2, 6, AddressingMode::INDIRECT_X },
    { 0x62 },
    { 0x63, Mnemonic::RRA, 2, 8, AddressingMode::INDIRECT_X },
    { 0x64, Mnemonic::NOP, 2, 3, AddressingMode::ZEROPAGE },
    { 0x65, Mnemonic::ADC, 2, 3, AddressingMode::ZEROPAGE },
    { 0x66, Mnemonic::ROR, 2, 5, AddressingMode::ZEROPAGE },
    { 0x67, Mnemonic::RRA, 2, 5, AddressingMode::ZEROPAGE },
    { 0x68, Mnemonic::PLA, 1, 4, AddressingMode::IMPLIED },
    { 0x69, Mnemonic::ADC, 2, 2, AddressingMode::IMMEDIATE },
    { 0x6a, Mnemonic::ROR, 1, 2, AddressingMode::ACCUMULATOR },
    { 0x6b },
    { 0x6c, Mnemonic::JMP, 3, 5, AddressingMode::INDIRECT },
    { 0x6d, Mnemonic::ADC, 3, 4, AddressingMode::ABSOLUTE },
    { 0x6e, Mnemonic::ROR, 3, 6, AddressingMode::ABSOLUTE },
    { 0x6f, Mnemonic::RRA, 3, 6, AddressingMode::ABSOLUTE },
    // Conditional cycles: 2 is the base,
    // +1 if branch succeeds, +2 if there is a new page.
    // So basically if we want realism with the branching
    // we need to account for page in / out.
    { 0x70, Mnemonic::BVS, 2,  2, AddressingMode::RELATIVE, 1, 2 },
    // Conditional cycles: 5 is the base,
    // +1 if page crossed.
    { 0x71, Mnemonic::ADC, 2,  5, AddressingMode::INDIRECT_Y, 0, 1 },
    { 0x72 },
    { 0x73, Mnemonic::RRA, 2, 8, AddressingMode::INDIRECT_Y },
    { 0x74, Mnemonic::NOP, 2, 4, AddressingMode::ZEROPAGE },
    { 0x75, Mnemonic::ADC, 2, 4, AddressingMode::ZEROPAGE_X },
    { 0x76, Mnemonic::ROR, 2, 6, AddressingMode::ZEROPAGE_X },
    { 0x77, Mnemonic::RRA, 2, 6, AddressingMode::ZEROPAGE_X },
    { 0x78, Mnemonic::SEI, 1, 2, AddressingMode::IMPLIED },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0x79, Mnemonic::ADC, 3,  4, AddressingMode::ABSOLUTE_Y, 0, 1 },
    { 0x7a, Mnemonic::NOP, 1, 2, AddressingMode::IMPLIED },
    { 0x7b, Mnemonic::RRA, 3, 7, AddressingMode::ABSOLUTE_Y },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0x7c, Mnemonic::NOP, 3,  4, AddressingMode::ABSOLUTE_X, 0, 1 },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0x7d, Mnemonic::ADC, 3,  4, AddressingMode::ABSOLUTE_X, 0, 1 },
    { 0x7e, Mnemonic::ROR, 3, 7, AddressingMode::ABSOLUTE_X },
    { 0x7f, Mnemonic::RRA, 3, 7, AddressingMode::ABSOLUTE_X },
    { 0x80, Mnemonic::NOP, 2, 2, AddressingMode::IMMEDIATE },
    { 0x81, Mnemonic::STA, 2, 6, AddressingMode::INDIRECT_X },
    { 0x82, Mnemonic::NOP, 1, 2, AddressingMode::IMPLIED },
    { 0x83, Mnemonic::SAX, 2, 6, AddressingMode::INDIRECT_X },
    // TODO
    // For testing, we can ensure that we're only writing from 0x0
    // up to 0xFF since that's the ZERO_PAGE adderssing mode.
    // For now this is actually going to let it write anywhere in
    // the address, so we might wanna check that.
    { 0x84, Mnemonic::STY, 2, 3, AddressingMode::ZEROPAGE },
    // TODO
    // For testing, we can ensure that we're only writing from 0x0
    // up to 0xFF since that's the ZERO_PAGE adderssing mode.
    // For now this is actually going to let it write anywhere in
    // the address, so we might wanna check that.
    { 0x85, Mnemonic::STA, 2, 3, AddressingMode::ZEROPAGE },
    // TODO
    // For testing, we can ensure that we're only writing from 0x0
    // up to 0xFF since that's the ZERO_PAGE adderssing mode.
    // For now this is actually going to let it write anywhere in
    // the address, so we might wanna check that.
    { 0x86, Mnemonic::STX, 2, 3, AddressingMode::ZEROPAGE },
    { 0x87, Mnemonic::SAX, 2, 3, AddressingMode::ZEROPAGE },
    { 0x88, Mnemonic::DEY, 1, 2, AddressingMode::IMPLIED },
    { 0x89, Mnemonic::NOP, 1, 2, AddressingMode::IMPLIED },
    { 0x8a, Mnemonic::TXA, 1, 2, AddressingMode::RELATIVE },
    { 0x8b },
    { 0x8c, Mnemonic::STY, 3, 4, AddressingMode::ABSOLUTE },
    { 0x8d, Mnemonic::STA, 3, 4, AddressingMode::ABSOLUTE },
    { 0x8e, Mnemonic::STX, 3, 4, AddressingMode::ABSOLUTE },
    { 0x8f, Mnemonic::SAX, 3, 4, AddressingMode::ABSOLUTE },
    // Conditional cycles: 2 is the base,
    // +1 if branch succeeds, +2 if there is a new page.
    // So basically if we want realism with the branching
    // we need to account for page in / out.
    { 0x90, Mnemonic::BCC, 2,  2, AddressingMode::RELATIVE, 1, 2 },
    { 0x91, Mnemonic::STA, 2, 6, AddressingMode::INDIRECT_Y },
    { 0x92 },
    { 0x93 },
    { 0x94, Mnemonic::STY, 2, 4, AddressingMode::ZEROPAGE_X },
    { 0x95, Mnemonic::STA, 2, 4, AddressingMode::ZEROPAGE_X },
    { 0x96, Mnemonic::STX, 2, 4, AddressingMode::ZEROPAGE_Y },
    { 0x97, Mnemonic::SAX, 2, 4, AddressingMode::ZEROPAGE_Y },
    { 0x98, Mnemonic::TYA, 1, 2, AddressingMode::RELATIVE },
    { 0x99, Mnemonic::STA, 3, 5, AddressingMode::ABSOLUTE_Y },
    { 0x9a, Mnemonic::TXS, 1, 2, AddressingMode::IMPLIED },
    { 0x9b },
    { 0x9c },
    { 0x9d, Mnemonic::STA, 3, 5, AddressingMode::ABSOLUTE_X },
    { 0x9e },
    { 0x9f },
    { 0xa0, Mnemonic::LDY, 2, 2, AddressingMode::IMMEDIATE },
    { 0xa1, Mnemonic::LDA, 2, 6, AddressingMode::INDIRECT_X },
    { 0xa2, Mnemonic::LDX, 2, 2, AddressingMode::IMMEDIATE },
    { 0xa3, Mnemonic::LAX, 2, 6, AddressingMode::INDIRECT_X },
    { 0xa4, Mnemonic::LDY, 2, 3, AddressingMode::ZEROPAGE },
    { 0xa5, Mnemonic::LDA, 2, 3, AddressingMode::ZEROPAGE },
    { 0xa6, Mnemonic::LDX, 2, 3, AddressingMode::ZEROPAGE },
    { 0xa7, Mnemonic::LAX, 2, 3, AddressingMode::ZEROPAGE },
    { 0xa8, Mnemonic::TAY, 1, 2, AddressingMode::IMPLIED },
    { 0xa9, Mnemonic::LDA, 2, 2, AddressingMode::IMMEDIATE },
    { 0xaa, Mnemonic::TAX, 1, 2, AddressingMode::IMPLIED },
    { 0xab },
    { 0xac, Mnemonic::LDY, 3, 4, AddressingMode::ABSOLUTE },
    { 0xad, Mnemonic::LDA, 3, 4, AddressingMode::ABSOLUTE },
    { 0xae, Mnemonic::LDX, 3, 4, AddressingMode::ABSOLUTE },
    { 0xaf, Mnemonic::LAX, 3, 4, AddressingMode::ABSOLUTE },
    // Conditional cycles: 2 is the base,
    // +1 if branch succeeds, +2 if there is a new page.
    { 0xb0, Mnemonic::BCS, 2,  2, AddressingMode::RELATIVE, 1 },
    // Conditional cycles: 5 is the base,
    // +1 if page crossed.
    { 0xb1, Mnemonic::LDA, 2,  5, AddressingMode::INDIRECT_Y, 0, 1 },
    { 0xb2 },
    { 0xb3, Mnemonic::LAX, 2, 5, AddressingMode::INDIRECT_Y, 0, 1 },
    { 0xb4, Mnemonic::LDY, 2, 4, AddressingMode::ZEROPAGE_X },
    { 0xb5, Mnemonic::LDA, 2, 4, AddressingMode::ZEROPAGE_X },
    { 0xb6, Mnemonic::LDX, 2, 4, AddressingMode::ZEROPAGE_Y },
    // Although the chart above says ZERO PAGE X
    // it should actually be using the y register (i.e. ZERO PAGE Y).
    { 0xb7, Mnemonic::LAX, 2, 4, AddressingMode::ZEROPAGE_Y },
    { 0xb8, Mnemonic::CLV, 1, 2, AddressingMode::IMPLIED },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0xb9, Mnemonic::LDA, 3,  4, AddressingMode::ABSOLUTE_Y, 0, 1 },
    { 0xba, Mnemonic::TSX, 1, 2, AddressingMode::IMPLIED },
    { 0xbb },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0xbc, Mnemonic::LDY, 3,  4, AddressingMode::ABSOLUTE_X, 0, 1 },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0xbd, Mnemonic::LDA, 3,  4, AddressingMode::ABSOLUTE_X, 0, 1 },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0xbe, Mnemonic::LDX, 3,  4, AddressingMode::ABSOLUTE_Y, 0, 1 },
    // Although the chart above says ABSOLUTE X
    // it should actually be using the y register (i.e. ABSOLUTE Y).
    { 0xbf, Mnemonic::LAX, 3, 4, AddressingMode::ABSOLUTE_Y },
    { 0xc0, Mnemonic::CPY, 2, 2, AddressingMode::IMMEDIATE },
    { 0xc1, Mnemonic::CMP, 2, 6, AddressingMode::INDIRECT_X },
    { 0xc2, Mnemonic::NOP, 1, 2, AddressingMode::IMPLIED },
    { 0xc3, Mnemonic::DCP, 2, 8, AddressingMode::INDIRECT_X },
    { 0xc4, Mnemonic::CPY, 2, 3, AddressingMode::ZEROPAGE },
    { 0xc5, Mnemonic::CMP, 2, 3, AddressingMode::ZEROPAGE },
    { 0xc6, Mnemonic::DEC, 2, 5, AddressingMode::ZEROPAGE },
    { 0xc7, Mnemonic::DCP, 2, 5, AddressingMode::ZEROPAGE },
    { 0xc8, Mnemonic::INY, 1, 2, AddressingMode::IMPLIED },
    { 0xc9, Mnemonic::CMP, 2, 2, AddressingMode::IMMEDIATE },
    { 0xca, Mnemonic::DEX, 1, 2, AddressingMode::IMPLIED },
    { 0xcb },
    { 0xcc, Mnemonic::CPY, 3, 4, AddressingMode::ABSOLUTE },
    { 0xcd, Mnemonic::CMP, 3, 4, AddressingMode::ABSOLUTE },
    { 0xce, Mnemonic::DEC, 3, 6, AddressingMode::ABSOLUTE },
    { 0xcf, Mnemonic::DCP, 3, 6, AddressingMode::ABSOLUTE },
    // Conditional cycles: 2 is the base,
    // +1 if branch succeeds, +2 if there is a new page.
    { 0xd0, Mnemonic::BNE, 2,  2, AddressingMode::RELATIVE, 1, 2 },
    // Conditional cycles: 5 is the base,
    // +1 if page crossed.
    { 0xd1, Mnemonic::CMP, 2,  5, AddressingMode::INDIRECT_Y, 0, 1 },
    { 0xd2 },
    { 0xd3, Mnemonic::DCP, 2, 8, AddressingMode::INDIRECT_Y },
    { 0xd4, Mnemonic::NOP, 2, 4, AddressingMode::ZEROPAGE },
    { 0xd5, Mnemonic::CMP, 2, 4, AddressingMode::ZEROPAGE_X },
    { 0xd6, Mnemonic::DEC, 2, 6, AddressingMode::ZEROPAGE_X },
    { 0xd7, Mnemonic::DCP, 2, 6, AddressingMode::ZEROPAGE_X },
    { 0xd8, Mnemonic::CLD, 1, 2, AddressingMode::IMPLIED },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0xd9, Mnemonic::CMP, 3,  4, AddressingMode::ABSOLUTE_Y, 0, 1 },
    { 0xda, Mnemonic::NOP, 1, 2, AddressingMode::IMPLIED },
    { 0xdb, Mnemonic::DCP, 3, 7, AddressingMode::ABSOLUTE_Y },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0xdc, Mnemonic::NOP, 3,  4, AddressingMode::ABSOLUTE_X, 0, 1 },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0xdd, Mnemonic::CMP, 3,  4, AddressingMode::ABSOLUTE_X, 0, 1 },
    { 0xde, Mnemonic::DEC, 3, 7, AddressingMode::ABSOLUTE_X },
    { 0xdf, Mnemonic::DCP, 3, 7, AddressingMode::ABSOLUTE_X },
    { 0xe0, Mnemonic::CPX, 2, 2, AddressingMode::IMMEDIATE },
    { 0xe1, Mnemonic::SBC, 2, 6, AddressingMode::INDIRECT_X },
    { 0xe2, Mnemonic::NOP, 1, 2, AddressingMode::IMPLIED },
    { 0xe3, Mnemonic::ISB, 2, 8, AddressingMode::INDIRECT_X },
    { 0xe4, Mnemonic::CPX, 2, 3, AddressingMode::ZEROPAGE },
    { 0xe5, Mnemonic::SBC, 2, 3, AddressingMode::ZEROPAGE },
    { 0xe6, Mnemonic::INC, 2, 5, AddressingMode::ZEROPAGE },
    { 0xe7, Mnemonic::ISB, 2, 5, AddressingMode::ZEROPAGE },
    { 0xe8, Mnemonic::INX, 1, 2, AddressingMode::IMPLIED },
    { 0xe9, Mnemonic::SBC, 2, 2, AddressingMode::IMMEDIATE },
    { 0xea, Mnemonic::NOP, 1, 2, AddressingMode::IMPLIED },
    { 0xeb, Mnemonic::SBC, 2, 2, AddressingMode::IMMEDIATE },
    { 0xec, Mnemonic::CPX, 3, 4, AddressingMode::ABSOLUTE },
    { 0xed, Mnemonic::SBC, 3, 4, AddressingMode::ABSOLUTE },
    { 0xee, Mnemonic::INC, 3, 6, AddressingMode::ABSOLUTE },
    { 0xef, Mnemonic::ISB, 3, 6, AddressingMode::ABSOLUTE },
    // Conditional cycles: 2 is the base,
    // +1 if branch succeeds, +2 if there is a new page.
    { 0xf0, Mnemonic::BEQ, 2,  2, AddressingMode::IMPLIED, 1, 2 },
    // Conditional cycles: 5 is the base,
    // +1 if page crossed.
    { 0xf1, Mnemonic::SBC, 2,  5, AddressingMode::INDIRECT_Y, 0, 1 },
    { 0xf2 },
    { 0xf3, Mnemonic::ISB, 2, 8, AddressingMode::INDIRECT_Y },
    { 0xf4, Mnemonic::NOP, 2, 4, AddressingMode::ZEROPAGE },
    { 0xf5, Mnemonic::SBC, 2, 4, AddressingMode::ZEROPAGE_X },
    { 0xf6, Mnemonic::INC, 2, 6, AddressingMode::ZEROPAGE_X },
    { 0xf7, Mnemonic::ISB, 2, 6, AddressingMode::ZEROPAGE_X },
    { 0xf8, Mnemonic::SED, 1, 2, AddressingMode::IMPLIED },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0xf9, Mnemonic::SBC, 3,  4, AddressingMode::ABSOLUTE_Y, 0, 1 },
    { 0xfa, Mnemonic::NOP, 1, 2, AddressingMode::IMPLIED },
    { 0xfb, Mnemonic::ISB, 3, 7, AddressingMode::ABSOLUTE_Y },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0xfc, Mnemonic::NOP, 3,  4, AddressingMode::ABSOLUTE_X, 0, 1 },
    // Conditional cycles: 4 is the base,
    // +1 if page crossed.
    { 0xfd, Mnemonic::SBC, 3,  4, AddressingMode::ABSOLUTE_X, 0, 1 },
    { 0xfe, Mnemonic::INC, 3, 7, AddressingMode::ABSOLUTE_X },
    { 0xff, Mnemonic::ISB, 3, 7, AddressingMode::ABSOLUTE_X }
};

#endif
