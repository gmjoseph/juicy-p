from enum import Enum
from enum import IntEnum


class AddressingMode(Enum):
    ABSOLUTE = 'ABSOLUTE'
    # "The address to be accessed by an instruction using X
    # register indexed absolute addressing is computed by taking
    # the 16 bit address from the instruction and added the
    # contents of the X register."
    # "For example if X contains $92 then an STA $2000,X instruction
    # will store the accumulator at $2092 (e.g. $2000 + $92).""
    ABSOLUTE_X = 'ABSOLUTE_X'
    # "The Y register indexed absolute addressing mode is the same
    # as the previous mode only with the contents of the Y register
    # added to the 16 bit address from the instruction."
    ABSOLUTE_Y = 'ABSOLUTE_Y'
    ACCUMULATOR = 'ACCUMULATOR'
    IMMEDIATE = 'IMMEDIATE'
    IMPLIED = 'IMPLIED'
    # "JMP is the only 6502 instruction to support indirection.
    # The instruction contains a 16 bit address which identifies
    # the location of the least significant byte of another 16
    # bit memory address which is the real target of the
    # instruction."
    # "For example if location $0120 contains $FC and location
    # $0121 contains $BA then the instruction JMP ($0120) will
    # cause the next instruction execution to occur at $BAFC
    # (e.g. the contents of $0120 and $0121)."
    INDIRECT = 'INDIRECT'
    # "Indexed indirect addressing is normally used in conjunction
    # with a table of address held on zero page. The address of
    # the table is taken from the instruction and the X register
    # added to it (with zero page wrap around) to give the location
    # of the least significant byte of the target address."
    # Or in simpler terms, it's just a pointer to another address
    # where we can get the pointer to the real data.
    INDIRECT_X = 'INDIRECT_X'
    # "Indirect indirect addressing is the most common indirection
    # mode used on the 6502. In instruction contains the zero page
    # location of the least significant byte of 16 bit address. The
    # Y register is dynamically added to this value to generated
    # the actual target address for operation."
    INDIRECT_Y = 'INDIRECT_Y'
    RELATIVE = 'RELATIVE'
    ZEROPAGE = 'ZEROPAGE'
    # "The address to be accessed by an instruction using indexed
    # zero page addressing is calculated by taking the 8 bit zero
    # page address from the instruction and adding the current
    # value of the X register to it. For example if the X register
    # contains $0F and the instruction LDA $80,X is executed then
    # the accumulator will be loaded from $008F
    # (e.g. $80 + $0F => $8F)."
    # "NB:
    # The address calculation wraps around if the sum of the base
    # address and the register exceed $FF. If we repeat the last
    # example but with $FF in the X register then the accumulator
    # will be loaded from $007F (e.g. $80 + $FF => $7F) and not
    # $017F."
    ZEROPAGE_X = 'ZEROPAGE_X'
    # "The address to be accessed by an instruction using indexed
    # zero page addressing is calculated by taking the 8 bit zero
    # page address from the instruction and adding the current
    # value of the Y register to it. This mode can only be used
    # with the LDX and STX instructions.
    ZEROPAGE_Y = 'ZEROPAGE_Y'


class PPUAddress(IntEnum):
    # PPU Registers are memory-mapped. In other words, they're
    # backed by locations in the CPU memory. That said, the PPU
    # also has its own memory.
    PPUCTRL_ADDRESS = 0x2000
    PPUMASK_ADDRESS = 0x2001
    PPUSTATUS_ADDRESS = 0x2002
    OAMADDR_ADDRESS = 0x2003
    OAMDATA_ADDRESS = 0x2004
    PPUSCROLL_ADDRESS = 0x2005
    PPUADDR_ADDRESS = 0x2006
    PPUDATA_ADDRESS = 0x2007
    # This one is technically a port on the CPU.
    OAMDMA_ADDRESS = 0x4014


PPUAddressValues = {e.value for e in list(PPUAddress)}


class PPURegister(Enum):
    PPUCTRL = 'PPUCTRL'
    PPUMASK = 'PPUMASK'
    PPUSTATUS = 'PPUSTATUS'
    OAMADDR = 'OAMADDR'
    OAMDATA = 'OAMDATA'
    PPUSCROLL = 'PPUSCROLL'
    PPUADDR = 'PPUADDR'
    PPUDATA = 'PPUDATA'
    OAMDMA = 'OAMDMA'


# TODO
# This won't account for address mirroring so don't use this
# if we need to handle that. OR just update this to a function
# that can handle mirroring.
PPUAddressToRegister = {
    PPUAddress.PPUCTRL_ADDRESS: PPURegister.PPUCTRL,
    PPUAddress.PPUMASK_ADDRESS: PPURegister.PPUMASK,
    PPUAddress.PPUSTATUS_ADDRESS: PPURegister.PPUSTATUS,
    PPUAddress.OAMADDR_ADDRESS: PPURegister.OAMADDR,
    PPUAddress.OAMDATA_ADDRESS: PPURegister.OAMDATA,
    PPUAddress.PPUSCROLL_ADDRESS: PPURegister.PPUSCROLL,
    PPUAddress.PPUADDR_ADDRESS: PPURegister.PPUADDR,
    PPUAddress.PPUDATA_ADDRESS: PPURegister.PPUDATA,
    PPUAddress.OAMDMA_ADDRESS: PPURegister.OAMDMA,
}


PPURegisterToAddress = {
    PPURegister.PPUCTRL: PPUAddress.PPUCTRL_ADDRESS,
    PPURegister.PPUMASK: PPUAddress.PPUMASK_ADDRESS,
    PPURegister.PPUSTATUS: PPUAddress.PPUSTATUS_ADDRESS,
    PPURegister.OAMADDR: PPUAddress.OAMADDR_ADDRESS,
    PPURegister.OAMDATA: PPUAddress.OAMDATA_ADDRESS,
    PPURegister.PPUSCROLL: PPUAddress.PPUSCROLL_ADDRESS,
    PPURegister.PPUADDR: PPUAddress.PPUADDR_ADDRESS,
    PPURegister.PPUDATA: PPUAddress.PPUDATA_ADDRESS,
    PPURegister.OAMDMA: PPUAddress.OAMDMA_ADDRESS,
}


class WriteMnemonic(Enum):
    STA = 'STA'
    STX = 'STX'
    STY = 'STY'


WriteMnemonicValues = {e.value for e in list(WriteMnemonic)}


class ReadMnemonic(Enum):
    BIT = 'BIT'
    LDA = 'LDA'
    LDX = 'LDX'
    LDY = 'LDY'


ReadMnemonicValues = {e.value for e in list(ReadMnemonic)}


# These mnemonics mutate the pc register directly by
# doing some kind of jump, return or branch. If the
# current mnemonic we're handling is in this set, we
# don't need to increment the program counter. An
# alternative would just be to increment the program
# counter ahead of each instruction but that also seems
# a bit weird and breaks subroutine calls because the
# return address we pushed isn't the right place to return
# to relative to the PC.
BranchingMnemonics = {
    'BRK',
    'JMP',
    'JSR',
    'RTI',
    # Because these can result in page crossing penalties
    # depending on where the PC is pointing to, we need
    # to handle the final PC address all together in the
    # instruction handler. This is kind of unfortunate
    # but oh well...
    'BEQ',
}

# TODO
# 341 PPU cycles per scanline. This might be NTSC specific.
# After that, we need to roll over and begin counting
# from 0 again. We need to take any number that put us
# above 341 and set it as the starting value. There will be
# 261 scanlines drawn per frame.
PPUCyclesPerScanline = 341
# 3 PPU cycles per CPU cycle.
PPUCyclesPerCPUCycle = 3
PPUMaxScanline = 261
PPUVBlankScanline = 241

PPUMemoryMap = {
    # Nicknamed 'left' for how it's displayed in a debug view
    # of 128x128 pixel sections next to pattern_table_1
    'pattern_table_0': (0x0000, 0x0FFF),
    # Nicknamed 'right'.
    'pattern_table_1': (0x1000, 0x1FFF),
    # https://wiki.nesdev.com/w/index.php/PPU_nametables
    # "A nametable is a 1024 byte area of memory used by the PPU
    # to lay out backgrounds. Each byte in the nametable controls
    # one 8x8 pixel character cell, and each nametable has 30 rows
    # of 32 tiles each, for 960 ($3C0) bytes; the rest is used by
    # each nametable's attribute table. With each tile being 8x8
    # pixels, this makes a total of 256x240 pixels in one map,
    # the same size as one full screen."
    # Nametables also have various mirroring configurations where
    # two (or more) nametables mirror two (or less) of the other
    # ones. E.g. nametables 0 and 1 could be mirrored by 2 and 3.
    # Top Left
    'nametable_0':     (0x2000, 0x23FF),
    # Top Right
    'nametable_1':     (0x2400, 0x27FF),
    # Bottom Left
    'nametable_2':     (0x2800, 0x2BFF),
    # Bottom Right
    'nametable_3':     (0x2C00, 0x2FFF),
    'nametable_mirrors': (0x3000, 0x3EFF),
    'nametable_range': (0x2000, 0x3EFF),
    'palette_ram_indexes': (0x3F00, 0x3F1F),
    'palette_ram_mirrors': (0x3F20, 0x3FFF),
    'ppu_memory_range': (0x0000, 0x4000),
}


NametableSize = 0x400


# TODO
# Add other modes
# https://wiki.nesdev.com/w/index.php/Mirroring#Memory_Mirroring
class NametableMirroring(Enum):
    HORIZONTAL = 'HORIZONTAL'
    VERTICAL = 'VERTICAL'
