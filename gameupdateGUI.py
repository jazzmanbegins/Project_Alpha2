import pygame
import random
import os
import sys
from pygame import gfxdraw

# ---------------- SETTINGS ----------------
WIDTH, HEIGHT = 1200, 950
FPS = 60

# Assets
ASSET_FOLDER = "assets"
IMG_FOLDER = os.path.join(ASSET_FOLDER, "images")
SOUND_FOLDER = os.path.join(ASSET_FOLDER, "sounds")

CARD_BACK = "back.png"
BACKGROUND_IMG = "room.png"

CARD_SIZE = (150, 150)
ROWS, COLS = 4, 6
CARD_SPACING = 10
START_X, START_Y = 50, 150

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (50, 50, 50)
BUTTON_BG = (39, 114, 201)
BUTTON_HOVER = (27, 96, 153)

# ---------------- INIT ----------------
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Street Fighter Memory Game")
clock = pygame.time.Clock()

# ---------------- LOAD BACKGROUND ----------------
bg_path = os.path.join(IMG_FOLDER, BACKGROUND_IMG)
if not os.path.exists(bg_path):
    print("Missing background image:", bg_path)
    sys.exit()
background = pygame.image.load(bg_path).convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# ---------------- LOAD SOUNDS ----------------
def load_sound(name):
    for ext in [".wav", ".mp3"]:
        path = os.path.join(SOUND_FOLDER, name + ext)
        if os.path.exists(path):
            return pygame.mixer.Sound(path) if ext == ".wav" else path
    return None

sounds = {
    "click": load_sound("click"),
    "match": load_sound("match"),
    "wrong": load_sound("wrong"),
    "win": load_sound("win")
}

def play_sound(name):
    sound = sounds.get(name)
    if sound:
        try:
            if isinstance(sound, str):
                pygame.mixer.music.load(sound)
                pygame.mixer.music.play()
            else:
                sound.play()
        except:
            pass

# ---------------- LOAD IMAGES ----------------
def load_image(name, size=CARD_SIZE):
    path = os.path.join(IMG_FOLDER, name)
    if not os.path.exists(path):
        print("Missing image:", path)
        sys.exit()
    img = pygame.image.load(path).convert_alpha()
    img = pygame.transform.scale(img, size)
    return img

# Load card back
back_img = load_image(CARD_BACK)

# Load card faces
card_files = [f for f in os.listdir(IMG_FOLDER) if f.endswith(".png") and f != CARD_BACK and f != BACKGROUND_IMG]
if len(card_files) < 12:
    print("Need at least 12 card images in:", IMG_FOLDER)
    sys.exit()
card_files = card_files[:12]
card_images = [load_image(f) for f in card_files]

# ---------------- CARD CLASS ----------------
class Card:
    def __init__(self, image, x, y):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.flipped = False
        self.matched = False
        self.temp_flipped = False

    def draw(self, surface):
        if self.matched or self.flipped or self.temp_flipped:
            surface.blit(self.image, self.rect)
        else:
            surface.blit(back_img, self.rect)

# ---------------- BUTTON CLASS ----------------
class Button:
    def __init__(self, text, x, y, w, h, callback):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.hover = False
        self.font = pygame.font.SysFont("Arial", 28, bold=True)

    def draw(self, surface):
        color = BUTTON_HOVER if self.hover else BUTTON_BG
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        text_surf = self.font.render(self.text, True, WHITE)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()

# ---------------- GAME CLASS ----------------
class MemoryGame:
    def __init__(self):
        self.cards = []
        self.flipped_cards = []
        self.attempts = 0
        self.matches = 0
        self.font = pygame.font.SysFont("Arial", 32, bold=True)
        self.create_board()
        self.reset_button = Button("Reset Game", WIDTH-200, 20, 160, 50, self.reset_game)
        self.popup_open = False

        self.delay_timer = 0
        self.delay_active = False

    def create_board(self):
      self.cards = []
      images = card_images * 2
      random.shuffle(images)
      idx = 0

      # คำนวณ START_X ให้กลุ่มการ์ดอยู่กลาง
      total_width = COLS * CARD_SIZE[0] + (COLS - 1) * CARD_SPACING
      start_x = (WIDTH - total_width) // 2
      start_y = START_Y  # หรือปรับกลางแนวตั้งตามต้องการ

      for row in range(ROWS):
          for col in range(COLS):
              x = start_x + col * (CARD_SIZE[0] + CARD_SPACING)
              y = start_y + row * (CARD_SIZE[1] + CARD_SPACING)
              self.cards.append(Card(images[idx], x, y))
              idx += 1

      self.flipped_cards = []
      self.attempts = 0
      self.matches = 0
      self.delay_timer = 0
      self.delay_active = False
      for card in self.cards:
          card.flipped = False
          card.temp_flipped = False
          card.matched = False
      self.popup_open = False


    def draw(self, surface):
        surface.blit(background, (0, 0))
        for card in self.cards:
            card.draw(surface)

        # HUD
        attempts_text = self.font.render(f"Attempts: {self.attempts}", True, WHITE)
        matches_text = self.font.render(f"Matches: {self.matches}", True, WHITE)
        surface.blit(attempts_text, (20, 20))
        surface.blit(matches_text, (20, 60))

        # Reset button
        self.reset_button.draw(surface)

        # Win popup
        if self.popup_open:
            self.draw_popup(surface)

    def draw_popup(self, surface):
      w, h = 450, 300
      popup_rect = pygame.Rect((WIDTH - w)//2, (HEIGHT - h)//2, w, h)
      pygame.draw.rect(surface, GRAY, popup_rect, border_radius=12)
      pygame.draw.rect(surface, GRAY, popup_rect, 1, border_radius=12)  # ลดความหนาเส้นจาก 4 → 2

      # ฟอนต์สำหรับแต่ละบรรทัด
      win_font = pygame.font.SysFont("Arial", 40, bold=True)      # "You Win!" ใหญ่ขึ้น
      info_font = pygame.font.SysFont("Arial", 30, bold=True)     # ข้อมูล Attempts/Matches

      # ข้อความ
      lines = [
          ("You Win!", win_font),
          (f"Attempts: {self.attempts}", info_font),
          (f"Matches: {self.matches}", info_font)
      ]
      line_spacing = 50
      start_y = (HEIGHT - h)//2 + 50

      for i, (text, font) in enumerate(lines):
          txt_surf = font.render(text, True, WHITE)
          txt_rect = txt_surf.get_rect(center=(WIDTH//2, start_y + i*line_spacing))
          surface.blit(txt_surf, txt_rect)

      # ปุ่ม Play Again
      btn_w, btn_h = 180, 50
      btn_x = WIDTH//2 - btn_w//2
      btn_y = start_y + len(lines)*line_spacing - 10  # เลื่อนปุ่มขึ้นเล็กน้อย
      self.popup_reset_button = Button("Play Again", btn_x, btn_y, btn_w, btn_h, self.reset_game)
      self.popup_reset_button.draw(surface)


    def handle_event(self, event):
        self.reset_button.handle_event(event)
        if self.popup_open:
            self.popup_reset_button.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and not self.popup_open:
            for card in self.cards:
                if card.rect.collidepoint(event.pos) and not card.flipped and not card.matched and not self.delay_active:
                    card.flipped = True
                    self.flipped_cards.append(card)
                    play_sound("click")
                    if len(self.flipped_cards) == 2:
                        self.delay_active = True
                        self.delay_timer = pygame.time.get_ticks()
                    break

    def update(self):
        if self.delay_active:
            current = pygame.time.get_ticks()
            if current - self.delay_timer >= 800:
                c1, c2 = self.flipped_cards
                if c1.image == c2.image:
                    c1.matched = True
                    c2.matched = True
                    self.matches += 1
                    play_sound("match")
                else:
                    c1.flipped = False
                    c2.flipped = False
                    play_sound("wrong")
                self.flipped_cards = []
                self.attempts += 1
                self.delay_active = False

        # ชนะเกม
        if self.matches == len(self.cards)//2 and not self.popup_open:
            play_sound("win")
            self.popup_open = True

    def reset_game(self):
        self.create_board()

# ---------------- MAIN LOOP ----------------
def main():
    game = MemoryGame()
    running = True

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)

        game.update()
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
