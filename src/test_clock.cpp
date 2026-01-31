#include <assert.h>
#include "Clock.h"
#include "CPU.h"
#include "IO_DB.h"
#include "OAM.h"
#include "PPU.h"

void
test_clock_delay() {
    /*
     * Inspired by code in the full_palette test, this ensures that
     * the timing assumptions made in that test are accurate given
     * a small loop:
     * ```
	 *     ; Delay 29784 clocks
     *     ldx #24
     *     ldy #48
     * :	dey
     *     bne :-
     *     dex
     *     bne :-
     *     nop
     *     lda <0
     * ```
     * Where our point of reference starts at dey and ends at lda <0
     */
    IO_DB bus;
    Clock clock;
    OAM oam;
    // No PPU needed because the instructions have no interaction with it.
    CPU cpu = CPU(bus, clock, oam);

    // a2 18 (LDX 24)
    // a0 30 (LDY 48)
    // 88    (DEY)
    // d0 fd (BNE offset by -2 bytes to DEY)
    // ca    (DEX)
    // d0 fa (BNE offset by -5 bytes to DEY)
    // ea    (NOP)
    // a5 00 (LDA 0)
    uint8_t assembly[] = {
        0xa2, 0x18,
        0xa0, 0x30,
        0x88,
        0xd0, 0xfd,
        0xca,
        0xd0, 0xfa,
        0xea,
        0xa5, 0x00
    };
    cpu.memory.write_cpu_memory(0xc000, sizeof(assembly)/sizeof(uint8_t), assembly);
    cpu.pc = 0xc000;
    cpu.a = 0xff;
    uint8_t start_cycles = 0x7;
    assert(clock.cpu_cycles == start_cycles);

    // cpu.a is our sentinel because we'll load 0 into it when we're done
    // with the loop, letting us use that as a stopping condition.
    while (cpu.a != 0) {
        cpu.next(false);
    }

    uint16_t expected_elapsed_cycles = 29784;
    assert(clock.cpu_cycles - start_cycles == expected_elapsed_cycles);
}

int
main() {
    test_clock_delay();
    return 0;
}