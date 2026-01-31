from constants import PPUCyclesPerCPUCycle


class Clock:
    # Tracks the cycles for the CPU and PPU
    def __init__(self) -> None:
        # At boot cpu cycles are 0x7.
        self.cpu_cycles = 0x7
        self._previous_cpu_cycles = 0x7

        self.ppu_cycles = 0x0
        self._previous_ppu_cycles = 0x0
        # Let's the PPU know how many cycles to execute for as a result of
        # what the CPU did cycle-wise.
        self.ppu_cycles_next = 0x0

    def next(self) -> None:
        """
        Stores deltas of cycles and computes next cycle amount for PPU.
        """
        delta = self.cpu_cycles - self._previous_cpu_cycles
        self.ppu_cycles_next = delta * PPUCyclesPerCPUCycle

        self._previous_cpu_cycles = self.cpu_cycles
        self._previous_ppu_cycles = self.ppu_cycles
        # Compute the number of cpu cycles to run at the start of each
        # iteration.
