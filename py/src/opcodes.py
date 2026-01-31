
# Undocumented operations were pulled from here:
# https://wiki.nesdev.com/w/index.php/Programming_with_unofficial_opcodes

# Matrix:
# From http://nesdev.com/6502_cpu.txt
# 6510 Instructions by Addressing Modes
# off- ++++++++++ Positive ++++++++++  ---------- Negative ----------
# set  00      20      40      60      80      a0      c0      e0      mode
#
# +00  BRK     JSR     RTI     RTS     NOP*    LDY     CPY     CPX     Impl/immed
# +01  ORA     AND     EOR     ADC     STA     LDA     CMP     SBC     (indir,x)
# +02   t       t       t       t      NOP*t   LDX     NOP*t   NOP*t     ? /immed
# +03  SLO*    RLA*    SRE*    RRA*    SAX*    LAX*    DCP*    ISB*    (indir,x)
# +04  NOP*    BIT     NOP*    NOP*    STY     LDY     CPY     CPX     Zeropage
# +05  ORA     AND     EOR     ADC     STA     LDA     CMP     SBC     Zeropage
# +06  ASL     ROL     LSR     ROR     STX     LDX     DEC     INC     Zeropage
# +07  SLO*    RLA*    SRE*    RRA*    SAX*    LAX*    DCP*    ISB*    Zeropage
#
# +08  PHP     PLP     PHA     PLA     DEY     TAY     INY     INX     Implied
# +09  ORA     AND     EOR     ADC     NOP*    LDA     CMP     SBC     Immediate
# +0a  ASL     ROL     LSR     ROR     TXA     TAX     DEX     NOP     Accu/impl
# +0b  ANC**   ANC**   ASR**   ARR**   ANE**   LXA**   SBX**   SBC*    Immediate
# +0c  NOP*    BIT     JMP     JMP ()  STY     LDY     CPY     CPX     Absolute
# +0d  ORA     AND     EOR     ADC     STA     LDA     CMP     SBC     Absolute
# +0e  ASL     ROL     LSR     ROR     STX     LDX     DEC     INC     Absolute
# +0f  SLO*    RLA*    SRE*    RRA*    SAX*    LAX*    DCP*    ISB*    Absolute
#
# +10  BPL     BMI     BVC     BVS     BCC     BCS     BNE     BEQ     Relative
# +11  ORA     AND     EOR     ADC     STA     LDA     CMP     SBC     (indir),y
# +12   t       t       t       t       t       t       t       t         ?
# +13  SLO*    RLA*    SRE*    RRA*    SHA**   LAX*    DCP*    ISB*    (indir),y
# +14  NOP*    NOP*    NOP*    NOP*    STY     LDY     NOP*    NOP*    Zeropage,x
# +15  ORA     AND     EOR     ADC     STA     LDA     CMP     SBC     Zeropage,x
# +16  ASL     ROL     LSR     ROR     STX  y) LDX  y) DEC     INC     Zeropage,x
# +17  SLO*    RLA*    SRE*    RRA*    SAX* y) LAX* y) DCP*    ISB*    Zeropage,x
#
# +18  CLC     SEC     CLI     SEI     TYA     CLV     CLD     SED     Implied
# +19  ORA     AND     EOR     ADC     STA     LDA     CMP     SBC     Absolute,y
# +1a  NOP*    NOP*    NOP*    NOP*    TXS     TSX     NOP*    NOP*    Implied
# +1b  SLO*    RLA*    SRE*    RRA*    SHS**   LAS**   DCP*    ISB*    Absolute,y
# +1c  NOP*    NOP*    NOP*    NOP*    SHY**   LDY     NOP*    NOP*    Absolute,x
# +1d  ORA     AND     EOR     ADC     STA     LDA     CMP     SBC     Absolute,x
# +1e  ASL     ROL     LSR     ROR     SHX**y) LDX  y) DEC     INC     Absolute,x
# +1f  SLO*    RLA*    SRE*    RRA*    SHA**y) LAX* y) DCP*    ISB*    Absolute,x
#
# ROR intruction is available on MC650x microprocessors after
# June, 1976.
#
# Legend:
#
# t       Jams the machine
# *t      Jams very rarely
# *       Undocumented command
# **      Unusual operation
# y)      indexed using Y instead of X
# ()      indirect instead of absolute

from constants import AddressingMode


# Some instructions will have a 'branch_cycles' property.
# These are additional cycles that are tacked on in case
# branch succeeds.
# Others will have a 'page_crossing_cycles' property. This
# is for when we incur a cycle penalty for a page crossing,
# which are also added to the CPU.
# Ram is divided into 256-byte pages, so when we go from
# one page (256-byte chunk) to another, we've crossed a
# page.
instructions = {
    0x0: {
        'opcode': 0x0,
        'mnemonic': 'BRK',
        'bytes': 1,
        'cycles': 7,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x1: {
        'opcode': 0x1,
        'mnemonic': 'ORA',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0x3: {
        'opcode': 0x3,
        'mnemonic': 'SLO',
        'bytes': 2,
        'cycles': 8,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0x4: {
        'opcode': 0x4,
        'mnemonic': 'NOP',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x5: {
        'opcode': 0x5,
        'mnemonic': 'ORA',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x6: {
        'opcode': 0x6,
        'mnemonic': 'ASL',
        'bytes': 2,
        'cycles': 5,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x7: {
        'opcode': 0x7,
        'mnemonic': 'SLO',
        'bytes': 2,
        'cycles': 5,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x8: {
        'opcode': 0x8,
        'mnemonic': 'PHP',
        'bytes': 1,
        'cycles': 3,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x9: {
        'opcode': 0x9,
        'mnemonic': 'ORA',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0xa: {
        'opcode': 0xa,
        'mnemonic': 'ASL',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.ACCUMULATOR,
    },
    0xc: {
        'opcode': 0xc,
        'mnemonic': 'NOP',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xd: {
        'opcode': 0xd,
        'mnemonic': 'ORA',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xe: {
        'opcode': 0xe,
        'mnemonic': 'ASL',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xf: {
        'opcode': 0xf,
        'mnemonic': 'SLO',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x10: {
        'opcode': 0x10,
        'mnemonic': 'BPL',
        'bytes': 2,
        # Conditional cycles: 2 is the base,
        # +1 if branch succeeds, +2 if there is a new page.
        'cycles': 2,
        # An additional cycle if the branch succeeds.
        'branch_cycles': 1,
        'page_crossing_cycles': 2,
        'addressing_mode': AddressingMode.RELATIVE,
    },
    0x11: {
        'opcode': 0x11,
        'mnemonic': 'ORA',
        'bytes': 2,
        # Conditional cycles: 5 is the base,
        # +1 if page crossed.
        'cycles': 5,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0x13: {
        'opcode': 0x13,
        'mnemonic': 'SLO',
        'bytes': 2,
        'cycles': 8,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0x14: {
        'opcode': 0x14,
        'mnemonic': 'NOP',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x15: {
        'opcode': 0x15,
        'mnemonic': 'ORA',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x16: {
        'opcode': 0x16,
        'mnemonic': 'ASL',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x17: {
        'opcode': 0x17,
        'mnemonic': 'SLO',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x18: {
        'opcode': 0x18,
        'mnemonic': 'CLC',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x19: {
        'opcode': 0x19,
        'mnemonic': 'ORA',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0x1a: {
        'opcode': 0x1a,
        'mnemonic': 'NOP',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
     0x1b: {
        'opcode': 0x1b,
        'mnemonic': 'SLO',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0x1c: {
        'opcode': 0x1c,
        'mnemonic': 'NOP',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x1d: {
        'opcode': 0x1d,
        'mnemonic': 'ORA',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x1e: {
        'opcode': 0x1e,
        'mnemonic': 'ASL',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x1f: {
        'opcode': 0x1f,
        'mnemonic': 'SLO',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x20: {
        'opcode': 0x20,
        'mnemonic': 'JSR',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x21: {
        'opcode': 0x21,
        'mnemonic': 'AND',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0x23: {
        'opcode': 0x23,
        'mnemonic': 'RLA',
        'bytes': 2,
        'cycles': 8,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0x24: {
        'opcode': 0x24,
        'mnemonic': 'BIT',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x25: {
        'opcode': 0x25,
        'mnemonic': 'AND',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x26: {
        'opcode': 0x26,
        'mnemonic': 'ROL',
        'bytes': 2,
        'cycles': 5,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x27: {
        'opcode': 0x27,
        'mnemonic': 'RLA',
        'bytes': 2,
        'cycles': 5,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x28: {
        'opcode': 0x28,
        'mnemonic': 'PLP',
        'bytes': 1,
        'cycles': 4,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x29: {
        'opcode': 0x29,
        'mnemonic': 'AND',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0x2a: {
        'opcode': 0x2a,
        'mnemonic': 'ROL',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.ACCUMULATOR,
    },
    0x2c: {
        'opcode': 0x2c,
        'mnemonic': 'BIT',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x2d: {
        'opcode': 0x2d,
        'mnemonic': 'AND',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x2e: {
        'opcode': 0x2e,
        'mnemonic': 'ROL',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x2f: {
        'opcode': 0x2f,
        'mnemonic': 'RLA',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x30: {
        'opcode': 0x30,
        'mnemonic': 'BMI',
        'bytes': 2,
        # Conditional cycles: 2 is the base,
        # +1 if branch succeeds, +2 if there is a new page.
        # So basically if we want realism with the branching
        # we need to account for page in / out.
        'cycles': 2,
        # An additional cycle if the branch succeeds.
        'branch_cycles': 1,
        'page_crossing_cycles': 2,
        'addressing_mode': AddressingMode.RELATIVE,
    },
    0x31: {
        'opcode': 0x31,
        'mnemonic': 'AND',
        'bytes': 2,
        # Conditional cycles: 5 is the base,
        # +1 if page crossed.
        'cycles': 5,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0x33: {
        'opcode': 0x33,
        'mnemonic': 'RLA',
        'bytes': 2,
        'cycles': 8,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0x34: {
        'opcode': 0x34,
        'mnemonic': 'NOP',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x35: {
        'opcode': 0x35,
        'mnemonic': 'AND',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x36: {
        'opcode': 0x36,
        'mnemonic': 'ROL',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x37: {
        'opcode': 0x37,
        'mnemonic': 'RLA',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x38: {
        'opcode': 0x38,
        'mnemonic': 'SEC',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x39: {
        'opcode': 0x39,
        'mnemonic': 'AND',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0x3a: {
        'opcode': 0x3a,
        'mnemonic': 'NOP',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x3b: {
        'opcode': 0x3b,
        'mnemonic': 'RLA',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0x3c: {
        'opcode': 0x3c,
        'mnemonic': 'NOP',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x3d: {
        'opcode': 0x3d,
        'mnemonic': 'AND',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x3e: {
        'opcode': 0x3e,
        'mnemonic': 'ROL',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x3f: {
        'opcode': 0x3f,
        'mnemonic': 'RLA',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x40: {
        'opcode': 0x40,
        'mnemonic': 'RTI',
        'bytes': 1,
        'cycles': 6,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x41: {
        'opcode': 0x41,
        'mnemonic': 'EOR',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0x43: {
        'opcode': 0x43,
        'mnemonic': 'SRE',
        'bytes': 2,
        'cycles': 8,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0x44: {
        'opcode': 0x44,
        'mnemonic': 'NOP',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x45: {
        'opcode': 0x45,
        'mnemonic': 'EOR',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x46: {
        'opcode': 0x46,
        'mnemonic': 'LSR',
        'bytes': 2,
        'cycles': 5,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x47: {
        'opcode': 0x47,
        'mnemonic': 'SRE',
        'bytes': 2,
        'cycles': 5,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x48: {
        'opcode': 0x48,
        'mnemonic': 'PHA',
        'bytes': 1,
        'cycles': 3,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x49: {
        'opcode': 0x49,
        'mnemonic': 'EOR',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0x4a: {
        'opcode': 0x4a,
        'mnemonic': 'LSR',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.ACCUMULATOR,
    },
    0x4c: {
        'opcode': 0x4c,
        'mnemonic': 'JMP',
        'bytes': 3,
        'cycles': 3,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x4d: {
        'opcode': 0x4d,
        'mnemonic': 'EOR',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x4e: {
        'opcode': 0x4e,
        'mnemonic': 'LSR',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x4f: {
        'opcode': 0x4f,
        'mnemonic': 'SRE',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x50: {
        'opcode': 0x50,
        'mnemonic': 'BVC',
        'bytes': 2,
        # Conditional cycles: 2 is the base,
        # +1 if branch succeeds, +2 if there is a new page.
        'cycles': 2,
        'branch_cycles': 1,
        'page_crossing_cycles': 2,
        'addressing_mode': AddressingMode.RELATIVE,
    },
    0x51: {
        'opcode': 0x51,
        'mnemonic': 'EOR',
        'bytes': 2,
        # Conditional cycles: 5 is the base,
        # +1 if page crossed.
        'cycles': 5,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0x53: {
        'opcode': 0x53,
        'mnemonic': 'SRE',
        'bytes': 2,
        'cycles': 8,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0x54: {
        'opcode': 0x54,
        'mnemonic': 'NOP',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x55: {
        'opcode': 0x55,
        'mnemonic': 'EOR',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x56: {
        'opcode': 0x56,
        'mnemonic': 'LSR',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x57: {
        'opcode': 0x57,
        'mnemonic': 'SRE',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x59: {
        'opcode': 0x59,
        'mnemonic': 'EOR',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0x5a: {
        'opcode': 0x5a,
        'mnemonic': 'NOP',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x5b: {
        'opcode': 0x5b,
        'mnemonic': 'SRE',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0x5c: {
        'opcode': 0x5c,
        'mnemonic': 'NOP',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x5d: {
        'opcode': 0x5d,
        'mnemonic': 'EOR',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x5e: {
        'opcode': 0x5e,
        'mnemonic': 'LSR',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x5f: {
        'opcode': 0x5f,
        'mnemonic': 'SRE',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x60: {
        'opcode': 0x60,
        'mnemonic': 'RTS',
        'bytes': 1,
        # TODO
        # Conditional cycles! 2 is the base,
        # +1 if branch succeeds, +2 if there is a new page.
        # So basically if we want realism with the branching
        # we need to account for page in / out.
        'cycles': 6,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x61: {
        'opcode': 0x61,
        'mnemonic': 'ADC',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0x63: {
        'opcode': 0x63,
        'mnemonic': 'RRA',
        'bytes': 2,
        'cycles': 8,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0x64: {
        'opcode': 0x64,
        'mnemonic': 'NOP',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x65: {
        'opcode': 0x65,
        'mnemonic': 'ADC',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x66: {
        'opcode': 0x66,
        'mnemonic': 'ROR',
        'bytes': 2,
        'cycles': 5,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x67: {
        'opcode': 0x67,
        'mnemonic': 'RRA',
        'bytes': 2,
        'cycles': 5,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x68: {
        'opcode': 0x68,
        'mnemonic': 'PLA',
        'bytes': 1,
        'cycles': 4,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x69: {
        'opcode': 0x69,
        'mnemonic': 'ADC',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0x6a: {
        'opcode': 0x6a,
        'mnemonic': 'ROR',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.ACCUMULATOR,
    },
    0x6c: {
        'opcode': 0x6c,
        'mnemonic': 'JMP',
        'bytes': 3,
        'cycles': 5,
        'addressing_mode': AddressingMode.INDIRECT,
    },
    0x6d: {
        'opcode': 0x6d,
        'mnemonic': 'ADC',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x6e: {
        'opcode': 0x6e,
        'mnemonic': 'ROR',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x6f: {
        'opcode': 0x6f,
        'mnemonic': 'RRA',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x70: {
        'opcode': 0x70,
        'mnemonic': 'BVS',
        'bytes': 2,
        # Conditional cycles: 2 is the base,
        # +1 if branch succeeds, +2 if there is a new page.
        # So basically if we want realism with the branching
        # we need to account for page in / out.
        'cycles': 2,
        # An additional cycle if the branch succeeds.
        'branch_cycles': 1,
        'page_crossing_cycles': 2,
        'addressing_mode': AddressingMode.RELATIVE,
    },
    0x71: {
        'opcode': 0x71,
        'mnemonic': 'ADC',
        'bytes': 2,
        # Conditional cycles: 5 is the base,
        # +1 if page crossed.
        'cycles': 5,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0x73: {
        'opcode': 0x73,
        'mnemonic': 'RRA',
        'bytes': 2,
        'cycles': 8,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0x74: {
        'opcode': 0x74,
        'mnemonic': 'NOP',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x75: {
        'opcode': 0x75,
        'mnemonic': 'ADC',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x76: {
        'opcode': 0x76,
        'mnemonic': 'ROR',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x77: {
        'opcode': 0x77,
        'mnemonic': 'RRA',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x78: {
        'opcode': 0x78,
        'mnemonic': 'SEI',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x79: {
        'opcode': 0x79,
        'mnemonic': 'ADC',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0x7a: {
        'opcode': 0x7a,
        'mnemonic': 'NOP',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x7b: {
        'opcode': 0x7b,
        'mnemonic': 'RRA',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0x7c: {
        'opcode': 0x7c,
        'mnemonic': 'NOP',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x7d: {
        'opcode': 0x7d,
        'mnemonic': 'ADC',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x7e: {
        'opcode': 0x7e,
        'mnemonic': 'ROR',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x7f: {
        'opcode': 0x7f,
        'mnemonic': 'RRA',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0x80: {
        'opcode': 0x80,
        'mnemonic': 'NOP',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0x81: {
        'opcode': 0x81,
        'mnemonic': 'STA',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0x82: {
        'opcode': 0x82,
        'mnemonic': 'NOP',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x83: {
        'opcode': 0x83,
        'mnemonic': 'SAX',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0x84: {
        'opcode': 0x84,
        'mnemonic': 'STY',
        'bytes': 2,
        'cycles': 3,
        # TODO
        # For testing, we can ensure that we're only writing from 0x0
        # up to 0xFF since that's the ZERO_PAGE adderssing mode.
        # For now this is actually going to let it write anywhere in
        # the address, so we might wanna check that.
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x85: {
        'opcode': 0x85,
        'mnemonic': 'STA',
        'bytes': 2,
        'cycles': 3,
        # TODO
        # For testing, we can ensure that we're only writing from 0x0
        # up to 0xFF since that's the ZERO_PAGE adderssing mode.
        # For now this is actually going to let it write anywhere in
        # the address, so we might wanna check that.
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x86: {
        'opcode': 0x86,
        'mnemonic': 'STX',
        'bytes': 2,
        'cycles': 3,
        # TODO
        # For testing, we can ensure that we're only writing from 0x0
        # up to 0xFF since that's the ZERO_PAGE adderssing mode.
        # For now this is actually going to let it write anywhere in
        # the address, so we might wanna check that.
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x87: {
        'opcode': 0x87,
        'mnemonic': 'SAX',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0x88: {
        'opcode': 0x88,
        'mnemonic': 'DEY',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x89: {
        'opcode': 0x89,
        'mnemonic': 'NOP',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x8a: {
        'opcode': 0x8a,
        'mnemonic': 'TXA',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.RELATIVE,
    },
    0x8c: {
        'opcode': 0x8c,
        'mnemonic': 'STY',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x8d: {
        'opcode': 0x8d,
        'mnemonic': 'STA',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x8e: {
        'opcode': 0x8e,
        'mnemonic': 'STX',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x8f: {
        'opcode': 0x8f,
        'mnemonic': 'SAX',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0x90: {
        'opcode': 0x90,
        'mnemonic': 'BCC',
        'bytes': 2,
        # Conditional cycles: 2 is the base,
        # +1 if branch succeeds, +2 if there is a new page.
        # So basically if we want realism with the branching
        # we need to account for page in / out.
        'cycles': 2,
        'branch_cycles': 1,
        'page_crossing_cycles': 2,
        'addressing_mode': AddressingMode.RELATIVE,
    },
    0x91: {
        'opcode': 0x91,
        'mnemonic': 'STA',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0x94: {
        'opcode': 0x94,
        'mnemonic': 'STY',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x95: {
        'opcode': 0x95,
        'mnemonic': 'STA',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0x96: {
        'opcode': 0x96,
        'mnemonic': 'STX',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_Y,
    },
    0x97: {
        'opcode': 0x97,
        'mnemonic': 'SAX',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_Y,
    },
    0x98: {
        'opcode': 0x98,
        'mnemonic': 'TYA',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.RELATIVE,
    },
    0x99: {
        'opcode': 0x99,
        'mnemonic': 'STA',
        'bytes': 3,
        'cycles': 5,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0x9a: {
        'opcode': 0x9a,
        'mnemonic': 'TXS',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0x9d: {
        'opcode': 0x9d,
        'mnemonic': 'STA',
        'bytes': 3,
        'cycles': 5,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0xa0: {
        'opcode': 0xa0,
        'mnemonic': 'LDY',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0xa1: {
        'opcode': 0xa1,
        'mnemonic': 'LDA',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0xa2: {
        'opcode': 0xa2,
        'mnemonic': 'LDX',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0xa3: {
        'opcode': 0xa3,
        'mnemonic': 'LAX',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0xa4: {
        'opcode': 0xa4,
        'mnemonic': 'LDY',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xa5: {
        'opcode': 0xa5,
        'mnemonic': 'LDA',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xa6: {
        'opcode': 0xa6,
        'mnemonic': 'LDX',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xa7: {
        'opcode': 0xa7,
        'mnemonic': 'LAX',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xa8: {
        'opcode': 0xa8,
        'mnemonic': 'TAY',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xa9: {
        'opcode': 0xa9,
        'mnemonic': 'LDA',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0xaa: {
        'opcode': 0xaa,
        'mnemonic': 'TAX',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xac: {
        'opcode': 0xac,
        'mnemonic': 'LDY',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xad: {
        'opcode': 0xad,
        'mnemonic': 'LDA',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xae: {
        'opcode': 0xae,
        'mnemonic': 'LDX',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xaf: {
        'opcode': 0xaf,
        'mnemonic': 'LAX',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xb0: {
        'opcode': 0xb0,
        'mnemonic': 'BCS',
        'bytes': 2,
        # Conditional cycles: 2 is the base,
        # +1 if branch succeeds, +2 if there is a new page.
        'cycles': 2,
        'branch_cycles': 1,
        'addressing_mode': AddressingMode.RELATIVE,
    },
    0xb1: {
        'opcode': 0xb1,
        'mnemonic': 'LDA',
        'bytes': 2,
        # Conditional cycles: 5 is the base,
        # +1 if page crossed.
        'cycles': 5,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0xb3: {
        'opcode': 0xb3,
        'mnemonic': 'LAX',
        'bytes': 2,
        'cycles': 5,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0xb4: {
        'opcode': 0xb4,
        'mnemonic': 'LDY',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0xb5: {
        'opcode': 0xb5,
        'mnemonic': 'LDA',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0xb6: {
        'opcode': 0xb6,
        'mnemonic': 'LDX',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_Y,
    },
    0xb7: {
        'opcode': 0xb7,
        'mnemonic': 'LAX',
        'bytes': 2,
        'cycles': 4,
        # Although the chart above says 'ZERO PAGE X' it should actually
        # be using the y register (i.e. ZERO PAGE Y).
        'addressing_mode': AddressingMode.ZEROPAGE_Y,
    },
    0xb8: {
        'opcode': 0xb8,
        'mnemonic': 'CLV',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xb9: {
        'opcode': 0xb9,
        'mnemonic': 'LDA',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0xba: {
        'opcode': 0xba,
        'mnemonic': 'TSX',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xbc: {
        'opcode': 0xbc,
        'mnemonic': 'LDY',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0xbd: {
        'opcode': 0xbd,
        'mnemonic': 'LDA',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0xbe: {
        'opcode': 0xbe,
        'mnemonic': 'LDX',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0xbf: {
        'opcode': 0xbf,
        'mnemonic': 'LAX',
        'bytes': 3,
        'cycles': 4,
        # Although the chart above says 'ABSOLUTE X' it should actually
        # be using the y register (i.e. ABSOLUTE Y).
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0xc0: {
        'opcode': 0xc0,
        'mnemonic': 'CPY',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0xc1: {
        'opcode': 0xc1,
        'mnemonic': 'CMP',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0xc2: {
        'opcode': 0xc2,
        'mnemonic': 'NOP',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xc3: {
        'opcode': 0xc3,
        'mnemonic': 'DCP',
        'bytes': 2,
        'cycles': 8,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0xc4: {
        'opcode': 0xc4,
        'mnemonic': 'CPY',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xc5: {
        'opcode': 0xc5,
        'mnemonic': 'CMP',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xc6: {
        'opcode': 0xc6,
        'mnemonic': 'DEC',
        'bytes': 2,
        'cycles': 5,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xc7: {
        'opcode': 0xc7,
        'mnemonic': 'DCP',
        'bytes': 2,
        'cycles': 5,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xc8: {
        'opcode': 0xc8,
        'mnemonic': 'INY',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xc9: {
        'opcode': 0xc9,
        'mnemonic': 'CMP',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0xca: {
        'opcode': 0xca,
        'mnemonic': 'DEX',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xcc: {
        'opcode': 0xcc,
        'mnemonic': 'CPY',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xcd: {
        'opcode': 0xcd,
        'mnemonic': 'CMP',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xce: {
        'opcode': 0xce,
        'mnemonic': 'DEC',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xcf: {
        'opcode': 0xcf,
        'mnemonic': 'DCP',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xd0: {
        'opcode': 0xd0,
        'mnemonic': 'BNE',
        'bytes': 2,
        # Conditional cycles: 2 is the base,
        # +1 if branch succeeds, +2 if there is a new page.
        'cycles': 2,
        # An additional cycle if the branch succeeds.
        'branch_cycles': 1,
        'page_crossing_cycles': 2,
        'addressing_mode': AddressingMode.RELATIVE,
    },
    0xd1: {
        'opcode': 0xd1,
        'mnemonic': 'CMP',
        'bytes': 2,
        # Conditional cycles: 5 is the base,
        # +1 if page crossed.
        'cycles': 5,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0xd3: {
        'opcode': 0xd3,
        'mnemonic': 'DCP',
        'bytes': 2,
        'cycles': 8,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0xd4: {
        'opcode': 0xd4,
        'mnemonic': 'NOP',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xd5: {
        'opcode': 0xd5,
        'mnemonic': 'CMP',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0xd6: {
        'opcode': 0xd6,
        'mnemonic': 'DEC',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0xd7: {
        'opcode': 0xd7,
        'mnemonic': 'DCP',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0xd8: {
        'opcode': 0xd8,
        'mnemonic': 'CLD',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xd9: {
        'opcode': 0xd9,
        'mnemonic': 'CMP',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0xda: {
        'opcode': 0xda,
        'mnemonic': 'NOP',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xdb: {
        'opcode': 0xdb,
        'mnemonic': 'DCP',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0xdc: {
        'opcode': 0xdc,
        'mnemonic': 'NOP',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0xdd: {
        'opcode': 0xdd,
        'mnemonic': 'CMP',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0xde: {
        'opcode': 0xde,
        'mnemonic': 'DEC',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0xdf: {
        'opcode': 0xdf,
        'mnemonic': 'DCP',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0xe0: {
        'opcode': 0xe0,
        'mnemonic': 'CPX',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0xe1: {
        'opcode': 0xe1,
        'mnemonic': 'SBC',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0xe2: {
        'opcode': 0xe2,
        'mnemonic': 'NOP',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xe3: {
        'opcode': 0xe3,
        'mnemonic': 'ISB',
        'bytes': 2,
        'cycles': 8,
        'addressing_mode': AddressingMode.INDIRECT_X,
    },
    0xe4: {
        'opcode': 0xe4,
        'mnemonic': 'CPX',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xe5: {
        'opcode': 0xe5,
        'mnemonic': 'SBC',
        'bytes': 2,
        'cycles': 3,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xe6: {
        'opcode': 0xe6,
        'mnemonic': 'INC',
        'bytes': 2,
        'cycles': 5,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xe7: {
        'opcode': 0xe7,
        'mnemonic': 'ISB',
        'bytes': 2,
        'cycles': 5,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xe8: {
        'opcode': 0xe8,
        'mnemonic': 'INX',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xe9: {
        'opcode': 0xe9,
        'mnemonic': 'SBC',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0xea: {
        'opcode': 0xea,
        'mnemonic': 'NOP',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xeb: {
        'opcode': 0xeb,
        'mnemonic': 'SBC',
        'bytes': 2,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMMEDIATE,
    },
    0xec: {
        'opcode': 0xec,
        'mnemonic': 'CPX',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xed: {
        'opcode': 0xed,
        'mnemonic': 'SBC',
        'bytes': 3,
        'cycles': 4,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xee: {
        'opcode': 0xee,
        'mnemonic': 'INC',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xef: {
        'opcode': 0xef,
        'mnemonic': 'ISB',
        'bytes': 3,
        'cycles': 6,
        'addressing_mode': AddressingMode.ABSOLUTE,
    },
    0xf0: {
        'opcode': 0xf0,
        'mnemonic': 'BEQ',
        'bytes': 2,
        # Conditional cycles: 2 is the base,
        # +1 if branch succeeds, +2 if there is a new page.
        'cycles': 2,
        'branch_cycles': 1,
        'page_crossing_cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xf1: {
        'opcode': 0xf1,
        'mnemonic': 'SBC',
        'bytes': 2,
        # Conditional cycles: 5 is the base,
        # +1 if page crossed.
        'cycles': 5,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0xf3: {
        'opcode': 0xf3,
        'mnemonic': 'ISB',
        'bytes': 2,
        'cycles': 8,
        'addressing_mode': AddressingMode.INDIRECT_Y,
    },
    0xf4: {
        'opcode': 0xf4,
        'mnemonic': 'NOP',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE,
    },
    0xf5: {
        'opcode': 0xf5,
        'mnemonic': 'SBC',
        'bytes': 2,
        'cycles': 4,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0xf6: {
        'opcode': 0xf6,
        'mnemonic': 'INC',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0xf7: {
        'opcode': 0xf7,
        'mnemonic': 'ISB',
        'bytes': 2,
        'cycles': 6,
        'addressing_mode': AddressingMode.ZEROPAGE_X,
    },
    0xf8: {
        'opcode': 0xf8,
        'mnemonic': 'SED',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xf9: {
        'opcode': 0xf9,
        'mnemonic': 'SBC',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0xfa: {
        'opcode': 0xfa,
        'mnemonic': 'NOP',
        'bytes': 1,
        'cycles': 2,
        'addressing_mode': AddressingMode.IMPLIED,
    },
    0xfb: {
        'opcode': 0xfb,
        'mnemonic': 'ISB',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_Y,
    },
    0xfc: {
        'opcode': 0xfc,
        'mnemonic': 'NOP',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0xfd: {
        'opcode': 0xfd,
        'mnemonic': 'SBC',
        'bytes': 3,
        # Conditional cycles: 4 is the base,
        # +1 if page crossed.
        'cycles': 4,
        'page_crossing_cycles': 1,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0xfe: {
        'opcode': 0xfe,
        'mnemonic': 'INC',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
    0xff: {
        'opcode': 0xff,
        'mnemonic': 'ISB',
        'bytes': 3,
        'cycles': 7,
        'addressing_mode': AddressingMode.ABSOLUTE_X,
    },
}
