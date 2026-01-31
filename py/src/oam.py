class OAM:
    """
    OAM: Object attribute memory. Holds 64 sprites of 1 byte
    each that were uploaded using OAMDMA or OAMDATA (more
    commonly the former than the latter)
    """

    def __init__(self):
        self._memory = bytearray(0x100)

    def sprite_at_index(self, index: int) -> bytearray:
        """
        Reads one sprite.
        """
        if index >= 0x40:
            raise Exception(f"Sprite index {index} out of range (0-63)")
        # TODO
        # Maybe return this data in a structured form rather than bytes?
        return self._memory[index * 0x4:(index + 1) * 0x4]

    def write(self, what: int, at_address: int) -> None:
        """
        Supports writing one byte of data at a time to an absolute
        address.
        what: a byte of data.
        address: an absolute address.
        """
        self._memory[at_address] = what

    def upload_data(self, what: bytearray) -> None:
        """
        Writes all sprites (256 bytes) at once.
        """
        if not isinstance(what, bytearray):
            raise TypeError("OAM Port requires bytearrays")
        self._memory[0:0x100] = what

    # TODO
    # https://wiki.nesdev.com/w/index.php/PPU_sprite_evaluation
    # This involves determining which sprites are in the frame
    # range and then drawing them.
    # For now i'll just grab the first 8 and draw them from
    # the top left.