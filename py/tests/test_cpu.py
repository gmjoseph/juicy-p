from clock import Clock
from cpu import CPU
from io_db import IO_DB


def test_cpu_nmi():
    """
    Ensures that the CPU properly handles an NMI by
    changing the program counter.
    """
    bus = IO_DB()
    clock = Clock()
    cpu = CPU(bus=bus, clock=clock, oam=None)

    # Setup the handler's address where the NMI handler
    # is stored, little endian.
    cpu.memory.write(0xbe, 0xFFFA)
    cpu.memory.write(0xba, 0xFFFB)
    # The handler is a NOP
    cpu.memory.write(0x1a, 0xbabe)

    start_pc = 0xcafe
    cpu.pc = start_pc

    start_p = 0x77
    cpu.p = start_p
    
    cpu.next(received_nmi=True)
    assert cpu.pc != start_pc
    # The NOP instruction was 1 byte.
    assert cpu.pc == 0xbabf

    # The start_pc and p should've been stored on the
    # stack when handling the NMI in expectation for the
    # inevitable RTI that should happen from the handler.
    cpu.sp, saved_p = cpu._stack.pop(cpu.memory, cpu.sp, 1)
    cpu.sp, saved_pc = cpu._stack.pop(cpu.memory, cpu.sp, 2)
    assert saved_p == start_p
    assert saved_pc == start_pc
