import sys
import random
import math
import pygame
from pygame import mixer

# Ensure Python 3.14 compatible style layout (Standard modern Python libraries)
# 60 FPS Vibe Code = ON

pygame.init()
mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# Configuration & Settings
FPS = 60
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 500
GRID_SIZE = 20
COLS = 10
ROWS = 20

# Famicom-inspired Playfield Placement
X_OFFSET = (SCREEN_WIDTH - (COLS * GRID_SIZE)) // 2
Y_OFFSET = (SCREEN_HEIGHT - (ROWS * GRID_SIZE)) // 2

# NES/Famicom Tetris Palettes (Bright Retro Colors)
COLORS = [
    (0, 0, 0),        # 0: Empty
    (31, 103, 226),   # 1: Cyan (I)
    (33, 56, 212),    # 2: Blue (J)
    (227, 140, 32),   # 3: Orange (L)
    (219, 201, 37),   # 4: Yellow (O)
    (54, 184, 46),    # 5: Green (Z)
    (145, 34, 194),   # 6: Purple (T)
    (214, 36, 36)     # 7: Red (S)
]

# Tetromino shapes (Famicom standard layout configurations)
SHAPES = [
    [[1, 1, 1, 1]], # I
    [[2, 0, 0], [2, 2, 2]], # J
    [[0, 0, 3], [3, 3, 3]], # L
    [[4, 4], [4, 4]], # O
    [[0, 5, 5], [5, 5, 0]], # Z
    [[0, 6, 0], [6, 6, 6]], # T
    [[7, 7, 0], [0, 7, 7]]  # S
]

# --- Sound Synthesis Engine ---
# Programmatic implementation of the famous Russian Tetris song ("Korobeiniki")
def generate_square_wave(frequency, duration, volume=0.1):
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    buffer = bytearray()
    
    # Simple 8-bit Famicom style square wave generator
    for i in range(num_samples):
        t = i / sample_rate
        # Alternating sign pulse wave
        val = volume if (math.sin(2 * math.pi * frequency * t) > 0) else -volume
        int_val = int(val * 32767)
        # 16-bit signed stereo format configuration
        try:
            packed = int_val.to_bytes(2, byteorder='little', signed=True)
            buffer.extend(packed) # Left Channel
            buffer.extend(packed) # Right Channel
        except OverflowError:
            buffer.extend(b'\x00\x00\x00\x00')
            
    return mixer.Sound(buffer=buffer)

# Notes mapping to frequencies
NOTES = {
    'E5': 659.25, 'B4': 493.88, 'C5': 523.25, 'D5': 587.33,
    'A4': 440.00, 'G4': 392.00, 'F4': 349.23, 'E4': 329.63,
    'C4': 261.63, 'D4': 293.66
}

# The classic Russian "Duh Duh Duh" Melody Sequence (Note, Duration in fractions of a second)
MELODY = [
    ('E5', 0.4), ('B4', 0.2), ('C5', 0.2), ('D5', 0.4), ('C5', 0.2), ('B4', 0.2),
    ('A4', 0.4), ('A4', 0.2), ('C5', 0.2), ('E5', 0.4), ('D5', 0.2), ('C5', 0.2),
    ('B4', 0.45), ('C5', 0.2), ('D5', 0.4), ('E5', 0.4),
    ('C5', 0.4), ('A4', 0.4), ('A4', 0.4), ('D5', 0.4), ('F4', 0.2), ('A5', 0.4),
    ('G5', 0.2), ('F5', 0.2), ('E5', 0.45), ('C5', 0.2), ('E5', 0.4), ('D5', 0.2),
    ('C5', 0.2), ('B4', 0.4), ('B4', 0.2), ('C5', 0.2), ('D5', 0.4), ('E5', 0.4),
    ('C5', 0.4), ('A4', 0.4), ('A4', 0.4)
]

# Fallback basic frequencies if notes go off chart scale
for idx, frame in enumerate(MELODY):
    note, dur = frame
    if note.startswith('G5'): NOTES['G5'] = 783.99
    if note.startswith('F5'): NOTES['F5'] = 698.46
    if note.startswith('A5'): NOTES['A5'] = 880.00

MENU_ITEMS = ["Play Game", "Controls", "About", "Help", "Exit Game"]

ABOUT_LINES = [
    "TETRIS 4K",
    "Famicom 60 FPS Edition",
    "",
    "Classic blocks. Russian melody.",
    "No external files required.",
    "",
    "Press ESC to return",
]

CONTROLS_LINES = [
    "CONTROLS",
    "",
    "Left / Right  - Move piece",
    "Down          - Soft drop",
    "Up            - Rotate",
    "ESC           - Main menu",
    "",
    "Up / Down     - Menu navigate",
    "Enter / Space - Select",
    "",
    "Press ESC to return",
]

HELP_LINES = [
    "HELP",
    "",
    "Clear lines for 100 pts each.",
    "Game over: Enter or ESC for menu.",
    "",
    "Press ESC to return",
]


class MusicPlayer:
    def __init__(self):
        self.sound_channels = []
        self.current_note_idx = 0
        self.note_timer = 0.0
        self.playing = False
        for note, duration in MELODY:
            freq = NOTES.get(note, 440.0)
            self.sound_channels.append((generate_square_wave(freq, duration), duration))

    def start(self):
        self.playing = True
        self.current_note_idx = 0
        self.note_timer = 0.0

    def stop(self):
        self.playing = False
        mixer.stop()

    def tick(self, dt):
        if not self.playing:
            return
        self.note_timer -= dt
        if self.note_timer <= 0:
            sound, duration = self.sound_channels[self.current_note_idx]
            sound.play()
            self.note_timer = duration
            self.current_note_idx = (self.current_note_idx + 1) % len(self.sound_channels)


class MainMenu:
    def __init__(self, screen, clock, music):
        self.screen = screen
        self.clock = clock
        self.music = music
        self.selected = 0
        self.overlay = None
        self.title_font = pygame.font.SysFont("Courier", 36, bold=True)
        self.menu_font = pygame.font.SysFont("Courier", 22, bold=True)
        self.body_font = pygame.font.SysFont("Courier", 16)

    def draw_menu(self):
        self.screen.fill((10, 10, 25))
        title = self.title_font.render("TETRIS 4K", True, (219, 201, 37))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 90))
        self.screen.blit(title, title_rect)

        for i, label in enumerate(MENU_ITEMS):
            color = (255, 255, 255) if i == self.selected else (140, 140, 160)
            prefix = "> " if i == self.selected else "  "
            text = self.menu_font.render(prefix + label, True, color)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 185 + i * 38))
            self.screen.blit(text, text_rect)

        hint = self.body_font.render("Up/Down  Enter  Esc", True, (120, 120, 140))
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40)))

    def draw_overlay(self, lines):
        self.screen.fill((10, 10, 25))
        panel = pygame.Rect(30, 50, SCREEN_WIDTH - 60, SCREEN_HEIGHT - 100)
        pygame.draw.rect(self.screen, (40, 40, 70), panel, border_radius=4)
        pygame.draw.rect(self.screen, (150, 150, 150), panel, 3, border_radius=4)
        y = panel.top + 24
        for line in lines:
            if line:
                surf = self.body_font.render(line, True, (255, 255, 255))
            else:
                y += 8
                continue
            self.screen.blit(surf, (panel.left + 20, y))
            y += 26

    def handle_menu_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected = (self.selected - 1) % len(MENU_ITEMS)
            elif event.key == pygame.K_DOWN:
                self.selected = (self.selected + 1) % len(MENU_ITEMS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                choice = MENU_ITEMS[self.selected]
                if choice == "Play Game":
                    return "play"
                elif choice == "Controls":
                    self.overlay = "controls"
                elif choice == "About":
                    self.overlay = "about"
                elif choice == "Help":
                    self.overlay = "help"
                elif choice == "Exit Game":
                    return "exit"
        return None

    def run_once(self):
        """One menu session until play or exit. Returns 'play', 'exit', or None on quit window."""
        self.selected = 0
        self.overlay = None
        running = True
        while running:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if self.overlay:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        self.overlay = None
                else:
                    action = self.handle_menu_input(event)
                    if action:
                        return action

            if self.overlay == "controls":
                self.draw_overlay(CONTROLS_LINES)
            elif self.overlay == "about":
                self.draw_overlay(ABOUT_LINES)
            elif self.overlay == "help":
                self.draw_overlay(HELP_LINES)
            else:
                self.draw_menu()

            pygame.display.flip()


class TetrisGame:
    def __init__(self, screen, clock, music):
        self.screen = screen
        self.clock = clock
        self.music = music
        self.reset()

    def reset(self):
        self.grid = [[0] * COLS for _ in range(ROWS)]
        self.score = 0
        self.game_over = False
        self.new_piece()

    def new_piece(self):
        self.current_piece = random.choice(SHAPES)
        self.piece_color = SHAPES.index(self.current_piece) + 1
        self.piece_x = COLS // 2 - len(self.current_piece[0]) // 2
        self.piece_y = 0
        
        if self.check_collision(self.piece_x, self.piece_y, self.current_piece):
            self.game_over = True

    def check_collision(self, nx, ny, piece):
        for r, row in enumerate(piece):
            for c, val in enumerate(row):
                if val:
                    if (nx + c < 0 or nx + c >= COLS or ny + r >= ROWS or 
                        (ny + r >= 0 and self.grid[ny + r][nx + c])):
                        return True
        return False

    def lock_piece(self):
        for r, row in enumerate(self.current_piece):
            for c, val in enumerate(row):
                if val:
                    self.grid[self.piece_y + r][self.piece_x + c] = self.piece_color
        self.clear_lines()
        self.new_piece()

    def clear_lines(self):
        new_grid = [row for row in self.grid if any(val == 0 for val in row)]
        cleared = ROWS - len(new_grid)
        self.score += (cleared * 100)
        while len(new_grid) < ROWS:
            new_grid.insert(0, [0] * COLS)
        self.grid = new_grid

    def rotate_piece(self):
        # Rotate matrix clockwise
        rotated = [list(x) for x in zip(*self.current_piece[::-1])]
        if not self.check_collision(self.piece_x, self.piece_y, rotated):
            self.current_piece = rotated

    def move(self, dx):
        if not self.check_collision(self.piece_x + dx, self.piece_y, self.current_piece):
            self.piece_x += dx

    def drop(self):
        if not self.check_collision(self.piece_x, self.piece_y + 1, self.current_piece):
            self.piece_y += 1
        else:
            self.lock_piece()

    def draw_frame(self, font, extra_lines=None):
        self.screen.fill((10, 10, 25))
        pygame.draw.rect(
            self.screen, (150, 150, 150),
            (X_OFFSET - 4, Y_OFFSET - 4, COLS * GRID_SIZE + 8, ROWS * GRID_SIZE + 8), 4,
        )
        for r in range(ROWS):
            for c in range(COLS):
                val = self.grid[r][c]
                if val:
                    pygame.draw.rect(
                        self.screen, COLORS[val],
                        (X_OFFSET + c * GRID_SIZE, Y_OFFSET + r * GRID_SIZE, GRID_SIZE - 1, GRID_SIZE - 1),
                    )
        for r, row in enumerate(self.current_piece):
            for c, val in enumerate(row):
                if val:
                    pygame.draw.rect(
                        self.screen, COLORS[self.piece_color],
                        (
                            X_OFFSET + (self.piece_x + c) * GRID_SIZE,
                            Y_OFFSET + (self.piece_y + r) * GRID_SIZE,
                            GRID_SIZE - 1, GRID_SIZE - 1,
                        ),
                    )
        score_surf = font.render(f"SCORE: {self.score:06d}", True, (255, 255, 255))
        self.screen.blit(score_surf, (X_OFFSET, Y_OFFSET - 35))
        if extra_lines:
            y = SCREEN_HEIGHT // 2 - 30
            for line, color in extra_lines:
                surf = font.render(line, True, color)
                self.screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH // 2, y)))
                y += 28

    def run(self):
        drop_timer = 0
        drop_interval = 30
        font = pygame.font.SysFont("Courier", 20, bold=True)
        waiting_game_over = False

        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.music.tick(dt)

            if not waiting_game_over:
                drop_timer += 1
                if drop_timer >= drop_interval:
                    self.drop()
                    drop_timer = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "exit"
                if event.type != pygame.KEYDOWN:
                    continue
                if waiting_game_over:
                    if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                        return "menu"
                    continue
                if event.key == pygame.K_ESCAPE:
                    return "menu"
                if event.key == pygame.K_LEFT:
                    self.move(-1)
                elif event.key == pygame.K_RIGHT:
                    self.move(1)
                elif event.key == pygame.K_DOWN:
                    self.drop()
                elif event.key == pygame.K_UP:
                    self.rotate_piece()

            if self.game_over and not waiting_game_over:
                waiting_game_over = True
                print(f"Game Over! Final Score: {self.score}")

            extra = None
            if waiting_game_over:
                extra = [
                    ("GAME OVER", (214, 36, 36)),
                    (f"SCORE: {self.score:06d}", (255, 255, 255)),
                    ("Enter - Main Menu", (219, 201, 37)),
                ]
            self.draw_frame(font, extra)
            pygame.display.flip()


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris 4K - Famicom 60FPS Edition")
    clock = pygame.time.Clock()
    music = MusicPlayer()
    menu = MainMenu(screen, clock, music)

    while True:
        action = menu.run_once()
        if action == "exit":
            break
        if action == "play":
            music.start()
            game = TetrisGame(screen, clock, music)
            result = game.run()
            music.stop()
            if result == "exit":
                break

    pygame.quit()


if __name__ == "__main__":
    main()
