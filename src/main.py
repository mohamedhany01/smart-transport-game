import pygame
import sys
import os
import random
import math
import arabic_reshaper
from bidi.algorithm import get_display

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Configuration & Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (9, 132, 227)
RED = (220, 20, 60)
RED_HOVER = (255, 80, 80)
BG_COLOR_MENU = (135, 206, 235)
BG_COLOR_GAME = (240, 255, 240)
BG_COLOR_WIN = (255, 223, 0)

# Paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = resource_path("fonts")
SOUNDS_DIR = resource_path("sounds")
ASSETS_DIR = resource_path(os.path.join("assets", "in-game"))
SCREENS_DIR = resource_path(os.path.join("assets", "screens"))

# --- Custom Events ---
# حدث خاص سينطلق عندما ينتهي المقطع الصوتي التمهيدي
MUSIC_END_EVENT = pygame.USEREVENT + 1

# --- Helper Functions ---

def get_arabic_text(text):
    """Reshapes and reorders Arabic text for correct display."""
    configuration = {
        'delete_harakat': True,
        'support_ligatures': True,
    }
    reshaper = arabic_reshaper.ArabicReshaper(configuration)
    reshaped_text = reshaper.reshape(text)
    return get_display(reshaped_text)

def load_local_font(filename, size=40):
    """Safely loads a font from the fonts directory."""
    font_path = os.path.join(FONTS_DIR, filename)
    try:
        return pygame.font.Font(font_path, size)
    except Exception as e:
        print(f"[WARN] Font load failed ({filename}): {e}")
        return pygame.font.Font(None, size)

def hsv_to_rgb(h, s, v):
    """Generates rainbow colors."""
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if 0 <= h < 60: r, g, b = c, x, 0
    elif 60 <= h < 120: r, g, b = x, c, 0
    elif 120 <= h < 180: r, g, b = 0, c, x
    elif 180 <= h < 240: r, g, b = 0, x, c
    elif 240 <= h < 300: r, g, b = x, 0, c
    else: r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

# --- Game Classes ---

class DraggableItem:
    """Represents a game object (either a target or a movable transport)."""
    def __init__(self, name, image_filename, type_id, is_target=False, pos=(0, 0), size=(120, 120)):
        self.name = name
        self.type_id = type_id
        self.is_target = is_target
        self.original_pos = pos
        self.is_dragging = False
        self.is_matched = False
        
        # Load and scale image
        img_path = os.path.join(ASSETS_DIR, image_filename)
        try:
            raw_image = pygame.image.load(img_path).convert_alpha()
            self.image = pygame.transform.scale(raw_image, size)
        except Exception as e:
            print(f"[ERROR] Failed to load image {img_path}: {e}")
            self.image = pygame.Surface(size)
            self.image.fill(BLACK if is_target else RED)

        self.rect = self.image.get_rect(topleft=pos)
        self.drag_offset_x = 0
        self.drag_offset_y = 0

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.is_target:
            pygame.draw.rect(surface, (255, 255, 255), self.rect, 3)
            pygame.draw.rect(surface, BLACK, self.rect, 1)

    def start_drag(self, mouse_pos):
        if not self.is_target and not self.is_matched and self.rect.collidepoint(mouse_pos):
            self.is_dragging = True
            self.drag_offset_x = self.rect.x - mouse_pos[0]
            self.drag_offset_y = self.rect.y - mouse_pos[1]
            return True
        return False

    def update_drag(self, mouse_pos):
        if self.is_dragging:
            self.rect.x = mouse_pos[0] + self.drag_offset_x
            self.rect.y = mouse_pos[1] + self.drag_offset_y

    def stop_drag(self):
        self.is_dragging = False

    def return_to_start(self):
        self.rect.topleft = self.original_pos

class TransportGame:
    """Main Game Manager Class."""
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("لعبة وسائل المواصلات")
        self.clock = pygame.time.Clock()
        self.state = "MENU" # MENU, GAME, WIN

        # Fonts
        self.font_main = load_local_font("NotoSansArabic-Bold.ttf", 40)
        self.font_title = load_local_font("NotoSansArabic-Black.ttf", 30) # يمكنك زيادة هذا الرقم لتكبير العنوان
        self.font_ui = load_local_font("NotoSansArabic-Regular.ttf", 30)
        
        # Sounds
        self.snd_correct = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "select-right.mp3"))
        self.snd_wrong = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, "select-wrong.mp3"))
        self.snd_win_path = os.path.join(SOUNDS_DIR, "yay-win.mp3")

        # Background Images
        self.bg_menu = self.load_background("main.png")
        self.bg_game = self.load_background("in-game.png")
        self.bg_win = self.load_background("win.png")

        # Game Objects
        self.targets = []
        self.movables = []
        self.hue = 0
        
        # متغير لتخزين اسم الموسيقى التالية التي يجب تشغيلها
        self.next_music_track = None

        # Start with Menu Intro Sequence
        self.play_music_sequence("main-screen-intro.mp3", "main-intro.mp3")

    def load_background(self, filename):
        path = os.path.join(SCREENS_DIR, filename)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert()
                return pygame.transform.scale(img, (WIDTH, HEIGHT))
            except Exception as e:
                print(f"[ERROR] Failed to load background {filename}: {e}")
        return None

    def play_music_sequence(self, intro_file, loop_file):
        """
        تقوم بتشغيل ملف المقدمة (intro) مرة واحدة.
        وعند انتهائه سيقوم النظام تلقائياً بتشغيل ملف (loop) بشكل متكرر.
        """
        intro_path = os.path.join(SOUNDS_DIR, intro_file)
        
        if os.path.exists(intro_path):
            # 1. إيقاف أي موسيقى سابقة
            pygame.mixer.music.stop()
            # 2. تحميل المقدمة
            pygame.mixer.music.load(intro_path)
            # 3. تشغيل المقدمة مرة واحدة (0 تعني مرة واحدة)
            pygame.mixer.music.play(0)
            print(f"[AUDIO] Playing INTRO: {intro_file}")
            
            # 4. نخبر Pygame أن يرسل لنا حدثاً عندما ينتهي هذا المقطع
            pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
            
            # 5. نحفظ اسم الملف الذي نريد تشغيله لاحقاً
            self.next_music_track = loop_file
        else:
            # إذا لم يوجد ملف المقدمة، نشغل الملف الأساسي فوراً
            print(f"[WARN] Intro not found. Skipping to loop.")
            self.play_music_loop(loop_file)

    def play_music_loop(self, filename):
        """تقوم بتشغيل ملف صوتي في حلقة لا نهائية فوراً"""
        path = os.path.join(SOUNDS_DIR, filename)
        if os.path.exists(path):
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1) # -1 تعني تكرار لانهائي
            # نلغي أي أحداث انتظار لأننا بدأنا التكرار بالفعل
            pygame.mixer.music.set_endevent() 
            print(f"[AUDIO] Playing LOOP: {filename}")

    def start_new_game(self):
        self.state = "GAME"
        # تشغيل تسلسل الموسيقى الخاص باللعبة (Intro -> Loop)
        self.play_music_sequence("in-game-screen-intro.mp3", "in-game.mp3")
        
        # Data & Logic setup
        movable_data = [
            ("Car", "car.png", "road"),
            ("Ship", "ship.png", "sea"),
            ("Plane", "plane.png", "sky")
        ]
        target_data = [
            ("Road", "road.png", "road"),
            ("Sea", "sea.png", "sea"),
            ("Sky", "sky.png", "sky")
        ]

        random.shuffle(movable_data)
        random.shuffle(target_data)

        # Targets (Horizontal - Bottom)
        self.targets = []
        start_x = 80     
        fixed_y = 380     
        spacing_x = 240   
        for i, (name, img, type_id) in enumerate(target_data):
            pos_x = start_x + (i * spacing_x)
            t = DraggableItem(name, img, type_id, is_target=True, pos=(pos_x, fixed_y))
            self.targets.append(t)

        # Movables (Horizontal - Top)
        self.movables = []
        start_x = 80      
        fixed_y = 180     
        spacing_x = 240   
        for i, (name, img, type_id) in enumerate(movable_data):
            pos_x = start_x + (i * spacing_x)
            m = DraggableItem(name, img, type_id, is_target=False, pos=(pos_x, fixed_y))
            self.movables.append(m)

    def check_win_condition(self):
        if all(m.is_matched for m in self.movables):
            print("[GAME] Player Won!")
            self.state = "WIN"
            pygame.mixer.music.stop()
            # عند الفوز نشغل ملف الفوز مرة واحدة ونلغي الـ Loop
            pygame.mixer.music.load(self.snd_win_path)
            pygame.mixer.music.play(0)
            pygame.mixer.music.set_endevent() # لا نريد شيئاً بعد موسيقى الفوز

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # --- التعامل مع انتهاء المقاطع الصوتية ---
            if event.type == MUSIC_END_EVENT:
                print("[AUDIO] Music track ended.")
                # إذا كان لدينا ملف "تالٍ" محفوظ في الطابور، قم بتشغيله الآن كـ Loop
                if self.next_music_track:
                    self.play_music_loop(self.next_music_track)
                    self.next_music_track = None # تفريغ المتغير

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.state == "MENU":
                        self._handle_menu_click(mouse_pos)
                    elif self.state == "GAME":
                        if pygame.Rect(10, 10, 100, 50).collidepoint(mouse_pos):
                            self.state = "MENU"
                            # عند العودة للقائمة، نعيد تشغيل مقدمة القائمة
                            self.play_music_sequence("main-screen-intro.mp3", "main-intro.mp3")
                        else:
                            for m in self.movables:
                                if m.start_drag(mouse_pos):
                                    break 
                    elif self.state == "WIN":
                        self.state = "MENU"
                        self.play_music_sequence("main-screen-intro.mp3", "main-intro.mp3")

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.state == "GAME":
                    self._handle_drop_logic()

    def _handle_menu_click(self, mouse_pos):
        play_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 60, 300, 80)
        exit_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 60)
        
        if play_rect.collidepoint(mouse_pos):
            self.start_new_game()
        elif exit_rect.collidepoint(mouse_pos):
            pygame.quit()
            sys.exit()

    def _handle_drop_logic(self):
        for m in self.movables:
            if m.is_dragging:
                m.stop_drag()
                
                dist_x = m.rect.x - m.original_pos[0]
                dist_y = m.rect.y - m.original_pos[1]
                distance = math.hypot(dist_x, dist_y)
                
                if distance < 20:
                    m.return_to_start()
                    return

                found_target = False
                for t in self.targets:
                    if m.rect.colliderect(t.rect):
                        found_target = True
                        if m.type_id == t.type_id:
                            m.rect.center = t.rect.center
                            m.is_matched = True
                            self.snd_correct.play()
                            self.check_win_condition()
                        else:
                            m.return_to_start()
                            self.snd_wrong.play()
                        break 
                
                if not found_target:
                    m.return_to_start()
                    self.snd_wrong.play()

    def update(self):
        if self.state == "GAME":
            mouse_pos = pygame.mouse.get_pos()
            for m in self.movables:
                m.update_drag(mouse_pos)

    def draw(self):
        if self.state == "MENU":
            self.draw_menu()
        elif self.state == "GAME":
            self.draw_game()
        elif self.state == "WIN":
            self.draw_win()
        pygame.display.flip()

    def draw_menu(self):
        if self.bg_menu:
            self.screen.blit(self.bg_menu, (0, 0))
        else:
            self.screen.fill(BG_COLOR_MENU)

        self.hue = (self.hue + 2) % 360
        rainbow = hsv_to_rgb(self.hue, 1, 1)

        title_shadow = self.font_title.render(get_arabic_text("لعبة وسائل المواصلات"), True, BLACK)
        shadow_rect = title_shadow.get_rect(center=(WIDTH//2 + 3, 120 + 53))
        self.screen.blit(title_shadow, shadow_rect)
        
        title_text = self.font_title.render(get_arabic_text("لعبة وسائل المواصلات"), True, BLUE)
        title_rect = title_text.get_rect(center=(WIDTH//2, 120 + 50))
        self.screen.blit(title_text, title_rect)

        # Buttons
        play_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 60, 300, 80)
        glow_rect = play_rect.inflate(10, 10)
        pygame.draw.rect(self.screen, [c//2 for c in rainbow], glow_rect, border_radius=20)
        pygame.draw.rect(self.screen, rainbow, play_rect, border_radius=15)
        txt = self.font_main.render(get_arabic_text("Play"), True, WHITE)
        self.screen.blit(txt, txt.get_rect(center=play_rect.center))

        exit_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 50, 200, 60)
        mouse_pos = pygame.mouse.get_pos()
        col = RED_HOVER if exit_rect.collidepoint(mouse_pos) else RED
        pygame.draw.rect(self.screen, col, exit_rect, border_radius=15)
        txt = self.font_main.render(get_arabic_text("Exit"), True, WHITE)
        self.screen.blit(txt, txt.get_rect(center=exit_rect.center))

    def draw_game(self):
        if self.bg_game:
            self.screen.blit(self.bg_game, (0, 0))
        else:
            self.screen.fill(BG_COLOR_GAME)
        
        instr = self.font_ui.render(get_arabic_text("ضع كل وسيلة مواصلات بمكانها الصحيح"), True, BLACK)
        bg_rect = instr.get_rect(topleft=(WIDTH//2 - instr.get_width()//2, 80))
        pygame.draw.rect(self.screen, (255, 255, 255, 180), bg_rect.inflate(20, 10), border_radius=10)
        self.screen.blit(instr, bg_rect)

        back_rect = pygame.Rect(10, 10, 100, 50)
        pygame.draw.rect(self.screen, RED, back_rect, border_radius=10)
        txt = self.font_ui.render(get_arabic_text("رجوع"), True, WHITE)
        self.screen.blit(txt, txt.get_rect(center=back_rect.center))

        for t in self.targets:
            t.draw(self.screen)
        for m in self.movables:
            if not m.is_dragging:
                m.draw(self.screen)
        for m in self.movables:
            if m.is_dragging:
                m.draw(self.screen)

    def draw_win(self):
        if self.bg_win:
            self.screen.blit(self.bg_win, (0, 0))
        else:
            self.screen.fill(BG_COLOR_WIN)
        
        txt_win = self.font_title.render(get_arabic_text("ممتاز! إجابة صحيحة"), True, BLACK)
        win_rect = txt_win.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        pygame.draw.rect(self.screen, (255, 255, 255, 200), win_rect.inflate(40, 20), border_radius=20)
        self.screen.blit(txt_win, win_rect)
        
        txt_sub = self.font_ui.render(get_arabic_text("اضغط للعودة للقائمة"), True, (50, 50, 50))
        sub_rect = txt_sub.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
        pygame.draw.rect(self.screen, (255, 255, 255, 200), sub_rect.inflate(20, 10), border_radius=10)
        self.screen.blit(txt_sub, sub_rect)

if __name__ == "__main__":
    game = TransportGame()
    game.run()
