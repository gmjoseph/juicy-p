# Most descriptions are pulled verbatim from here:
# http://obelisk.me.uk/6502/reference.html

_description_map = {
    'ADC': '''
            This instruction adds the contents of a memory location
            to the accumulator together with the carry bit. If
            overflow occurs the carry bit is set, this enables multiple
            byte addition to be performed.
            C 	Carry Flag 	Set if overflow in bit 7
            Z 	Zero Flag 	Set if A = 0
            V 	Overflow Flag 	Set if sign bit is incorrect
            N 	Negative Flag 	Set if bit 7 set

            Additional docs from from the 6502 manual:
            The ninth bit of the result is stored in the carry flag and
            the remaining 8 bits reside in the accumulator.
            ''',
    'AND': '''
            A logical AND is performed, bit by bit, on the accumulator
            contents using the contents of a byte of memory.
            Z 	Zero Flag 	Set if A = 0
            N 	Negative Flag 	Set if bit 7 of A is set   
            ''',
    'ASL': '''
            This operation shifts all the bits of the accumulator or 
            memory contents one bit left. Bit 0 is set to 0 and bit 7
            is placed in the carry flag. The effect of this operation
            is to multiply the memory contents by 2 (ignoring 2's
            complement considerations), setting the carry if the result
            will not fit in 8 bits.
            C 	Carry Flag 	Set to contents of old bit 7
            Z 	Zero Flag 	Set if result = 0
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'BCC': '''
            If the carry flag is clear then add the relative
            displacement to the program counter to cause a
            branch to a new location.
            ''',
    'BCS': '''
            If the carry flag is set then add the relative displacement
            to the program counter to cause a branch to a new location.
            ''',
    'BEQ': '''
            If the zero flag is set then add the relative displacement
            to the program counter to cause a branch to a new location.
            ''',
    'BIT': '''
            This instructions is used to test if one or more bits
            are set in a target memory location. The mask pattern
            in A is ANDed with the value in memory to set or clear
            the zero flag, but the result is not kept. Bits 7 and 6
            of the value from memory are copied into the N and V
            flags.
            ''',
    'BMI': '''
            If the negative flag is set then add the relative
            displacement to the program counter to cause a branch
            to a new location.
            ''',
    'BNE': '''
            If the zero flag is clear then add the relative displacement
            to the program counter to cause a branch to a new location.
            ''',
    'BPL': '''
            If the negative flag is clear then add the relative
            displacement to the program counter to cause a branch
            to a new location.
            ''',
    'BVC': '''
            If the overflow flag is clear then add the relative
            displacement to the program counter to cause a branch
            to a new location.
            ''',
    'BVS': '''
            If the overflow flag is set then add the relative
            displacement to the program counter to cause a branch
            to a new location.
            ''',
    'CLC': '''
            Set the carry flag to zero.
            ''',
    'CLD': '''
            Sets the decimal mode flag to zero.
            ''',
    'CLV': '''
            Clears the overflow flag.
            ''',
    'CMP': '''
            This instruction compares the contents of the accumulator with
            another memory held value and sets the zero and carry flags as
            appropriate.
            C 	Carry Flag 	Set if A >= M
            Z 	Zero Flag 	Set if A = M
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'CPX': '''
            This instruction compares the contents of the X register with
            another memory held value and sets the zero and carry flags as
            appropriate.
            C 	Carry Flag 	Set if X >= M
            Z 	Zero Flag 	Set if X = M
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'CPY': '''
            This instruction compares the contents of the Y register with
            another memory held value and sets the zero and carry flags as
            appropriate.
            C 	Carry Flag 	Set if Y >= M
            Z 	Zero Flag 	Set if Y = M
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'DEC': '''
            Subtracts one from the value held at a specified memory location
            setting the zero and negative flags as appropriate.
            Z 	Zero Flag 	Set if result is zero
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'DEY': '''
            Subtracts one from the Y register setting the zero and negative
            flags as appropriate.
            Z 	Zero Flag 	Set if Y = 0
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'EOR': '''
            An exclusive OR is performed, bit by bit, on the
            accumulator contents using the contents of a byte
            of memory.
            Z 	Zero Flag 	Set if A = 0
            N 	Negative Flag 	Set if bit 7 set
            ''',
    'DEX': '''
            Subtracts one from the X register setting the zero and negative
            flags as appropriate.
            Z 	Zero Flag 	Set if X = 0
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'INC': '''
            Adds one to the value held at a specified memory location setting
            the zero and negative flags as appropriate.
            Z 	Zero Flag 	Set if result = 0
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'INX': '''
            Adds one to the X register setting the zero and negative flags as
            appropriate.
            Z 	Zero Flag 	Set if X = 0
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'INY': '''
            Adds one to the Y register setting the zero and negative flags as
            appropriate.
            Z 	Zero Flag 	Set if Y = 0
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'JMP': '''
            Sets the program counter to the address specified by
            the operand.
            ''',
    'JSR': '''
            The JSR instruction pushes the address (minus one)
            of the return point on to the stack and then sets
            the program counter to the target memory address.
            ''',
    'LDA': '''
            Loads a byte of memory into the accumulator setting the
            zero and negative flags as appropriate.
            Z 	Zero Flag 	Set if A = 0
            N 	Negative Flag 	Set if bit 7 of A is set
            ''',
    'LDX': '''
            Loads a byte of memory into the X register setting the
            zero and negative flags as appropriate.
            Z 	Zero Flag 	Set if X = 0
            N 	Negative Flag 	Set if bit 7 of X is set
            ''',     
    'LDY': '''
            Loads a byte of memory into the Y register setting the
            zero and negative flags as appropriate.
            Z 	Zero Flag 	Set if Y = 0
            N 	Negative Flag 	Set if bit 7 of Y is set
            ''',
    'LSR': '''
            Each of the bits in A or M is shift one place to the
            right. The bit that was in bit 0 is shifted into the
            carry flag. Bit 7 is set to zero.
            C 	Carry Flag 	Set to contents of old bit 0
            Z 	Zero Flag 	Set if result = 0
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'NOP': '''
            The NOP instruction causes no changes to the processor
            other than the normal incrementing of the program counter
            to the next instruction.
            ''',
    'ORA': '''
            An inclusive OR is performed, bit by bit, on the
            accumulator contents using the contents of a byte
            of memory.
            Z   Zero Flag 	Set if A = 0
            N 	Negative Flag 	Set if bit 7 set
            '''
    'PHA': '''
            Pushes a copy of the accumulator on to the stack.
            ''',
    'PHP': '''
            Pushes a copy of the status flags on to the stack.
            ''',
    'PLA': '''
            Pulls an 8 bit value from the stack and into the
            accumulator. The zero and negative flags are set
            as appropriate.
            Z 	Zero Flag 	Set if A = 0
            N 	Negative Flag 	Set if bit 7 of A is set            
            ''',
    'PLP': '''
            Set the carry flag to one.
            ''',
    'ROL': '''
            Move each of the bits in either A or M one place to the left.
            Bit 0 is filled with the current value of the carry flag whilst
            the old bit 7 becomes the new carry flag value.
            C 	Carry Flag 	Set to contents of old bit 7
            Z 	Zero Flag 	Set if result = 0
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'ROR': '''
            Move each of the bits in either A or M one place to the
            right. Bit 7 is filled with the current value of the carry
            flag whilst the old bit 0 becomes the new carry flag value.
            C 	Carry Flag 	Set to contents of old bit 0
            Z 	Zero Flag 	Set if result = 0
            N 	Negative Flag 	Set if bit 7 of the result is set
            ''',
    'RTI': '''
            The RTI instruction is used at the end of an interrupt
            processing routine. It pulls the processor flags from
            the stack followed by the program counter.
            ''',
    'RTS': '''
            The RTS instruction is used at the end of a subroutine
            to return to the calling routine. It pulls the program
            counter (minus one) from the stack.
            ''',
    'SBC': '''
            This instruction subtracts the contents of a memory location
            to the accumulator together with the not of the carry bit.
            If overflow occurs the carry bit is clear, this enables multiple
            byte subtraction to be performed.
            C 	Carry Flag 	Set if overflow in bit 7
            Z 	Zero Flag 	Set if A = 0
            V 	Overflow Flag 	Set if sign bit is incorrect
            N 	Negative Flag 	Set if bit 7 set
            ''',
    'SEC': '''
            Set the carry flag to one.
            ''',
    'SED': '''
            Set the decimal mode flag to one.
        ''',
    'SEI': '''
            Set the interrupt disable flag to one.
            ''',
    'STA': '''
            Stores the contents of the accumulator into memory.
            ''',
    'STY': '''
            Stores the contents of the Y register into memory.
            ''',
    'TAX': '''
            Copies the current contents of the accumulator into the
            X register and sets the zero and negative flags as
            appropriate.
            Z 	Zero Flag 	Set if X = 0
            N 	Negative Flag 	Set if bit 7 of X is set
            ''',
    'TAY': '''
            Copies the current contents of the accumulator into the
            Y register and sets the zero and negative flags as
            appropriate.
            Z 	Zero Flag 	Set if Y = 0
            N 	Negative Flag 	Set if bit 7 of Y is set
            ''',
    'TSX': '''
            Copies the current contents of the stack register into the
            X register and sets the zero and negative flags as
            appropriate.
            Z 	Zero Flag 	Set if X = 0
            N 	Negative Flag 	Set if bit 7 of X is set
            ''',
    'TXA': '''
            Copies the current contents of the X register into
            the accumulator and sets the zero and negative flags
            as appropriate.
            Z 	Zero Flag 	Set if A = 0
            N 	Negative Flag 	Set if bit 7 of A is set
            ''',
    'TXS': '''
            Copies the current contents of the X register into
            the stack register.
            ''',
    'TYA': '''
            Copies the current contents of the Y register into
            the accumulator and sets the zero and negative flags
            as appropriate.
            Z 	Zero Flag 	Set if A = 0
            N 	Negative Flag 	Set if bit 7 of A is set
            ''',
}