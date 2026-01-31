#include <assert.h>
#include "NESController.h"

void
test_handle_signal() {
    // Sets _polling and _bit_pointer based on the signal value.
    // Since they're private members we need to test this by
    // side effect.
    NESController nc;
    nc.handle_signal(1);
    nc.handle_input(Input::A);
    assert(nc.read_next() == 1);
    // only 0x1 is in the input but because it's still polling
    assert(nc.read_next() == 1);
    nc.handle_signal(0);
    assert(nc.read_next() == 1);
    assert(nc.read_next() == 0);
}

void
test_read_next() {
    // Ensures that when an input is received, it can be read
    // from later on.
    NESController nc;
    nc.handle_input(Input::A);
    nc.handle_signal(1);
    nc.handle_input(Input::LEFT);
    nc.handle_signal(0);
    assert(nc.read_next() == 1);
    assert(nc.read_next() == 0);
    assert(nc.read_next() == 0);
    assert(nc.read_next() == 0);
    assert(nc.read_next() == 0);
    assert(nc.read_next() == 0);
    assert(nc.read_next() == 1);
    assert(nc.read_next() == 0);
}

int
main() {
    test_handle_signal();
    test_read_next();
    return 0;
}
