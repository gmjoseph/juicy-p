#ifndef IO_DB_H
#define IO_DB_H

#include <stdint.h>
#include "PPU.h"


class IO_DB {
public:
    // The PPU's constructor requires the bus, which then
    // sets itself as this pointer so it's highly unlikely that this
    // would ever be a nullptr.
    PPU* ppu;

public:
    // TODO
    // Update this to request_data so the CPU can get it from the PPU.
    inline uint8_t data(PPURegister from_register) {
        // TODO
        // Throw if reading data when _has_data is false?
        return ppu->send_data_to_bus(from_register);
    }

    inline void set_data(uint8_t data, PPURegister to_register) {
        ppu->receive_data_from_bus(data, to_register);
    }      
};

#endif
