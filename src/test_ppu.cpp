#include <assert.h>
#include "Clock.h"
#include "CPU.h"
#include "IO_DB.h"
#include "OAM.h"
#include "PPU.h"

void
test_PPUSCROLL_writes() {
    /*
     * Writing to this register is done using successive pushes/stores
     * where the memory-mapped address is the target, for example:
     * LDA $low_byte (immediate mode)
     * STA 0x2005
     * LDA $high_byte (immediate mode)
     * STA 0x2005    
     * Would result with PPUSCROLL holding the x and y values in the
     * register.
     */
    Clock clock;
    OAM oam;
    IO_DB bus;
    CPU cpu = CPU(bus, clock, oam);
    cpu.pc = 0xc000;
    PPU ppu = PPU(bus, clock, oam);

    // a9 ba (LDA 0xba)
    // 8d 05 20 (STA 0x2005)
    // a9 be (LDA 0xbe)
    // 8d 05 20 (STA 0x2005)
    uint8_t assembly[] = {
        0xa9, 0xba,
        0x8d, 0x05, 0x20,
        0xa9, 0xbe,
        0x8d, 0x05, 0x20
    };
    cpu.memory.write_cpu_memory(0xc000, sizeof(assembly)/sizeof(uint8_t), assembly);

    cpu.next(false);
    assert(ppu.PPUSCROLL() != 0xbabe);
    assert(cpu.a == 0xba);

    cpu.next(false);
    // It's private.
    // assert(ppu._PPUSCROLL_pushes == 1);
    assert(ppu.PPUSCROLL() == 0xba00);
    assert(ppu.scroll_x() == 0xba);
    assert(ppu.scroll_y() == 0x00);

    cpu.next(false);
    assert(cpu.a == 0xbe);

    cpu.next(false);
    // It's private.
    // assert(ppu._PPUSCROLL_pushes == 0);
    assert(ppu.PPUSCROLL() == 0xbabe);
    assert(ppu.scroll_x() == 0xba);
    assert(ppu.scroll_y() == 0xbe);
}

void
test_PPUADDR_writes() {
    /*
     * Writing to this register is done using successive pushes/stores
     * where the memory-mapped address is the target, for example:
     * LDA $low_byte (immediate mode)
     * STA 0x2006
     * LDA $high_byte (immediate mode)
     * STA 0x2006    
     * Would result with PPUADDR holding a 16 bit address for PPU memory.
     */
    Clock clock;
    OAM oam;
    IO_DB bus;
    CPU cpu = CPU(bus, clock, oam);
    cpu.pc = 0xc000;
    PPU ppu = PPU(bus, clock, oam);

    // a9 ba (LDA 0xba)
    // 8d 06 20 (STA 0x2006)
    // a9 be (LDA 0xbe)
    // 8d 06 20 (STA 0x2006)
    uint8_t assembly[] = {
        0xa9, 0xba,
        0x8d, 0x06, 0x20,
        0xa9, 0xbe,
        0x8d, 0x06, 0x20
    };
    cpu.memory.write_cpu_memory(0xc000, sizeof(assembly)/sizeof(uint8_t), assembly);

    cpu.next(false);
    assert(ppu.PPUADDR() != 0xbabe);
    assert(cpu.a == 0xba);

    cpu.next(false);
    // It's private.
    // assert(ppu._PPUADDR_pushes == 1);
    assert(ppu.PPUADDR() == 0xba00);

    cpu.next(false);
    assert(cpu.a == 0xbe);

    cpu.next(false);
    // It's private.
    // assert(ppu._PPUADDR_pushes == 0);
    assert(ppu.PPUADDR() == 0xbabe);

}

int
main() {
    test_PPUSCROLL_writes();
    test_PPUADDR_writes();
    return 0; 
}
