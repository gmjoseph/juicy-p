#include "Constants.h"
#include "IO_DB.h"
#include "PPU.h"
#include "PPUUtils.h"

PPU::PPU(
    IO_DB& bus,
    Clock& clock,
    OAM& oam
) : bus(bus), clock(clock), oam(oam) {
    // Provide a way for the bus to write into the PPU.
    bus.ppu = this;
    clock.ppu = this;
    printf("PPU init with bus: %p clock: %p, oam: %p\n", &bus, &clock, &oam);
}

void
PPU::set_PPUADDR(uint8_t what) {
    if (_PPUADDR_pushes == 0) {
        // High byte is pushed first.
        _PPUADDR = what << 8;
        _PPUADDR_pushes += 1;
    } else if (_PPUADDR_pushes == 1) {
        // Low byte is pushed after high byte.
        _PPUADDR += what;
        _PPUADDR_pushes = 0;
        // FIXME
        // "Valid addresses are $0000-$3FFF; higher addresses will be
        // mirrored down."
        // So mirror down at write time possibly? to avoid doing it for
        // every uncached memory fetch?
    } else {
        // TODO
        // Use exception
        // raise Exception(f"PPUADDR is in a weird state: {self._PPUADDR_pushes}, {self._PPUADDR}")
        printf("PPUADDR is in a weird state: %d, %d\n", _PPUADDR_pushes, _PPUADDR);
    }
}

void
PPU::set_PPUSCROLL(uint8_t what) {
    // FIXME
    // Possibly validate what's being put in here?
    // "Horizontal offsets range from 0 to 255. "Normal" vertical offsets
    // range from 0 to 239, while values of 240 to 255 are treated as -16
    // through -1 in a way, but tile data is incorrectly fetched from the
    // attribute table."
    if (_PPUSCROLL_pushes == 0) {
        // High byte is pushed first.
        _PPUSCROLL = what << 8;
        _PPUSCROLL_pushes += 1;
    } else if (_PPUSCROLL_pushes == 1) {
        // Low byte is pushed after high byte.
        _PPUSCROLL += what;
        _PPUSCROLL_pushes = 0;
    } else {
        // TODO
        // Use exception
        // raise Exception(f"PPUSCROLL is in a weird state: {self._PPUSCROLL_pushes}, {self._PPUSCROLL}")
        printf("PPUSCROLL is in a weird state: %d, %d\n", _PPUSCROLL_pushes, _PPUADDR);
    }
}

uint8_t
PPU::send_data_to_bus(PPURegister from_register) {
    /*
     * The CPU shares its instructions with the PPU in case it needs to
     * take action on them. The PPU is subordinate in this relationship
     * because the CPU clearly does most of the heavy lifting. That said,
     * the PPU does need to sometimes do some internal state updating
     * before the CPU executes.
     */
    // The only register that we can support reading from right now
    // is PPUSTATUS. It also makes sense that read is happening before
    // the cpu because it'll need the value read back to populate
    // some register or somewhere in memory.
    if (from_register == PPURegister::PPUSTATUS) {
        return PPUSTATUS();
    }
    // All registers should be handled, so we shouldn't get here...
    return 0;
}

void
PPU::receive_data_from_bus(uint8_t data, PPURegister to_register) {
    // We need to handle write ops in post_next because it gives a chance
    // for the CPU to put it into the shared bus. If we try and access
    // the data in the bus before the CPU got a chance to put it in there
    // we'll have no data.
    PPURegister reg = to_register;
    if (reg == PPURegister::PPUCTRL) {
        _PPUCTRL = data;
    } else if (reg == PPURegister::PPUMASK) {
        _PPUMASK = data;
    } else if (reg == PPURegister::OAMADDR) {
        _OAMADDR = data;
    } else if (reg == PPURegister::OAMDATA) {
        // FIXME
        // Going off VBLANK to determine if rendering or not, this
        // might be wrong timing-wise.
        if (rendering()) {
            printf("WARNING writing to OAMDATA while rendering.");
            return;
        }
        // FIXME
        // This should write to OAMDMA?
        // memory.write(data, _OAMDATA);
        _OAMADDR++;
        // FIXME
        // This may need to support a read mode with auto incrementing
        // but that may be internal to the PPU only...
    } else if (reg == PPURegister::PPUSCROLL) {
        set_PPUSCROLL(data);
    } else if (reg == PPURegister::PPUADDR) {
        set_PPUADDR(data);
    } else if (reg == PPURegister::PPUDATA) {
        // Do this only if we're writing to the PPU memory.
        // Read PPUSTATUS but do nothing with the result. This forces
        // a bit to be cleared.
        PPUSTATUS();
        memory.write(data, PPUADDR());

        // Shouldn't be a need for this after the CPU handles the
        // instruction but if so we can move it there.
        // ppu._increment_PPUADDR()
        uint8_t adder = increment_mode() == 0 ? 1 : 32;
        // Notice that we're not using the setter/getter.
        _PPUADDR += adder;
    }
}

void
PPU::next() {
    _cycle();
    _post_cycle();
}

void
PPU::_cycle() {
    /*
     * Called once for each PPU cycle after the CPU executes. Knowing how
     * many cycles the CPU did lets us know how many cycles to perform
     * here since there is a 3:1 ratio of PPU cycles to CPU cycles.
     * This means that PPU calls are interleaved with CPU calls, which
     * is probably fine since the PPU will be doing pixel, rather than
     * instruction, processing.
     * The goal at each cycle is to do some part of this:
     * https://wiki.nesdev.com/w/index.php/PPU_rendering#Line-by-line_timing
     */
    // TODO
    // This is going to get very ugly as we stuff in all sorts of
    // conditions here. This may need to be pieced out.
    _update_state();
    _maybe_compute_pixel();
}

void
PPU::_update_state() {
    /* 
     * Various states crammed together in one function because calling
     * them in a row is costly.
     */
    if (clock.ppu_cycles == 1) {
        // Toggle VBLANK on first cycle of scanline 241
        if (scanline == PPUVBlankScanline) {
            // TODO
            // This might have to do the read ot clear it.
            _PPUSTATUS |= 0x80;
        } else if (scanline == PPUMaxScanline) {
            // Toggle VBLANK off first cycle of scanline 261
            _PPUSTATUS &= 0x7f;
        }
    } else if (257 <= clock.ppu_cycles && clock.ppu_cycles <= 320) {
        // self._maybe_zero_oamaddr()
        _OAMADDR = 0;
    }
}

void
PPU::_maybe_compute_pixel() {
    if (scanline >= 240) {
        // TODO
        // This is incomplete.
        // No pixel draws for these non-visible scanlines except
        // at 261 which is readying for the next frame.
        return;
    }

    if (1 > clock.ppu_cycles || clock.ppu_cycles > 256) {
        // No generating pixels during these PPU cycles. It only needs
        // to generate 256 pixels across so it makes no sense to run
        // outside of that point.
        // TODO
        // That's not quite accurate since there is loading and priming
        // certain data for the next scanline ahead of time.
        return;
    }

    // FIXME
    // Hacky
    uint8_t colour = colour_for_pixel(*this, _x, _y);
    // Index into the pixel buffer since it's flattened
    // and not an x/y grid.
    uint64_t pixel_index = _x + _y * 256;
    pixels[pixel_index] = colour;

    // We need to increment x here because it's tracking pixels. If we
    // do it in _post_cycle it'll increment even if we never moved the
    // pixel location.
    _x++;
}

void
PPU::_post_cycle() {
    clock.ppu_cycles++;
    if (clock.ppu_cycles == PPUCyclesPerScanline) {
        // TODO
        // 341 PPU cycles per scanline. This might be NTSC specific.
        // After that, we need to roll over and begin counting
        // from 0 again. We need to take any number that put us
        // above 341 and set it as the starting value.
        clock.ppu_cycles = 0;
        // Reset the horizontal scroll because we got to the end of
        // the scanline.
        _x = 0;
        scanline++;

        // TODO
        // Vertical register is computed at cycle 256, not at 341.
        // (See NTSC timing diagram, this obviously has implications
        // for badly behaved programs).
        _y++;
    }

    // One frame.
    if (scanline > PPUMaxScanline) {
        // FIXME
        // As the comment in the function says, this is not how the CPU works
        // at all. However, it'll be good enough to test sprite rendering
        // frame by frame.
        render_sprites(*this);
        // Reset the number of scanlines drawn, as well as our x and y offsets
        // for the current pixel being drawn.
        // Flush the pixel buffer to disk for now rather than output to screen.
        scanline = 0;
        _x = 0;
        _y = 0;
        frames++;
        renderer.render(pixels);
    }
}
