#ifndef STACK_H
#define STACK_H

#include "CPUMemory.h"
#include <unistd.h>

const static uint16_t _STACK_BASE = 0x100;


class Stack {
public:
    // Defines a stack that is compatible with the following
    // requirements:
    //
    // "The processor supports a 256 byte stack located between
    // $0100 and $01FF. The stack pointer is an 8 bit register
    // and holds the low 8 bits of the next free location on the
    // stack. The location of the stack is fixed and cannot be
    // moved."
    //
    // So basically we need to always add 0x100 to our stack pointer
    // value to retrieve and put things in the right location.
    void push_8(CPUMemory& memory, uint8_t& sp, uint8_t value) {
        memory.write(value, _STACK_BASE + sp);
        // We pushed a byte.
        sp--;
    }

    void push_16(CPUMemory& memory, uint8_t& sp, uint16_t value) {
        // High value first.
        memory.write((value >> 8), _STACK_BASE + sp);
        sp--;
        // Low value next
        memory.write((value & 0xff), _STACK_BASE + sp);
        sp--;
    }

    uint8_t pop_8(CPUMemory& memory, uint8_t& sp) {
        /*
         * Size is the size in bytes of the data we're popping.
         * This value has to be right to control the stack pointer.
         * 
         * Stack pointer must be incremented before each memory
         * read.
         */
        // TODO
        // We're only dealing with uint8 or uint16 so this should be ok
        // however, it's not the best. It'd be nicer to just read values
        // directly from the bytearray and convert them.
        sp++;
        // Stack pointer will go in the higher bits since we
        // can't return tuples
        uint8_t value = memory.read_one(_STACK_BASE + sp);
        return value;
    }

    uint16_t pop_16(CPUMemory& memory, uint8_t& sp) {
        sp++;
        uint8_t low = memory.read_one(_STACK_BASE + sp);
        sp++;
        uint16_t high = memory.read_one(_STACK_BASE + sp);
        uint16_t value = high;
        value <<= 0x8;
        value += low;
        return value;
    }
};

#endif
