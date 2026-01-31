#ifndef CPU_H
#define CPU_H

#include <unistd.h>
#include <string>
#include "Clock.h"
#include "CPUMemory.h"
#include "IO_DB.h"
#include "NESController.h"
#include "Stack.h"
#include "OAM.h"
#include "Opcodes.h"

class CPU {
public:
    // TODO
    // memory, clock, bus and stack should be friend-accessible
    // only.
    Clock& clock;
    IO_DB& bus;
    OAM& oam;
    CPUMemory memory;
    NESController nes_controller;
    Stack stack;
    // Accumulator
    uint8_t a = 0;
    // Index X
    uint8_t x = 0;
    // Index Y
    uint8_t y = 0;
    // Program Counter
    uint16_t pc = 0;
    // Stack Pointer
    uint8_t sp = 0xfd;
    // Status Register, ALU uses 6 bits but it's byte-wide.
    // This is equivalent to flags on x86:
    // 7  bit  0
    // ---- ----
    // NVss DIZC
    // |||| ||||
    // |||| |||+- Carry
    // |||| ||+-- Zero
    // |||| |+--- Interrupt Disable
    // |||| +---- Decimal
    // ||++------ No CPU effect, see: the B flag
    // |+-------- Overflow
    // +--------- Negative
    uint8_t p = 0x24;

private:
    inline void _mask_p(bool on, uint8_t mask) {
        p = on ? (p | mask) : (p & (mask ^ 0xff));
    };
    void _power_up();
    void _debug(std::string mnemonic);


public:
    CPU(IO_DB& bus, Clock& clock, OAM& oam);

    // Is the carry flag set or not? 
    inline uint8_t carry() { return (p & 0x1); };
    inline void set_carry(bool on) { return _mask_p(on, 0x1); };
    // Is the zero flag set or not? 
    inline uint8_t zero() { return (p & 0x2); };
    inline void set_zero(bool on) { return _mask_p(on, 0x2); };
    // Is the interrupt_disabled flag set or not? 
    inline uint8_t interrupt_disabled() { return (p & 0x4); };
    inline void set_interrupt_disabled(bool on) { return _mask_p(on, 0x4); };
    // Is the decimal flag set or not? 
    inline uint8_t decimal() { return (p & 0x8); };
    inline void set_decimal(bool on) { return _mask_p(on, 0x8); };
    // Is the overflow flag set or not? 
    inline uint8_t overflow() { return (p & 0x40); };
    inline void set_overflow(bool on) { return _mask_p(on, 0x40); };
    // Is the negative flag set or not? 
    inline uint8_t negative() { return (p & 0x80); };
    inline void set_negative(bool on) { return _mask_p(on, 0x80); };
    inline void set_bit_4(bool on) { return _mask_p(on, 0x10); };
    inline void set_bit_5(bool on) { return _mask_p(on, 0x20); };

    void reset();
    void next(bool received_nmi);

    void upload_oamdma_data(uint8_t high_byte);
};

#endif
