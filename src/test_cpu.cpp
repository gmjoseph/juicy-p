#include <assert.h>
#include "Clock.h"
#include "CPU.h"
#include "IO_DB.h"
#include "OAM.h"

void
test_cpu_nes_controller() {
    // Testing both to see if the cpu is properly handling
    // cases where the src/dst is the controller's mapped
    // address.
    uint8_t assembly[] = {
        // Strobe controller (i.e. start polling)
        // a9 01 (LDA 0x01)
        // 8d 14 40 (STA 0x4016)
        0xa9, 0x01,
        0x8d, 0x16, 0x40,
        // Stop strobing controller
        // a9 00 (LDA 0x00)
        // 8d 14 40 (STA 0x4016)
        0xa9, 0x00,
        0x8d, 0x16, 0x40,
        // Reading values from the controller into a.
        // Read Input::A
        // ad 16 40 (LDA 0x4016)
        0xad, 0x16, 0x40,
        // Read Input::B
        // ad 16 40 (LDA 0x4016)
        0xad, 0x16, 0x40,
        // Read Input::SELECT
        // ad 16 40 (LDA 0x4016)
        0xad, 0x16, 0x40,
        // Read Input::START
        // ad 16 40 (LDA 0x4016)
        0xad, 0x16, 0x40,
        // Read Input::INPUT_UP
        // ad 16 40 (LDA 0x4016)
        0xad, 0x16, 0x40,
        // Read Input::INPUT_DOWN
        // ad 16 40 (LDA 0x4016)
        0xad, 0x16, 0x40,
        // Read Input::INPUT_LEFT
        // ad 16 40 (LDA 0x4016)
        0xad, 0x16, 0x40,
        // Read Input::INPUT_RIGHT
        // ad 16 40 (LDA 0x4016)
        0xad, 0x16, 0x40,
    };

    Clock clock;
    OAM oam;
    IO_DB bus;
    CPU cpu = CPU(bus, clock, oam);
    cpu.memory.write_cpu_memory(0xc000, sizeof(assembly)/sizeof(uint8_t), assembly);
    cpu.pc = 0xc000;

    // fake an input so they're non 0.
    cpu.nes_controller.handle_input(Input::A);
    assert(1 == cpu.nes_controller.read_next());

    // Loads a and then puts it to the controller.
    cpu.next(false);
    cpu.next(false);
    // nes_controller should now be polling and all inputs
    // should be 0'd out.

    cpu.nes_controller.handle_input(Input::SELECT);
    // nes_controller should no longer be polling after these
    // run (that's the first cpu.next). There should be an event
    // at the position of the SELECT bit.
    cpu.next(false);
    cpu.next(false);
    // To get to the SELECT bit, we need to cause a read_next()
    // to happen a few times via CPU LD* instructions. All the
    // other bits should still be 0.
    // Now read back all the 
    for (int i = 0; i < 8; i++) {
        if (i == (int)Input::SELECT) {
            assert(1 == cpu.a);
        } else {
            assert(0 == cpu.a);
        }
        cpu.next(false);
    }

    // Now that we've read all 8 bits, the controller should
    // only return 1s
    for (int i = 0; i < 16; i++) {
        assert(1 == cpu.nes_controller.read_next());
    }
}

int
main() {
    test_cpu_nes_controller();
    return 0;
}