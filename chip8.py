import random, time, sys

SCREEN_W = 64
SCREEN_H = 32

RAM_SZ = 4096
N_REGS = 16
STACK_SZ = 16
N_KEYS = 16

START_ADDR = 0x200

FONTSET_SZ = 80
FONTSET = [
    0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
    0x20, 0x60, 0x20, 0x20, 0x70, # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
    0x90, 0x90, 0xF0, 0x10, 0x10, # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
    0xF0, 0x10, 0x20, 0x40, 0x40, # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90, # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
    0xF0, 0x80, 0x80, 0x80, 0xF0, # C
    0xE0, 0x90, 0x90, 0x90, 0xE0, # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
    0xF0, 0x80, 0xF0, 0x80, 0x80, # F
]

# TODO type hints?
class Emu():
    def __init__(self):
        self.pc = START_ADDR # 16 bit int
        self.i = 0 # 16 bit int -- idx into ram
        self.ram = bytearray(RAM_SZ)
        self.ram[:FONTSET_SZ] = FONTSET # TODO do we want fontset sprites...?
        self.screen = [0] * (SCREEN_W * SCREEN_H)
        self.v_reg = [0] * N_REGS
        self.stack = [0] * STACK_SZ
        self.sp = 0
        self.keys = [0] * N_KEYS # TODO 2 byte boolean value?
        self.delay_timer = 0
        self.sound_timer = 0

    def load(self, data: bytearray):
        start = START_ADDR
        end = START_ADDR + len(data)
        self.ram[start:end] = data

    # TODO -- do we need this? can we have stack be empty list, and push/pop onto it?
    def push(self, val):
        self.stack[self.sp] = val
        self.sp += 1

    def pop(self) -> int:
        self.sp -= 1
        return self.stack[self.sp]

    def tick(self):
        op = self.fetch()

        # decode & execute
        self.execute(op)

    def fetch(self) -> int:
        hi = self.ram[self.pc]
        lo = self.ram[self.pc+1]
        op = (hi << 8) | lo
        self.pc += 2
        return op

    def execute(self, op):
        nbl1 = (op & 0xf000) >> 12
        nbl2 = (op & 0x0f00) >> 8
        nbl3 = (op & 0x00f0) >> 4
        nbl4 = (op & 0x000f)

        match (nbl1, nbl2, nbl3, nbl4):
            case (0, 0, 0, 0): # NOP
                return
            case (0, 0, 0xe, 0): # CLS
                self.screen = [0 for _ in self.screen]
            case (0, 0, 0xe, 0xe): # RET
                self.pc = self.pop()
            case (1, _, _, _): # JMP NNN
                self.pc = (op & 0xfff)
            case (2, _, _, _): # CALL NNN
                self.push(self.pc)
                self.pc = (op & 0xfff)
            case (3, _, _, _): # 3XNN, skip next if VX == NN
                x = nbl2
                nn = (op & 0xff)
                if self.v_reg[x] == nn:
                    self.pc += 2
            case (4, _, _, _): # 4Xnn, skip next if VX != NN
                x = nbl2
                nn = (op & 0xff)
                if self.v_reg[x] != nn:
                    self.pc += 2
            case (5, _, _, 0): # 5XY0, skip next if VX == VY
                x, y = nbl2, nbl3
                if self.v_reg[x] == self.v_reg[y]:
                    self.pc += 2
            case (6, _, _, _): # VX = NN
                x = nbl2
                nn = (op & 0xff)
                self.v_reg[x] = nn
            case (7, _, _, _): # VX += NN
                x = nbl2
                nn = (op & 0xff)
                self.v_reg[x] += nn #! DOES NOT CHECK OVERFLOW
            case (8, _, _, 0): # VX = VY
                x, y = nbl2, nbl3
                self.v_reg[x] = self.v_reg[y]
            case (8, _, _, 1): # VX |= VY
                x, y = nbl2, nbl3
                self.v_reg[x] |= self.v_reg[y]
            case (8, _, _, 2): # VX &= VY
                x, y = nbl2, nbl3
                self.v_reg[x] &= self.v_reg[y]
            case (8, _, _, 3): # VX ^= VY
                x, y = nbl2, nbl3
                self.v_reg[x] ^= self.v_reg[y]
            case (8, _, _, 4): # VX += VY, set VF if over/underflow
                x, y = nbl2, nbl3
                # TODO check over/underflow, set vf if carry
                self.v_reg[x] += self.v_reg[y]
            case (8, _, _, 5): # VX -= VY, set VF if over/underflow
                x, y = nbl2, nbl3
                # TODO check over/underflow, set VF if carry
                self.v_reg[x] -= self.v_reg[y]
            case (8, _, _, 6): # VX >> 1, set VF to shifted bit
                x = nbl2
                lsb = self.v_reg[x] & 1
                self.v_reg[x] >>= nbl1
                self.v_reg[0xf] = lsb
            case (8, _, _, 7): # VY - VX
                x, y = nbl2, nbl3
                # TODO check over/underflow, set VF
                self.v_reg[x] = self.v_reg[y] - self.v_reg[x]
            case (8, _, _, 0xe): # VX <<= 1
                x = nbl2
                msb = (self.v_reg[x] >> 7) & 1
                self.v_reg[x] <<= 1
                self.v_reg[0xf] = msb
            case (9, _, _, 0): # 9XY0, skip next if VX != VY
                x, y = nbl2, nbl3
                if self.v_reg[x] != self.v_reg[y]:
                    self.pc += 2
            case (0xa, _, _, _): # ANNN
                nnn = op & 0xfff
                self.i = nnn
            case (0xb, _, _, _): # BNNN, JPM to v0 + NNN
                nnn = op & 0xfff
                self.pc = (self.v_reg[0] + nnn)
            case (0xc, _, _, _): # VX = rand() & NN
                x = nbl2
                nn = (op & 0xff)
                rng = random.randint(0, 255)
                self.v_reg[x] = rng & nn
            case (0xd, _, _, _): # DRAW
                x_coord = self.v_reg[nbl2]
                y_coord = self.v_reg[nbl3]
                n_rows = nbl4
                flipped = False
                for y_line in range(n_rows):
                    addr = self.i + y_line
                    pixels = self.ram[addr]
                    for x_line in range(8):
                        if (pixels & (0b1000_0000 >> x_line)) != 0:
                            x = (x_coord + x_line) % SCREEN_W
                            y = (y_coord + y_line) % SCREEN_H
                            idx = x + SCREEN_W * y
                            flipped |= self.screen[idx]
                            self.screen[idx] ^= True

                self.v_reg[0xf] = 1 if flipped else 0
            case (0xe, _, 9, 0xe): # SKIP KEY PRESS
                x = nbl2
                vc = self.v_reg[x]
                key = self.keys[vx]
                if key:
                    self.pc += 2
            case (0xe, _, 0xa, 0xe): # SKIP KEY NOT PRESS
                x = nbl2
                vc = self.v_reg[x]
                key = self.keys[vx]
                if not key:
                    self.pc += 2
            case (0xf, _, 0, 7): # VX = DT
                x = nbl2
                self.v_reg[x] = self.dt
            case (0xf, _, 0, 0xa): # WAIT KEY, blocking
                x = nbl2
                pressed = False
                for k in self.keys:
                    if k:
                        self.v_reg[x] = k
                        pressed = True
                        break

                if not pressed:
                    self.pc -= 2
            case (0xf, _, 1, 5): # DT = VX
                x = nbl2
                self.dt = self.v_reg[x]
            case (0xf, _, 1, 8): # ST = VX
                x = nbl2
                self.st = self.v_reg[x]
            case (0xf, _, 1, 0xe): # I += VX
                x = nbl2
                self.i = (self.i + self.v_reg[x]) % 2**16
            case (0xf, _, 2, 9): # I = FONT
                x = nbl2
                self.i = self.v_reg[x] * 5
            case (0xf, _, 3, 3): # BCD
                x = nbl2
                vx = self.v_reg[x]
                hundreds = vx // 100
                tens = int((vx / 10) % 10)
                ones = vx % 10
                self.ram[self.i] = hundreds
                self.ram[self.i+1] = tens
                self.ram[self.i+2] = ones
            case (0xf, _, 5, 5): # STORE V0 - VX
                x = nbl2
                for idx in range(x):
                    self.ram[self.i + idx] = self.v_reg[x]
            case (0xf, _, 6, 5): # LOAD V0 - VX
                x = nbl2
                for idx in range(x):
                    self.v_reg[idx] = self.ram[self.i + idx]
            case _: print(f"unimplemented opcode: {op}")


    def _tick_timers(self):
        if self.delay_timer > 0: self.delay_timer -= 1

        if self.sound_timer > 0:
            if self.sound_timer == 1: ... # beep

            self.delay_timer -= 1

    def keypress(self, idx, pressed): self.keys[idx] = pressed
    def get_screen(self): return self.screen
    def __repr__(self): return f"EMU\n\t{self.pc=}\n\t{self.v_reg=}\n\t{self.stack=}\n\t{self.sp=}\n\t{self.i=}"

    def print_screen(self):
        for i in range(SCREEN_H):
            print(''.join(map(str, self.screen[i * SCREEN_W:(i+1)*SCREEN_W])))


if __name__ == "__main__":
    rom_path = sys.argv[1]
    prog = open(rom_path, "rb").read()

    emu = Emu()
    emu.load(prog)

    try:
        while True:
            print("\033[2J\033[H", end="")
            emu.tick()
            emu.print_screen()
            # time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
