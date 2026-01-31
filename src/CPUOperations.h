#ifndef CPU_OPERATIONS_H
#define CPU_OPERATIONS_H

#include <stdint.h>
#include <map>
#include <string>
#include "Opcodes.h"

class CPU;

void handle_instruction(CPU&, Instruction&, uint8_t*);
void NMI(CPU&);

#endif