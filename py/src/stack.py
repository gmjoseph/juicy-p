from typing import Tuple

from cpu_memory import CPUMemory


_STACK_BASE = 0x100

class Stack():
    """
    Defines a stack that is compatible with the following
    requirements:

    "The processor supports a 256 byte stack located between
    $0100 and $01FF. The stack pointer is an 8 bit register
    and holds the low 8 bits of the next free location on the
    stack. The location of the stack is fixed and cannot be
    moved."

    So basically we need to always add 0x100 to our stack pointer
    value to retrieve and put things in the right location.
    """
    def push(self, memory: CPUMemory, sp: int, value: int) -> int:
        if value <= 0xff:
            memory.write(value, _STACK_BASE + sp)
            # We pushed a byte.
            sp -=1
        elif value > 0xff and value <= 0xffff:
            # High value first.
            memory.write((value >> 8), _STACK_BASE + sp)
            sp -=1
            # Low value next
            memory.write((value & 0xff), _STACK_BASE + sp)
            sp -=1
        elif value > 0xffff:
            raise Exception(f"Can't push more than 2 bytes to the stack, attempted: {value}")

        return sp

    def pop(self, memory: CPUMemory, sp: int, size: int) -> Tuple[int, int]:
        """
        Size is the size in bytes of the data we're popping.
        This value has to be right to control the stack pointer.

        Stack pointer must be incremented before each memory
        read.
        """
        # TODO
        # We're only dealing with uint8 or uint16 so this should be ok
        # however, it's not the best. It'd be nicer to just read values
        # directly from the bytearray and convert them.
        value = None
        if size == 1:
            sp += 1
            value = memory.read_one(_STACK_BASE + sp)
        elif size == 2:
            sp += 1
            low = memory.read_one(_STACK_BASE + sp)
            sp += 1
            high = memory.read_one(_STACK_BASE + sp)
            value = high
            value <<= 0x8
            value += low
        return sp, value
