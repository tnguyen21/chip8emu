import sys


opcode_handlers = {
    0x00E0: "CLS",         # Clear screen
    0x00EE: "RET",         # Return from subroutine
}

# Dynamic opcode ranges are handled programmatically
def decode_opcode(opcode):
    if opcode & 0xF000 == 0x1000:
        return f"JP 0x{opcode & 0x0FFF:03X}"   # Jump to address 0xNNN
    elif opcode & 0xF000 == 0x2000:
        return f"CALL 0x{opcode & 0x0FFF:03X}" # Call subroutine at 0xNNN
    elif opcode & 0xF000 == 0x3000:
        return f"SE V{(opcode & 0x0F00) >> 8:X}, 0x{opcode & 0x00FF:02X}" # Skip if VX == NN
    elif opcode & 0xF000 == 0x4000:
        return f"SNE V{(opcode & 0x0F00) >> 8:X}, 0x{opcode & 0x00FF:02X}" # Skip if VX != NN
    elif opcode & 0xF000 == 0x5000:
        return f"SE V{(opcode & 0x0F00) >> 8:X}, V{(opcode & 0x00F0) >> 4:X}" # Skip if VX == VY
    elif opcode & 0xF000 == 0x6000:
        return f"LD V{(opcode & 0x0F00) >> 8:X}, 0x{opcode & 0x00FF:02X}" # VX = NN
    elif opcode & 0xF000 == 0x7000:
        return f"ADD V{(opcode & 0x0F00) >> 8:X}, 0x{opcode & 0x00FF:02X}" # VX += NN
    elif opcode & 0xF00F == 0x8000:
        return f"LD V{(opcode & 0x0F00) >> 8:X}, V{(opcode & 0x00F0) >> 4:X}" # VX = VY
    elif opcode & 0xF00F == 0x8001:
        return f"OR V{(opcode & 0x0F00) >> 8:X}, V{(opcode & 0x00F0) >> 4:X}" # VX |= VY
    elif opcode & 0xF00F == 0x8002:
        return f"AND V{(opcode & 0x0F00) >> 8:X}, V{(opcode & 0x00F0) >> 4:X}" # VX &= VY
    elif opcode & 0xF00F == 0x8003:
        return f"XOR V{(opcode & 0x0F00) >> 8:X}, V{(opcode & 0x00F0) >> 4:X}" # VX ^= VY
    elif opcode & 0xF00F == 0x8004:
        return f"ADD V{(opcode & 0x0F00) >> 8:X}, V{(opcode & 0x00F0) >> 4:X}" # VX += VY, carry
    elif opcode & 0xF00F == 0x8005:
        return f"SUB V{(opcode & 0x0F00) >> 8:X}, V{(opcode & 0x00F0) >> 4:X}" # VX -= VY, borrow
    elif opcode & 0xF00F == 0x8006:
        return f"SHR V{(opcode & 0x0F00) >> 8:X}" # VX >>= 1
    elif opcode & 0xF00F == 0x8007:
        return f"SUBN V{(opcode & 0x0F00) >> 8:X}, V{(opcode & 0x00F0) >> 4:X}" # VX = VY - VX
    elif opcode & 0xF00F == 0x800E:
        return f"SHL V{(opcode & 0x0F00) >> 8:X}" # VX <<= 1
    elif opcode & 0xF000 == 0x9000:
        return f"SNE V{(opcode & 0x0F00) >> 8:X}, V{(opcode & 0x00F0) >> 4:X}" # Skip if VX != VY
    elif opcode & 0xF000 == 0xA000:
        return f"LD I, 0x{opcode & 0x0FFF:03X}" # I = 0xNNN
    elif opcode & 0xF000 == 0xB000:
        return f"JP V0, 0x{opcode & 0x0FFF:03X}" # Jump to V0 + NNN
    elif opcode & 0xF000 == 0xC000:
        return f"RND V{(opcode & 0x0F00) >> 8:X}, 0x{opcode & 0x00FF:02X}" # VX = rand() & NN
    elif opcode & 0xF000 == 0xD000:
        return f"DRW V{(opcode & 0x0F00) >> 8:X}, V{(opcode & 0x00F0) >> 4:X}, {opcode & 0x000F}" # Draw sprite
    elif opcode & 0xF0FF == 0xE09E:
        return f"SKP V{(opcode & 0x0F00) >> 8:X}" # Skip if key in VX pressed
    elif opcode & 0xF0FF == 0xE0A1:
        return f"SKNP V{(opcode & 0x0F00) >> 8:X}" # Skip if key in VX not pressed
    elif opcode & 0xF0FF == 0xF007:
        return f"LD V{(opcode & 0x0F00) >> 8:X}, DT" # VX = delay timer
    elif opcode & 0xF0FF == 0xF00A:
        return f"LD V{(opcode & 0x0F00) >> 8:X}, K" # Wait for key press
    elif opcode & 0xF0FF == 0xF015:
        return f"LD DT, V{(opcode & 0x0F00) >> 8:X}" # Delay timer = VX
    elif opcode & 0xF0FF == 0xF018:
        return f"LD ST, V{(opcode & 0x0F00) >> 8:X}" # Sound timer = VX
    elif opcode & 0xF0FF == 0xF01E:
        return f"ADD I, V{(opcode & 0x0F00) >> 8:X}" # I += VX
    elif opcode & 0xF0FF == 0xF029:
        return f"LD F, V{(opcode & 0x0F00) >> 8:X}" # Set I to font character in VX
    elif opcode & 0xF0FF == 0xF033:
        return f"LD B, V{(opcode & 0x0F00) >> 8:X}" # BCD encoding of VX to I
    elif opcode & 0xF0FF == 0xF055:
        return f"LD [I], V0-V{(opcode & 0x0F00) >> 8:X}" # Store V0-VX at I
    elif opcode & 0xF0FF == 0xF065:
        return f"LD V0-V{(opcode & 0x0F00) >> 8:X}, [I]" # Load I into V0-VX
    else:
        return f"UNKNOWN {opcode:04X}" # Unknown opcode

def disassemble_chip8_rom(rom_path, output_path):
    """
    Disassembles a Chip-8 game ROM into human-readable assembly instructions.

    :param rom_path: Path to the Chip-8 ROM file.
    :param output_path: Path to save the disassembled output.
    """
    with open(rom_path, 'rb') as rom:
        rom_data = rom.read()

    disassembled_code = []

    # Iterate through the ROM, two bytes at a time
    pc = 0x200  # Chip-8 programs start at memory address 0x200
    for i in range(0, len(rom_data), 2):
        opcode = (rom_data[i] << 8) | rom_data[i + 1]
        disassembled_code.append(f"{pc:04X}: {decode_opcode(opcode)}")
        pc += 2

    with open(output_path, 'w') as output_file:
        output_file.write('\n'.join(disassembled_code))
        output_file.write('\n')

if __name__ == "__main__":
    rom_path = sys.argv[1]
    output_path = "disassembled_chip8.asm"
    disassemble_chip8_rom(rom_path, output_path)

