from pathlib import Path

from cartridge import Cartridge
from clock import Clock
from cpu import CPU
from io_db import IO_DB
from oam import OAM
from ppu import PPU


class NES:
    def __init__(self, filepath: Path) -> None:
        bus = IO_DB()
        oam = OAM()

        self.clock = Clock()
        self.cartridge = Cartridge(filepath)
        self.cpu = CPU(bus=bus, clock=self.clock, oam=oam)
        self.cartridge.store_rom(self.cpu.memory)
        self.cpu.reset()

        self.ppu = PPU(bus=bus, clock=self.clock, oam=oam)
        self.ppu.memory.nametable_mirroring = self.cartridge._header.nametable_mirroring
        self.cartridge.store_palette(self.ppu.memory)

    def run(self) -> None:
        # In most cases the CPU can handle an instruction on its own. Some,
        # however, also need PPU involvement (for updating its internal
        # registers for example, like PPUSTATUS based on the upcoming
        # instruction.
        # For that reason we need to possibly speak to the PPU from here,
        # and the PPU may need to communicate back to the CPU.
        # The ordering of this ma need to be CPU first then PPU or PPU
        # then CPU. In either case we tap into the lifecycle of the CPU's
        # instruction handling to coordinate between the two chips.
        # We can maybe think of this as the implementation of the 'latch'.
        # (See _get_bus_data in CPU for details on the latch).
        #
        # However this doesn't really handle receiving data from the ppu
        # so...

        # TODO
        # This may all need to be driven by a clock input object that
        # triggers the PPU or CPU because the PPU has very specific per-cycle
        # behaviours and is more granular than CPU operation in that
        # sense. Simply incrementing the PPU's cycles by 3 for each CPU
        # instruction may not make sense given the state changes from
        # cycle to cycle in the PPU.

        self.cpu.next(
            pre_instruction_callback=self.ppu.before_cpu,
            post_instruction_callback=self.ppu.after_cpu,
            received_nmi=self.ppu.generated_nmi,
        )

        self.clock.next()

        # Run the PPU for some number of its own cycles to
        # do pixel processing
        self.ppu.next()
