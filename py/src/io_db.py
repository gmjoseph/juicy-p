# https://wiki.nesdev.com/w/index.php/PPU_programmer_reference#Ports
# "The PPU has an internal data bus that it uses for communication
# with the CPU. This bus, called _io_db in Visual 2C02 and PPUGenLatch
# in FCEUX,[1] behaves as an 8-bit dynamic latch due to capacitance
# of very long traces that run to various parts of the PPU. Writing
# any value to any PPU port, even to the nominally read-only PPUSTATUS,
# will fill this latch. Reading any readable port (PPUSTATUS, OAMDATA,
# or PPUDATA) also fills the latch with the bits read. Reading a
# nominally "write-only" register returns the latch's current value,
# as do the unused bits of PPUSTATUS. This value begins to decay after
# a frame or so, faster once the PPU has warmed up, and it is likely
# that values with alternating bit patterns (such as $55 or $AA) will
# decay faster.[2]

# TODO
# May want to register callbacks/handlers when we read/write data to
# this on both ends of the PPU and CPU
class IO_DB:

    def __init__(self) -> None:
        self._data: int = 0
        self._has_data: bool = False

    @property
    def data(self) -> int:
        # TODO
        # Throw if reading data when _has_data is false?
        existing = self._data
        self.has_data = False
        return existing

    @data.setter
    def data(self, what: int) -> None:
        if not isinstance(what, int):
            raise TypeError("Data setting needs an integer. Use the has_data to clear it.")
        self._data = what
        self._has_data = True

    @property
    def has_data(self) -> bool:
        return self._has_data

    @has_data.setter
    def has_data(self, what: bool) -> None:
        self._has_data = False
        self._data = 0

