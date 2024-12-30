
import sdl2
import sdl2.ext
import sys
import time
from chip8 import Emu

# CHIP-8 Keypad layout:
# 1 2 3 C
# 4 5 6 D
# 7 8 9 E
# A 0 B F

# We'll map it to:
# 1 2 3 4
# Q W E R
# A S D F
# Z X C V

KEYMAP = {
    sdl2.SDLK_1: 0x1, sdl2.SDLK_2: 0x2, sdl2.SDLK_3: 0x3, sdl2.SDLK_4: 0xC,
    sdl2.SDLK_q: 0x4, sdl2.SDLK_w: 0x5, sdl2.SDLK_e: 0x6, sdl2.SDLK_r: 0xD,
    sdl2.SDLK_a: 0x7, sdl2.SDLK_s: 0x8, sdl2.SDLK_d: 0x9, sdl2.SDLK_f: 0xE,
    sdl2.SDLK_z: 0xA, sdl2.SDLK_x: 0x0, sdl2.SDLK_c: 0xB, sdl2.SDLK_v: 0xF,
}

class Chip8Frontend:
    def __init__(self, scale=12):
        self.scale = scale
        self.window_width = 64 * scale
        self.window_height = 32 * scale

        # Initialize SDL2
        sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_AUDIO)
 
        self.window = sdl2.SDL_CreateWindow(
            b"CHIP-8 Emulator",
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            self.window_width,
            self.window_height,
            sdl2.SDL_WINDOW_SHOWN
        )
 
        self.renderer = sdl2.SDL_CreateRenderer(
            self.window,
            -1,
            sdl2.SDL_RENDERER_ACCELERATED
        )
 
        # Create the emulator instance
        self.emu = Emu()

    def load_rom(self, rom_path):
        with open(rom_path, "rb") as f:
            rom_data = f.read()
        self.emu.load(rom_data)

    def draw_screen(self):
        # Clear screen
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(self.renderer)
 
        # Set draw color for pixels
        sdl2.SDL_SetRenderDrawColor(self.renderer, 255, 255, 255, 255)
 
        # Draw pixels
        screen = self.emu.get_screen()
        rect = sdl2.SDL_Rect()
        rect.w = rect.h = self.scale
 
        for y in range(32):
            for x in range(64):
                if screen[y * 64 + x]:
                    rect.x = x * self.scale
                    rect.y = y * self.scale
                    sdl2.SDL_RenderFillRect(self.renderer, rect)

        sdl2.SDL_RenderPresent(self.renderer)

    def handle_input(self):
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                return False
            elif event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    return False
                if event.key.keysym.sym in KEYMAP:
                    self.emu.keypress(KEYMAP[event.key.keysym.sym], 1)
            elif event.type == sdl2.SDL_KEYUP:
                if event.key.keysym.sym in KEYMAP:
                    self.emu.keypress(KEYMAP[event.key.keysym.sym], 0)
        return True

    def run(self):
        running = True
        last_time = time.time()
        timer_counter = 0

        while running:
            # Handle timing
            current_time = time.time()
            delta_time = current_time - last_time
            last_time = current_time

            # Update timers at 60Hz
            timer_counter += delta_time
            if timer_counter >= 1/60:
                self.emu._tick_timers()
                timer_counter = 0

            # Run CPU cycles
            # Aim for roughly 700 instructions per second
            self.emu.tick()

            # Handle input and drawing
            running = self.handle_input()
            self.draw_screen()

            # Cap at ~60 FPS
            time.sleep(1/60)

    def cleanup(self):
        sdl2.SDL_DestroyRenderer(self.renderer)
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

def main():
    if len(sys.argv) != 2:
        print("Usage: python chip8_sdl_frontend.py <rom_file>")
        sys.exit(1)

    frontend = Chip8Frontend()
    try:
        frontend.load_rom(sys.argv[1])
        frontend.run()
    finally:
        frontend.cleanup()

if __name__ == "__main__":
    main()
