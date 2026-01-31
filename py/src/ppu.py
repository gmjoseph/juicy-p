from typing import Tuple

from ppu_operations import ppu_operations
from clock import Clock
from constants import PPUCyclesPerScanline
from constants import PPUMaxScanline
from constants import PPURegister
from constants import PPUVBlankScanline
from io_db import IO_DB
from oam import OAM
from ppu_memory import PPUMemory
from ppu_utils import colour_for_pixel
from ppu_utils import handler_for_read
from ppu_utils import handler_for_write
from ppu_utils import render_sprites
from renderer import Renderer


class PPU:

    ###########################################################################
    # PPUCTRL
    ###########################################################################

    @property
    def PPUCTRL(self) -> int:
        # TODO:
        # "Another way of seeing the explanation above is that when
        # you reach the end of a nametable, you must switch to the
        # next one, hence, changing the nametable address.
        # After power/reset, writes to this register are ignored for
        # about 30,000 cycles.
        # If the PPU is currently in vertical blank, and the PPUSTATUS
        # ($2002) vblank flag is still set (1), changing the NMI flag
        # in bit 7 of $2000 from 0 to 1 will immediately generate an NMI.
        # This can result in graphical errors (most likely a misplaced
        # scroll) if the NMI routine is executed too late in the blanking
        # period to finish on time. To avoid this problem it is prudent
        # to read $2002 immediately before writing $2000 to clear the
        # vblank flag.
        # For more explanation of sprite size, see: Sprite size "
        return self._PPUCTRL

    @PPUCTRL.setter
    def PPUCTRL(self, what: int) -> int:
        self._PPUCTRL = what

    @property
    def _base_nametable_address(self) -> int:
        index = self.PPUCTRL & 0x3
        bases = [0x2000, 0x2400, 0x2800, 0x2c00]
        return bases[index]

    @property
    def _increment_mode(self) -> int:
        # VRAM address increment per CPU read/write of PPUDATA
        # (0: add 1, going across; 1: add 32, going down)
        # TODO
        # Not sure what this means (add 32 going down) for when the bit is
        # set. I guess it depends on what down and across mean in this
        # context for the VRAM?
        # I think it may just mean the added amount because incrementing by
        # 32 gets us to the next row in memory? (0x20?)
        increment_mode = self.PPUCTRL & 0x4
        return increment_mode

    @property
    def _sprite_pattern_table_address(self) -> int:
        # Sprite pattern table address for 8x8 sprites
        # (0: $0000; 1: $1000; ignored in 8x16 mode)
        pattern = self.PPUCTRL & 0x8
        return pattern << 4

    @property
    def _background_pattern_table_address(self) -> int:
        # Background pattern table address (0: $0000; 1: $1000)
        pattern = self.PPUCTRL & 0x10
        return pattern << 4

    @property
    def _sprite_size(self) -> Tuple[int, int]:
        # Sprite size (0: 8x8 pixels; 1: 8x16 pixels)
        size_selector = self.PPUCTRL & 0x20
        if size_selector:
            return (8, 16)
        return (8, 8)

    @property
    def _slave_master_select(self) -> int:
        # PPU master/slave select
        # (0: read backdrop from EXT pins; 1: output color on EXT pins)
        return self.PPUCTRL & 0x40

    # @property
    # def _generate_nmi(self) -> int:
    #     # Generate an NMI at the start of the
    #     # vertical blanking interval (0: off; 1: on)
    #     return bool(self.PPUCTRL & 0x80)

    @property
    def generated_nmi(self) -> bool:
        # TODO
        # A fair amount of time is spent here.
        # Only returns true if the current cycle is the beginning
        # of VBLANK and _generate_nmi is true.
        first_cycle = self._clock.ppu_cycles == 1
        correct_scanline = self.scanline == PPUVBlankScanline
        # Generate an NMI at the start of the
        # vertical blanking interval (0: off; 1: on)
        generate_nmi = self.PPUCTRL & 0x80
        return generate_nmi and correct_scanline and first_cycle

    ###########################################################################
    # PPUMASK
    ###########################################################################

    @property
    def PPUMASK(self) -> int:
        return self._PPUMASK

    @PPUMASK.setter
    def PPUMASK(self, what: int) -> int:
        self._PPUMASK = what

    ###########################################################################
    # PPSTATUS
    ###########################################################################

    @property
    def PPUSTATUS(self) -> int:
        """
        "This register reflects the state of various functions inside the
        PPU. It is often used for determining timing. To determine when
        the PPU has reached a given pixel of the screen, put an opaque
        (non-transparent) pixel of sprite 0 there."
        Whenever this is read we have to clear bit 7 
        """
        # TODO
        # There are other conditions around this register.
        # Clear the V bit and update the value.
        previous = self._PPUSTATUS
        self._PPUSTATUS = self._PPUSTATUS & 0x7f
        return previous

    @PPUSTATUS.setter
    def PPUSTATUS(self, what: int) -> None:
        self._PPUSTATUS = what

    ###########################################################################
    # OAMADDR
    ###########################################################################

    @property
    def OAMADDR(self) -> int:
        # "The value of OAMADDR when sprite evaluation starts
        # at tick 65 of the visible scanlines will determine
        # where in OAM sprite evaluation starts"
        return self._OAMADDR

    @OAMADDR.setter
    def OAMADDR(self, what: int) -> None:
        # From the wiki: most games write 0 here and use
        # OAMDMA.
        self._OAMADDR = what

    def _increment_OAMADDR(self) -> None:
        self._OAMADDR += 1

    ###########################################################################
    # PPUSCROLL
    ###########################################################################

    @property
    def PPUSCROLL(self) -> int:
        """
        This register, like the others, is memory mapped. We'll update it
        by writing to 0x2006. Valid addresses for the PPU can be between
        0x0000 and 0x3ffff. So once we write an address here, we're then
        going to be using it to deal with the PPU-scoped memory (which
        is separate from the CPU's).
        """
        # FIXME
        # "Changes made to the vertical scroll during rendering will only take
        # effect on the next frame."
        # Basically this needs to be stateful and we need to know if it was
        # changed mid-frame.
        return self._PPUSCROLL

    @PPUSCROLL.setter
    def PPUSCROLL(self, what: int) -> None:
        # FIXME
        # Possibly validate what's being put in here?
        # "Horizontal offsets range from 0 to 255. "Normal" vertical offsets
        # range from 0 to 239, while values of 240 to 255 are treated as -16
        # through -1 in a way, but tile data is incorrectly fetched from the
        # attribute table."
        if self._PPUSCROLL_pushes == 0:
            # High byte is pushed first.
            self._PPUSCROLL = what << 8
            self._PPUSCROLL_pushes += 1
        elif self._PPUSCROLL_pushes == 1:
            # Low byte is pushed after high byte.
            self._PPUSCROLL += what
            self._PPUSCROLL_pushes = 0
        else:
            raise Exception(f"PPUSCROLL is in a weird state: {self._PPUSCROLL_pushes}, {self._PPUSCROLL}")
        if self._PPUSCROLL > 0xffff:
            raise Exception(f"Writing more than uint16 to memory for PPUSCROLL: {what}")

    @property
    def scroll_x(self) -> int:
        # FIXME
        # This might not be the high byte?
        return self._PPUSCROLL >> 8

    @property
    def scroll_y(self) -> int:
        # FIXME
        # This might not be the low byte
        return self._PPUSCROLL & 0xff

    ###########################################################################
    # PPUADDR
    ###########################################################################

    @property
    def PPUADDR(self) -> int:
        """
        This register, like the others, is memory mapped. We'll update it
        by writing to 0x2006. Valid addresses for the PPU can be between
        0x0000 and 0x3ffff. So once we write an address here, we're then
        going to be using it to deal with the PPU-scoped memory (which
        is separate from the CPU's).
        """
        return self._PPUADDR

    @PPUADDR.setter
    def PPUADDR(self, what: int) -> None:
        if self._PPUADDR_pushes == 0:
            # High byte is pushed first.
            self._PPUADDR = what << 8
            self._PPUADDR_pushes += 1
        elif self._PPUADDR_pushes == 1:
            # Low byte is pushed after high byte.
            self._PPUADDR += what
            self._PPUADDR_pushes = 0
            # FIXME
            # "Valid addresses are $0000-$3FFF; higher addresses will be
            # mirrored down."
            # So mirror down at write time possibly? to avoid doing it for
            # every uncached memory fetch?
        else:
            raise Exception(f"PPUADDR is in a weird state: {self._PPUADDR_pushes}, {self._PPUADDR}")
        if self._PPUADDR > 0xffff:
            raise Exception(f"Writing more than uint16 to memory for PPUADDR: {what}")

    def _increment_PPUADDR(self) -> None:
        """
        The PPUADDR setter is all about handling low and high byte pushes.
        If we just use the setter, we'll be mimicking that pushing behaviour
        when all we want to do is add some amount to the existing address.
        """
        adder = 1 if self._increment_mode == 0 else 32
        # Notice that we're not using the setter/getter.
        self._PPUADDR += adder

    def __init__(
        self,
        bus: IO_DB,
        clock: Clock,
        oam: OAM,
    ) -> None:
        # OAMDATA, PPUDATA, and OAMDMA are missing because they're just proxies
        # for memory read/write at specific places.

        self._PPUCTRL = 0x0
        self._PPUMASK = 0x0
        self._PPUSTATUS = 0x0
        self._OAMADDR = 0x0
        self._PPUSCROLL = 0x0
        self._PPUADDR = 0x0

        # TODO
        # Determine how many of these registers are needed.
        # # https://wiki.nesdev.com/w/index.php/PPU_scrolling#PPU_internal_registers
        # # Current VRAM address. This is independent of PPUADDR and is
        # # used strictly for rendering pixels, not for CPU read/write to
        # # PPU memory.
        # self._v = 0x0

        # Fine X scroll, it's the x location of the pixel.
        self._x = 0x0

        # Fine Y scroll, it's the y location of the pixel.
        self._y = 0x0

        # # First or second write toggle.
        # self._w = 0x0

        # Writing the the _PPUADDR register is done by STA'ing to
        # the PPUADDR_ADDRESS (0x2006). It needs to be done twice,
        # first the high byte then the low byte. For this reason we
        # need to track which one has been pushed.
        self._PPUADDR_pushes = 0

        # Same as _PPUADDR pushes.
        self._PPUSCROLL_pushes = 0

        self.scanline = 0

        self._frames = 0

        self._pixels = bytearray(256 * 240)

        self._bus = bus
        print(f"PPU init with bus: {id(bus)}")
        self._clock = clock
        print(f"PPU init with clock: {id(clock)}")
        self._oam = oam
        # The OAM is shared between the CPU and PPU directly.
        print(f"PPU init with oam: {id(oam)}")
        self._power_up()
        self.memory = PPUMemory()
        self.renderer = Renderer()
        # For rendering the background, this stores the nametable
        # and attribute table bytes every 8 pixels so that we don't
        # need to fetch it each time. This is also more realistic
        # in terms of per-cycle accuracy since the byte is only
        # fetched every 8 cycles according to the NTSC timing diagram.
        self.background_state = {}

    @property
    def rendering(self) -> bool:
        """
        Rendering happens for now between scanline 0 and 241 and cycles 1
        and 256. This _MAY_ be accurate in terms of outputing pixels to
        the screen, but it isn't in terms of computing the next frame's
        pixels up front.
        """
        # FIXME
        # Copied and pasted this from maybe compute pixel.
        if self.scanline >= 240:
            # TODO
            # This is incomplete.
            # No pixel draws for these non-visible scanlines except
            # at 261 which is readying for the next frame.
            return False

        if  1 > self._clock.ppu_cycles or self._clock.ppu_cycles > 256:
            # No generating pixels during these PPU cycles. It only needs
            # to generate 256 pixels across so it makes no sense to run
            # outside of that point.
            # TODO
            # That's not quite accurate since there is loading and priming
            # certain data for the next scanline ahead of time.
            return False

        return True

    def _power_up(self) -> None:
        """
        Puts the PPU into the powerup state:
        https://wiki.nesdev.com/w/index.php/PPU_power_up_state
        """
        pass

    def _receive_bus_data(self) -> int:
        # We should only ever call this if we expect to receive data from the CPU
        # over the bus.
        if not self._bus.has_data:
            raise Exception(f"Writing to register expected bus data.")
        return self._bus.data

    def before_cpu(self, instruction: dict, instruction_bytes: bytearray) -> None:
        """
        The CPU shares its instructions with the PPU in case it needs to
        take action on them. The PPU is subordinate in this relationship
        because the CPU clearly does most of the heavy lifting. That said,
        the PPU does need to sometimes do some internal state updating
        before the CPU executes.
        """
        register, handler = handler_for_read(instruction, instruction_bytes)
        if not handler:
            return
        # Reads fill bus data for the CPU.
        handler(self)

    def after_cpu(self, instruction: dict, instruction_bytes) -> None:
        # We need to handle write ops in post_next because it gives a chance
        # for the CPU to put it into the shared bus. If we try and access
        # the data in the bus before the CPU got a chance to put it in there
        # we'll have no data.
        register, handler = handler_for_write(instruction, instruction_bytes)
        if not handler:
            return
        data = self._receive_bus_data()
        handler(self, data)

    def next(self) -> None:
        for _ in range(self._clock.ppu_cycles_next):
            self._cycle()
            self._post_cycle()

    def _cycle(self) -> None:
        """
        Called once for each PPU cycle after the CPU executes. Knowing how
        many cycles the CPU did lets us know how many cycles to perform
        here since there is a 3:1 ratio of PPU cycles to CPU cycles.
        This means that PPU calls are interleaved with CPU calls, which
        is probably fine since the PPU will be doing pixel, rather than
        instruction, processing.
        The goal at each cycle is to do some part of this:
        https://wiki.nesdev.com/w/index.php/PPU_rendering#Line-by-line_timing
        """
        # TODO
        # This is going to get very ugly as we stuff in all sorts of
        # conditions here. This may need to be pieced out.
        self._update_state()
        self._maybe_compute_pixel()

    def _update_state(self) -> None:
        """
        Various states crammed together in one function because calling
        them in a row is costly.
        """
        # self._maybe_toggle_vblank()
        if self._clock.ppu_cycles == 1:
            # Toggle VBLANK on first cycle of scanline 241
            if self.scanline == PPUVBlankScanline:
                self.PPUSTATUS |= 0x80

            # Toggle VBLANK off first cycle of scanline 261
            elif self.scanline == PPUMaxScanline:
                self.PPUSTATUS &= 0x7f

        # self._maybe_zero_oamaddr()
        elif 257 <= self._clock.ppu_cycles <= 320:
            self._OAMADDR = 0

    # def _maybe_toggle_vblank(self) -> None:
    #     # Only do this on cycle 1 of the right scanlines.
    #     if self._clock.ppu_cycles != 1:
    #         return

    #     # Toggle VBLANK on first cycle of scanline 241
    #     if self.scanline == PPUVBlankScanline:
    #         self.PPUSTATUS |= 0x80

    #     # Toggle VBLANK off first cycle of scanline 261
    #     if self.scanline == PPUMaxScanline:
    #         self.PPUSTATUS &= 0x7f

    # def _maybe_zero_oamaddr(self) -> None:
    #     # "OAMADDR is set to 0 during each of ticks 257-320 (the
    #     # sprite tile loading interval) of the pre-render and visible
    #     # scanlines."
    #     if 257 <= self._clock.ppu_cycles <= 320:
    #         self._OAMADDR = 0

    def _maybe_compute_pixel(self) -> None:
        if self.scanline >= 240:
            # TODO
            # This is incomplete.
            # No pixel draws for these non-visible scanlines except
            # at 261 which is readying for the next frame.
            return

        if  1 > self._clock.ppu_cycles or self._clock.ppu_cycles > 256:
            # No generating pixels during these PPU cycles. It only needs
            # to generate 256 pixels across so it makes no sense to run
            # outside of that point.
            # TODO
            # That's not quite accurate since there is loading and priming
            # certain data for the next scanline ahead of time.
            return

        colour = colour_for_pixel(self, self._x, self._y)
        # Index into the pixel buffer since it's flattened
        # and not an x/y grid.
        pixel_index = self._x + self._y * 256
        self._pixels[pixel_index] = colour

        # We need to increment x here because it's tracking pixels. If we
        # do it in _post_cycle it'll increment even if we never moved the
        # pixel location.
        self._x += 1

    def _post_cycle(self) -> None:
        self._clock.ppu_cycles += 1
        if self._clock.ppu_cycles == PPUCyclesPerScanline:
            # TODO
            # 341 PPU cycles per scanline. This might be NTSC specific.
            # After that, we need to roll over and begin counting
            # from 0 again. We need to take any number that put us
            # above 341 and set it as the starting value.
            self._clock.ppu_cycles = 0
            # Reset the horizontal scroll because we got to the end of
            # the scanline.
            self._x = 0
            self.scanline += 1

            # TODO
            # Vertical register is computed at cycle 256, not at 341.
            # (See NTSC timing diagram, this obviously has implications
            # for badly behaved programs).
            self._y += 1

        # One frame.
        if self.scanline > PPUMaxScanline:
            # FIXME
            # As the comment in the function says, this is not how the CPU works
            # at all. However, it'll be good enough to test sprite rendering
            # frame by frame.
            render_sprites(self)
            # Reset the number of scanlines drawn, as well as our x and y offsets
            # for the current pixel being drawn.
            # Flush the pixel buffer to disk for now rather than output to screen.
            self.scanline = 0
            self._x = 0
            self._y = 0
            self._frames += 1
            self.renderer.render(self._pixels)
