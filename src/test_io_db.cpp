#include <vector>
#include <assert.h>
#include <stdint.h>
#include "Clock.h"
#include "Constants.h"
#include "CPU.h"
#include "IO_DB.h"
#include "PPU.h"

// TODO
// BIT is special in that it doesn't actually update a register.
// So in this case, we expect the registers to be unchanged from
// their defaults. Therefore, while the BIT operation can result
// in a read from a PPU register, it's hard to test because the
// value is then read internally in the op_BIT function.
// MagicMocks would work here to test certain calls in that
// function.

// Seed the CPU registers with values we can check the bus for.
// TODO
// Do this on 'READ' from PPU registers as well.
uint8_t _IO_A = 0xff;
uint8_t _IO_X = 0xba;
uint8_t _IO_Y = 0xbe;

// What data do we expect to be on the bus for write mnemonics
// going from CPU to PPU.
uint8_t
bus_data_for_mnemonic(Mnemonic mnemonic) {
    switch (mnemonic) {
        case Mnemonic::STA: return _IO_A;
        case Mnemonic::STX: return _IO_X;
        case Mnemonic::STY: return _IO_Y;
        default: return 0;
    }
}

void
assemble(Mnemonic mnemonic, uint16_t address, uint8_t* assembly_output) {
    /*
     * Assemble the mnemonic and address into bytecode
     */
    // Assuming ABSOLUTE addressing for each of these
    uint8_t opcode = 0x0;
    switch (mnemonic) {
        case Mnemonic::LDA:
            opcode = 0xad;
            break;
        case Mnemonic::LDX:
            opcode = 0xae;
            break;
        case Mnemonic::LDY:
            opcode = 0xac;
            break;
        case Mnemonic::BIT:
            opcode = 0x2c;
            break;
        case Mnemonic::STA:
            opcode = 0x8d;
            break;
        case Mnemonic::STX:
            opcode = 0x8e;
            break;
        case Mnemonic::STY:
            opcode = 0x8c;
            break;
        default:
            opcode = 0;
            break;
    };
    uint8_t high = address >> 0x8;
    uint8_t low = address & 0xff;
    assembly_output[0] = opcode;
    assembly_output[1] = low;
    assembly_output[2] = high;
}

void
setup_cpu(CPU& cpu) {
    cpu.pc = 0xc000;
    cpu.a = _IO_A;
    cpu.x = _IO_X;
    cpu.y = _IO_Y;
}

uint8_t
cpu_register_value_for_mnemonic(CPU& cpu, Mnemonic mnemonic) {
    switch (mnemonic) {
        case Mnemonic::LDA:
            return cpu.a;
        case Mnemonic::LDX:
            return cpu.x;
        case Mnemonic::LDY:
            return cpu.y;
        default:
            return 0;
    }
}
// Fully parametrized tests don't work well because not all addresses
// are supported. Compounding that, there are very different behaviours
// to expect when writing to certain PPU registers. As a result they
// need to be tested semi-discretely.

void
test_cpu_writes_to_PPUCTRL() {
    /*
     * Ensures that the CPU register data ends up in PPUCTRL
     */
    std::vector<Mnemonic> write_mnemonics = {
        Mnemonic::STA,
        Mnemonic::STX,
        Mnemonic::STY
    };

    for (auto& mnemonic : write_mnemonics) {
        // Annoyingly required for each test.
        IO_DB bus;
        Clock clock;
        OAM oam;
        CPU cpu = CPU(bus, clock, oam);
        PPU ppu = PPU(bus, clock, oam);
        setup_cpu(cpu);

        uint8_t assembly[3] = { 0 };
        assemble(mnemonic, (uint16_t)PPUAddress::PPUCTRL_ADDRESS, assembly);
        cpu.memory.write_cpu_memory(cpu.pc, 3, assembly);
        // E.g. if it's STA we'll put the cpu's 'a' value into whichever
        // PPU register it is. So if the argument is PPUCTRL we should
        // expect the cpu.a == ppu.PPUCTRL
        auto data_from_cpu = bus_data_for_mnemonic(mnemonic);
        assert(ppu.PPUCTRL() != data_from_cpu);

        // PPU can only read from the bus after the CPU instruction
        // finished writing.
        cpu.next(false);
        assert(ppu.PPUCTRL() == data_from_cpu);
    }
}

void
test_cpu_writes_to_PPUMASK() {
    /*
     * Ensures that the CPU register data ends up in PPUMASK
     */
    std::vector<Mnemonic> write_mnemonics = {
        Mnemonic::STA,
        Mnemonic::STX,
        Mnemonic::STY
    };

    for (auto& mnemonic : write_mnemonics) {
        IO_DB bus;
        Clock clock;
        OAM oam;
        CPU cpu = CPU(bus, clock, oam);
        PPU ppu = PPU(bus, clock, oam);
        setup_cpu(cpu);

        uint8_t assembly[3] = { 0 };
        assemble(mnemonic, (uint16_t)PPUAddress::PPUMASK_ADDRESS, assembly);
        cpu.memory.write_cpu_memory(cpu.pc, sizeof(assembly)/sizeof(uint8_t), assembly);
        auto data_from_cpu = bus_data_for_mnemonic(mnemonic);
        assert(ppu.PPUMASK() != data_from_cpu);

        // PPU can only read from the bus after the CPU instruction
        // finished writing.
        cpu.next(false);
        assert(ppu.PPUMASK() == data_from_cpu);
    }
}

void
test_cpu_writes_to_PPUADDR() {
    /*
     * PPUADDR is special in that it takes two writes to it and builds
     * up an address for where we are in PPU memory.
     */
    std::vector<Mnemonic> write_mnemonics = {
        Mnemonic::STA,
        Mnemonic::STX,
        Mnemonic::STY
    };

    for (auto& mnemonic : write_mnemonics) {
        IO_DB bus;
        Clock clock;
        OAM oam;
        CPU cpu = CPU(bus, clock, oam);
        PPU ppu = PPU(bus, clock, oam);
        setup_cpu(cpu);

        uint8_t first_instruction[3] = { 0 };
        assemble(mnemonic, (uint16_t)PPUAddress::PPUADDR_ADDRESS, first_instruction);
        uint8_t second_instruction[3] = { 0 };
        assemble(mnemonic, (uint16_t)PPUAddress::PPUADDR_ADDRESS, second_instruction);
        cpu.memory.write_cpu_memory(
            cpu.pc,
            sizeof(first_instruction)/sizeof(uint8_t),
            first_instruction
        );
        cpu.memory.write_cpu_memory(
            cpu.pc + sizeof(first_instruction)/sizeof(uint8_t),
            sizeof(second_instruction)/sizeof(uint8_t),
            second_instruction
        );

        // Two instructions to write the entire address to the register.
        cpu.next(false);
        cpu.next(false);
        auto high = (bus_data_for_mnemonic(mnemonic) << 8);
        auto low = bus_data_for_mnemonic(mnemonic);
        uint16_t expected_address = high + low;
        assert(ppu.PPUADDR() == expected_address);
    }
}

void
test_cpu_writes_to_PPUDATA() {
    /*
     * PPUDATA is special in that it takes the data that's given to
     * it over the bus and then puts it into memory based on PPUADDR.
     * It also needs to read from PPUSTATUS first. Lastly, it
     * increments PPUADDR.
     */
    std::vector<Mnemonic> write_mnemonics = {
        Mnemonic::STA,
        Mnemonic::STX,
        Mnemonic::STY
    };

    for (auto& mnemonic : write_mnemonics) {
        IO_DB bus;
        Clock clock;
        OAM oam;
        CPU cpu = CPU(bus, clock, oam);
        PPU ppu = PPU(bus, clock, oam);
        setup_cpu(cpu);

        uint8_t assembly[3] = { 0 };
        assemble(mnemonic, (uint16_t)PPUAddress::PPUDATA_ADDRESS, assembly);
        cpu.memory.write_cpu_memory(cpu.pc, sizeof(assembly)/sizeof(uint8_t), assembly);

        auto start_address = ppu.PPUADDR();
        cpu.next(false);
        assert(ppu.PPUADDR() == start_address + 1);

        auto data_in_memory = ppu.memory.read_one(start_address);
        auto data_from_cpu = bus_data_for_mnemonic(mnemonic);
        assert(data_in_memory == data_from_cpu);
    }
}

void
test_cpu_reads_from_PPUSTATUS() {
    /*
     * Reads from PPU registers put the right value in the right CPU register.
     */
    std::vector<Mnemonic> read_mnemonics = {
        Mnemonic::LDA,
        Mnemonic::LDX,
        Mnemonic::LDY
    };
    for (auto& mnemonic : read_mnemonics) {
        IO_DB bus;
        Clock clock;
        OAM oam;
        CPU cpu = CPU(bus, clock, oam);
        PPU ppu = PPU(bus, clock, oam);
        setup_cpu(cpu);
        uint8_t assembly[3] = { 0 };
        assemble(mnemonic, (uint16_t)PPUAddress::PPUSTATUS_ADDRESS, assembly);
        cpu.memory.write_cpu_memory(cpu.pc, sizeof(assembly)/sizeof(uint8_t), assembly);
        assert(ppu.PPUSTATUS() != cpu_register_value_for_mnemonic(cpu, mnemonic));

        cpu.next(false);
        assert(ppu.PPUSTATUS() == cpu_register_value_for_mnemonic(cpu, mnemonic));
    }
}

void
test_cpu_BIT_from_PPUSTATUS() {
    /*
     * BIT is special because it only uses the value from the PPU register
     * internally for calculations.
     */
    IO_DB bus;
    Clock clock;
    OAM oam;
    CPU cpu = CPU(bus, clock, oam);
    PPU ppu = PPU(bus, clock, oam);
    setup_cpu(cpu);

    uint8_t assembly[3] = { 0 };
    assemble(Mnemonic::BIT, (uint16_t)PPUAddress::PPUSTATUS_ADDRESS, assembly);
    cpu.memory.write_cpu_memory(cpu.pc, sizeof(assembly)/sizeof(uint8_t), assembly);
    // Start state of the register before it gets modified by BIT
    assert(cpu.p == 0x24);

    cpu.next(false);
    // TODO
    // Need to check this given differing PPUSTATUS data just to
    // be sure it's all working.
    assert(cpu.p == 0x26);
}

int
main() {
    test_cpu_writes_to_PPUCTRL();
    test_cpu_writes_to_PPUMASK();
    test_cpu_writes_to_PPUADDR();
    test_cpu_writes_to_PPUDATA();
    test_cpu_reads_from_PPUSTATUS();
    test_cpu_BIT_from_PPUSTATUS();
    return 0;
}
