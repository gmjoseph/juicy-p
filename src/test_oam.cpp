#include <assert.h>
#include "Clock.h"
#include "CPU.h"
#include "IO_DB.h"
#include "OAM.h"
#include "PPU.h"

void test_oam() {
    uint8_t cases[] = {
        // a9 02 (LDA 0x02)
        // 8d 14 40 (STA 0x4014)
        0xa9, 0x02,
        0x8d, 0x14, 0x40,
        // a2 02 (LDX 0x02)
        // 8e 14 40 (STX 0x4014)
        0xa2, 0x02,
        0x8e, 0x14, 0x40,
        // a0 02 (LDY 0x02)
        // 8c 14 40 (STY 0x4014)
        0xa0, 0x02,
        0x8c, 0x14, 0x40
    };

    const uint8_t chunk_size = 5;
    for (uint8_t i = 0; i < sizeof(cases)/sizeof(uint8_t); i += chunk_size) {
        // Deal with five byte 
        Clock clock;
        OAM oam;
        IO_DB bus;
        CPU cpu = CPU(bus, clock, oam);
        cpu.pc = 0xc000;
        PPU ppu = PPU(bus, clock, oam);

        // Ensure that they use the same reference.
        assert(&(cpu.oam) == &(ppu.oam));

        uint8_t* assembly = &(cases[i]);
        cpu.memory.write_cpu_memory(0xc000, chunk_size, assembly);
        cpu.pc = 0xc000;

        // Add some bytes
        uint8_t oam_data[] = { 0xca, 0xfe, 0xba, 0xbe };
        for (uint8_t i = 0; i < sizeof(oam_data)/sizeof(uint8_t); i++) {
            cpu.memory.write(oam_data[i], 0x0200 + i);
            assert(ppu.oam.memory[i] != oam_data[i]);
        }

        // Two sets of instructions need to be called for
        // the transfer to happen.
        cpu.next(false);
        cpu.next(false);

        // At this point the memory should've bene transferred over
        // to PPU OAM memory.
        for (uint8_t i = 0; i < sizeof(oam_data)/sizeof(uint8_t); i++) {
            cpu.memory.write(oam_data[i], 0x0200 + i);
            assert(ppu.oam.memory[i] == oam_data[i]);
        }
    }
}

int
main() {
    test_oam();
    return 0;
}