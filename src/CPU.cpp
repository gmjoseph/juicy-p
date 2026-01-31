#include "Clock.h"
#include "CPU.h"
#include "CPUMemory.h"
#include "CPUOperations.h"
#include "IO_DB.h"
#include "OAM.h"

CPU::CPU(
    IO_DB& bus,
    Clock& clock,
    OAM& oam
) : bus(bus), clock(clock), oam(oam) {
    printf("CPU init with bus: %p clock: %p, oam: %p\n", &bus, &clock, &oam);
    _power_up();
}

void
CPU::_power_up() {
    /*
     * Puts the CPU into the powerup state:
     * https://wiki.nesdev.com/w/index.php/CPU_power_up_state
     */
    clock.cpu_cycles = 0x7;
    memory.write(0, 0x4015);
    memory.write(0, 0x4017);
    // in range(0x4000, 0x4013):
    for (uint16_t address = 0x4000; address < 0x4013; address++) {
        memory.write(0, address);
    }

    // "Internal memory ($0000-$07FF) has unreliable startup state.
    // Some machines may have consistent RAM contents at power-on,
    // but others do not."
    // TODO
    // Randomize those contents on boot since some games use them
    // as part of randomness. We can use a seed for deterministic
    // randomness for debugging (final builds too maybe?)
    reset();
}

void
CPU::reset() {
    // RESET (0xFFFC and 0xFFFD for low and high bytes respectively)
    // is the place to look for as the ROM entry point for on boot
    // i.e. where to set PC to to start fetching instructions.

    // TODO
    // Assuming that all the mappers just put the right data there
    // for now.
    // Use enums/constants for these values.
    // https://www.pagetable.com/?p=410
    // https://forums.nesdev.com/viewtopic.php?t=13560
    // http://users.telenet.be/kim1-6502/6502/proman.html#91
    // https://book.famicom.party/chapters/06-headersinterruptvectors.html
    // Little endian, of course.
    // Memory must be set first for this to work.
    uint8_t start_low = memory.read_one(0xFFFC);
    uint16_t start_high = memory.read_one(0xFFFD) << 8;
    uint16_t start_address = start_high + start_low;
    pc = start_address;
}

void
CPU::next(bool received_nmi) {
    // Handle the current instruction. May be pre-empted if an NMI
    // was received.
    // Advances the progarm counter (pc) to the next instruction.
    if (received_nmi) {
        // Not returning early because it seems once the interrupt is
        // handled the CPU should then start executing from there
        // immediately.
        // FIXME
        // Hacky.
        NMI(*this);
    }

    // Read four bytes worth of data. This should cover all addressing
    // modes. The first byte should be the opcode.
    uint8_t instruction_bytes[0x4] = { 0xff };
    memory.read(pc, 0x4, instruction_bytes);
    Instruction instruction = Instructions[instruction_bytes[0]];

    // FIXME
    // Hacky
    handle_instruction(*this, instruction, instruction_bytes);

    if (!IsBranchingMnemonic(instruction.mnemonic)) {
        // This must be done before we handle the instruction because
        // some of them may cause displacement which would also result
        // in a page crossing for certain program counters.
        pc += instruction.bytes;
    }

    clock.cpu_cycle(instruction.cycles);
    // clock.cpu_cycles += instruction.cycles;
}

void
CPU::upload_oamdma_data(uint8_t high_byte) {
    // When we get an action to upload OAMDMA data (it's a write to 0x4014)
    // we need to copy 256 bytes to PPU memory. We know which memory to
    // copy because the high byte of the CPU memory was loaded into some
    // register. E.g. LDA 0x40, STA 0x4014 would use 0x40 as the high
    // byte.
    // https://wiki.nesdev.com/w/index.php/PPU_programmer_reference#OAMDMA

    uint16_t address = high_byte << 8;
    uint8_t data[0x100] = { 0 };
    memory.read(address, 0x100, data);
    oam.upload_data(data);
    // FIXME
    // Technically the CPU is supposed to be paused for 512 cycles
    // 256 for each read/write, and then 1 dummy cycle, and then
    // 1 more cycle if we're on an odd number. Not sure if it's
    // important to mimic this for emulation.
}
