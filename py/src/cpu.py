from typing import Callable
from typing import Optional

from cpu_operations import cpu_operations
from cpu_operations import NMI
from clock import Clock
from constants import BranchingMnemonics
from constants import WriteMnemonic
from cpu_memory import CPUMemory
from io_db import IO_DB
from oam import OAM
from opcodes import instructions
from stack import Stack


class CPU:

    @property
    def pc(self) -> int:
        return self._pc

    @pc.setter
    def pc(self, where: int) -> None:
        self._pc = where

    @property
    def sp(self) -> int:
        return self._sp

    @sp.setter
    def sp(self, where: int) -> None:
        self._sp = where

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, what: int) -> None:
        # Truncate any values that would overflow this 1-byte storage.
        self._x = what & 0xff

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, what: int) -> None:
        # Truncate any values that would overflow this 1-byte storage.
        self._y = what & 0xff

    @property
    def a(self) -> int:
        return self._a

    @a.setter
    def a(self, what: int) -> None:
        # TODO
        # Truncate any values that would overflow this 1-byte storage.
        self._a = what

    @property
    def p(self) -> int:
        return self._p

    @p.setter
    def p(self, what: int) -> None:
        self._p = what
    
    # Helpers to set the P register since there's a finite set of
    # operations we want to do on it.
    @property
    def _carry(self) -> int:
        """Is the carry flag set or not?"""
        return self.p & 0x01

    @property
    def _zero(self) -> int:
        """Is the zero flag set or not?"""
        return self.p & 0x02

    @property
    def _interrupt_disabled(self) -> int:
        """Is the interrupt_disabled flag set or not?"""
        return self.p & 0x04

    @property
    def _decimal(self) -> int:
        """Is the decimal flag set or not?"""
        return self.p & 0x08

    @property
    def _overflow(self) -> int:
        """Is the overflow flag set or not?"""
        return self.p & 0x40

    @property
    def _negative(self) -> int:
        """Is the negative flag set or not?"""
        return self.p & 0x80

    def __init__(
        self,
        bus: IO_DB,
        clock: Clock,
        oam: OAM,
    ) -> None:
        # Registers
        # Index X, 1 byte
        self._x = 0x0

        # Index Y, 1 byte
        self._y = 0x0

        # Accumulator
        self._a = 0x0

        # Program Counter, 2 bytes
        self._pc = 0x0

        # Stack Pointer, 1 byte
        self._sp = 0xfd

        # Status Register, ALU uses 6 bits but it's byte-wide.
        # This is equivalent to flags on x86:
        # 7  bit  0
        # ---- ----
        # NVss DIZC
        # |||| ||||
        # |||| |||+- Carry
        # |||| ||+-- Zero
        # |||| |+--- Interrupt Disable
        # |||| +---- Decimal
        # ||++------ No CPU effect, see: the B flag
        # |+-------- Overflow
        # +--------- Negative
        self._p = 0x24
        self._stack = Stack()

        self.memory = CPUMemory()
        self._bus = bus
        print(f"CPU init with bus: {id(bus)}")
        self._clock = clock
        print(f"CPU init with clock: {id(clock)}")
        self._oam = oam
        print(f"CPU init with oam: {id(oam)}")
        self._power_up()

    def _power_up(self) -> None:
        """
        Puts the CPU into the powerup state:
        https://wiki.nesdev.com/w/index.php/CPU_power_up_state
        """
        # Powerup needs to write to the 'private' member directly.
        self._clock._cpu_cycles = 0x7
        self.memory.write(0, 0x4015)
        self.memory.write(0, 0x4017)
        for address in range(0x4000, 0x4013):
            self.memory.write(0, address)

        # "Internal memory ($0000-$07FF) has unreliable startup state.
        # Some machines may have consistent RAM contents at power-on,
        # but others do not."
        # TODO
        # Randomize those contents on boot since some games use them
        # as part of randomness. We can use a seed for deterministic
        # randomness for debugging (final builds too maybe?)
        self.reset()
   
    def reset(self) -> None:
        # RESET (0xFFFC and 0xFFFD for low and high bytes respectively)
        # is the place to look for as the ROM entry point for on boot
        # i.e. where to set PC to to start fetching instructions.

        # TODO
        # Assuming that all the mappers just put the right data there
        # for now.
        # Use enums/constants for these values.
        # https://www.pagetable.com/?p=410
        # https://forums.nesdev.com/viewtopic.php?t=13560
        # http://users.telenet.be/kim1-6502/6502/proman.html#91
        # https://book.famicom.party/chapters/06-headersinterruptvectors.html
        # Little endian, of course.
        # Memory must be set first for this to work.
        start_low = self.memory.read_one(0xFFFC)
        start_high = self.memory.read_one(0xFFFD) << 8
        start_address = start_high + start_low
        self.pc = start_address


    def _mask_p(self, on: bool, mask: int) -> None:
        # Example for this and the rest of the setters for the flags:
        #
        # Mask of 0x1:
        #
        # 0 0 0 0 0 0 0 0
        # 0 0 0 0 0 0 0 1
        # --------------- |
        # 0 0 0 0 0 0 0 1
        #
        # XOR of mask with 0xff:
        # 0 0 0 0 0 0 0 1
        # 1 1 1 1 1 1 1 1 ^
        # ---------------
        # 1 1 1 1 1 1 1 0
        #
        # AND with the XOR of the mask:
        #
        # 0 0 0 0 0 0 0 1
        # 1 1 1 1 1 1 1 0 &
        # ---------------
        # 0 0 0 0 0 0 0 0
        if on:
            self.p |= mask
        else:
            self.p &= (mask ^ 0xff)

    def _set_carry(self, on: bool) -> None:
        self._mask_p(on, 0x1)

    def _set_zero(self, on: bool) -> None:
        self._mask_p(on, 0x2)

    def _set_interrupt_disabled(self, on: bool) -> None:
        self._mask_p(on, 0x4)

    def _set_decimal(self, on: bool) -> None:
        self._mask_p(on, 0x8)

    def _set_bit_4(self, on: bool) -> None:
        self._mask_p(on, 0x10)

    def _set_bit_5(self, on: bool) -> None:
        self._mask_p(on, 0x20)

    def _set_overflow(self, on: bool) -> None:
        self._mask_p(on, 0x40)

    def _set_negative(self, on: bool) -> None:
        self._mask_p(on, 0x80)

    def next(
        self,
        pre_instruction_callback: Optional[Callable] = None,
        post_instruction_callback: Optional[Callable] = None,
        received_nmi: Optional[bool] = None,
    ) -> None:
        """
        Handle the current instruction. May be pre-empted if an NMI
        was received.
        Advances the progarm counter (pc) to the next instruction.
        """
        if received_nmi:
            # Not returning early because it seems once the interrupt is
            # handled the CPU should then start executing from there
            # immediately.
            NMI(self)
            # self._debug('***NMI***')

        # Peek at the instruction. Account for cycles this takes if any?
        instruction_byte = self.memory.read_one(self.pc)
        if instruction_byte not in instructions:
            raise Exception(f"Unhandled opcode {hex(instruction_byte)} at {hex(self.pc)}")
        instruction = instructions[instruction_byte]
        instruction_bytes = self.memory.read(self.pc, amount = instruction['bytes'])

        if pre_instruction_callback:            
            pre_instruction_callback(instruction, instruction_bytes)

        # If there is bus_data the instruction that cares about it handles
        # it internally. See op_BIT or op_LDA for example.
        # TODO
        # Test that the instructions that should handle bus_data have handled
        # it after handler() executes. For example. assert pre handler we have
        # bus data, assert post handler that we don't.
        mnemonic = instruction['mnemonic']
        handler = cpu_operations[mnemonic]
        handler(self, instruction, instruction_bytes)

        # By now if an instruction resulted in a bus_data update (it happens
        # in operations.py) then it should be there in time for the PPU to
        # handle it in the callback.
        if post_instruction_callback:
            post_instruction_callback(instruction, instruction_bytes)

        if mnemonic not in BranchingMnemonics:
            # This must be done before we handle the instruction because
            # some of them may cause displacement which would also result
            # in a page crossing for certain program counters.
            self._pc += instruction['bytes']

        self._clock.cpu_cycles += instruction['cycles']
        # self._debug(mnemonic)

    def upload_oamdma_data(self, high_byte: int) -> None:
        """
        When we get an action to upload OAMDMA data (it's a write to 0x4014)
        we need to copy 256 bytes to PPU memory. We know which memory to
        copy because the high byte of the CPU memory was loaded into some
        register. E.g. LDA 0x40, STA 0x4014 would use 0x40 as the high
        byte.
        https://wiki.nesdev.com/w/index.php/PPU_programmer_reference#OAMDMA
        """
        address = high_byte << 8
        data = self.memory.read(address, 0x100)
        self._oam.upload_data(data)
        # FIXME
        # Technically the CPU is supposed to be paused for 512 cycles
        # 256 for each read/write, and then 1 dummy cycle, and then
        # 1 more cycle if we're on an odd number. Not sure if it's
        # important to mimic this for emulation.

    def _debug(self, mnemonic: Optional[str] = None) -> None:
        """Temporarily recording debug data during runs..."""
        # It's a queue of mnemonics we've executed that holds max 300.
        if not hasattr(self, '_executed_mnemonics'):
            setattr(self, '_executed_mnemonics', [])
        self._executed_mnemonics.insert(
            0,
            (hex(self.pc), mnemonic)
        )
        if len(self._executed_mnemonics) > 300:
            self._executed_mnemonics.pop(-1)

        if not hasattr(self, '_subroutines'):
            setattr(self, '_subroutines', [])
        if mnemonic in {'JSR', 'RTS'}:
            self._subroutines.append(mnemonic)
