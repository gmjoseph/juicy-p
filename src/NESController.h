#ifndef NES_CONTROLLER_H
#define NES_CONTROLLER_H

#include <stdint.h>
#include "Constants.h"
#include <stdio.h>

/*
 * This is not strictly accurate.
 * When the _polling flag is set, the controller should poll
 * for button state changes. When it's no longer set, that should
 * stop.
 * The problem with that is, the emulated code runs so fast
 * that within that narrow frame of polling / not polling, it
 * never picks up any inputs. This is because the input frequency
 * is way slower than the frequency at which the emulated code
 * runs.
 * As a result, this allows inputs to come in even when polling
 * is off.
 * It then stores those inputs for the next poll start/stop and
 * allows them to be picked up by the game.
 * Once an input has been used, it's discarded.
 * The end result is that we have sane controller behaviour that
 * works okay with OS-provided inputs that also ensures a one-time
 * delivery of the input to the emulated code.
 * I think it also enables a kind of 'rapid fire' (where the
 * key is held down and then the key press is delivered at whatever
 * Hz to the controller, which is then pulled off during read,
 * even if polling isn't open).
 *
 * FIXME
 * This could become a problem where games are explicitly not picking
 * up inputs during some phase of the game. If that's the case, when
 * the game starts picking up inputs again it'll receive all the
 * inputs from before at once.
 * However this works for now. A longer term fix could be to run the
 * emulation more slowly and tie it into some sort of 60fps or key
 * vending solution where each CPU instruction is tied directly to
 * a Hz of 60.
 *
 * Another option might be to just force this thread to sleep for
 * 1/60th of a second (1 frame at 60 fps) to pick up anything from
 * the OS on the other thread. That window may be just large enough
 * to not show jittering ot stuttering but also allow a key to be
 * picked up.
 */
class NESController {
private:
    bool _polling = false;
    uint8_t _inputs = 0;
    uint8_t _bit_pointer = 0;

public:
    inline void handle_signal(uint8_t signal) {
        // When a value is written to 0x4016/0x4017 then
        // a signal of whatever's being stored will be received
        // here. A write of 0x1 means start polling, a write
        // of 0x0 means stop.
        _polling = signal & 0x1;
        if (_polling) {
            // FIXME
            // This is disabled for now:
            // Clear whatever inputs were previously recorded.
            // This lets the controller internally record a new
            // input state which the CPU can then get when _polling
            // is set to false.
            // _inputs = 0;
            _bit_pointer = 0;
        }
        // printf("polling? signal? %x %x\n", _polling, signal);
    }

    inline void handle_input(Input input) {
        // FIXME
        // This is disabled for now:
        // if (!_polling) {
        //     // Ignoring all inputs when the game isn't asking for it.
        //     printf("handle input %d won't save since not polling %p\n", _inputs, this);
        //     return;
        // }

        // Allow handling even when not strobing, the inputs will be
        // picked up on the next read.
        uint8_t mask = 0x1 << (int)input;
        _inputs |= mask;
        // printf("handle input, inputs and mask: %d, %d\n", _inputs, mask);
    }

    inline uint8_t read_next() {
        if (_polling || _bit_pointer > 8) {
            // "While S (strobe) is high, the shift registers in
            // the controllers are continuously reloaded from the
            // button states, and reading $4016/$4017 will keep
            // returning the current state of the first button (A)."
            // But because we wrote 1 to place 0 we just return 1.
            return 0x1;
        }
        uint8_t next = (_inputs >> _bit_pointer) & 0x1;

        _bit_pointer++;

        // "After 8 bits are read, all subsequent bits will report 1
        // on a standard NES controller, but third party and other
        // controllers may report other values here."
        if (_bit_pointer > 8) {
            // Consumer got a chance to read out any stored inputs.
            // So now reset them.
            // FIXME
            // This is only a temporary solution because _inputs should probably
            // be reset when polling is reset.
            _inputs = 0;
        }
        return next;
    }
};

#endif
