import pygame
import os
from unit import Swordsman, Archer, Arrow
import random

# Initialize Pygame
pygame.init()

# Set up the display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Battle Swap")

# Load the swordsman and archer sprite sheets
swordsman_path = os.path.join("assets", "MinifolksHumans", "Without Outline", "MiniSwordMan.png")
swordsman_sheet = pygame.image.load(swordsman_path).convert_alpha()
archer_path = os.path.join("assets", "MinifolksHumans", "Without Outline", "MiniArcherMan.png")
archer_sheet = pygame.image.load(archer_path).convert_alpha()

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (220, 220, 220)
GREEN = (34, 100, 34)  # Forest Green color

class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.is_hovered = False

    def draw(self, screen):
        color = LIGHT_GRAY if self.is_hovered else GRAY
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        font = pygame.font.Font(None, 24)
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()

class Checkbox:
    def __init__(self, x, y, text):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.text = text
        self.checked = False
        self.font = pygame.font.Font(None, 24)

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        if self.checked:
            pygame.draw.line(screen, BLACK, (self.rect.left + 4, self.rect.centery), (self.rect.centerx, self.rect.bottom - 4), 2)
            pygame.draw.line(screen, BLACK, (self.rect.centerx, self.rect.bottom - 4), (self.rect.right - 4, self.rect.top + 4), 2)
        text_surface = self.font.render(self.text, True, BLACK)
        screen.blit(text_surface, (self.rect.right + 5, self.rect.top))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked

class Game:
    def __init__(self):
        self.units = []
        self.setup_armies()
        self.speed_multiplier = 1
        self.setup_speed_buttons()
        self.time_accumulator = 0
        self.debug_checkbox = Checkbox(10, SCREEN_HEIGHT - 40, "Debug Mode")
        self.game_over = False
        self.winner = None
        self.restart_button = Button(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 + 50, 100, 40, "Restart", self.restart)

    def setup_armies(self):
        # Set up the formation
        num_units = 4

        # Define battle area (full screen with some padding)
        padding = 50
        battle_left = padding
        battle_right = SCREEN_WIDTH - padding
        battle_top = padding
        battle_bottom = SCREEN_HEIGHT - padding

        # Calculate the middle of the screen
        middle_x = SCREEN_WIDTH // 2

        # Unit size
        unit_size = 32 * 4  # 32 pixels * 4 scale

        for _ in range(num_units):
            ally_x = random.randint(battle_left + unit_size // 2, middle_x - padding - unit_size // 2)
            ally_y = random.randint(battle_top + unit_size, battle_bottom)
            enemy_x = random.randint(middle_x + padding + unit_size // 2, battle_right - unit_size // 2)
            enemy_y = random.randint(battle_top + unit_size, battle_bottom)

            # Randomly choose between swordsman and archer
            if random.choice([True, False]):
                ally_unit = Swordsman(ally_x, ally_y, swordsman_sheet, is_enemy=False)
                enemy_unit = Swordsman(enemy_x, enemy_y, swordsman_sheet, is_enemy=True)
            else:
                ally_unit = Archer(ally_x, ally_y, archer_sheet, is_enemy=False)
                enemy_unit = Archer(enemy_x, enemy_y, archer_sheet, is_enemy=True)

            self.units.extend([ally_unit, enemy_unit])

    def setup_speed_buttons(self):
        button_width = 80
        button_height = 30
        button_margin = 10
        total_width = button_width * 6 + button_margin * 5
        start_x = (SCREEN_WIDTH - total_width) // 2
        y = SCREEN_HEIGHT - button_height - 10

        self.speed_buttons = [
            Button(start_x, y, button_width, button_height, "Paused", lambda: self.set_speed(0)),
            Button(start_x + (button_width + button_margin), y, button_width, button_height, "0.25x", lambda: self.set_speed(0.25)),
            Button(start_x + (button_width + button_margin) * 2, y, button_width, button_height, "0.5x", lambda: self.set_speed(0.5)),
            Button(start_x + (button_width + button_margin) * 3, y, button_width, button_height, "1x", lambda: self.set_speed(1)),
            Button(start_x + (button_width + button_margin) * 4, y, button_width, button_height, "2x", lambda: self.set_speed(2)),
            Button(start_x + (button_width + button_margin) * 5, y, button_width, button_height, "4x", lambda: self.set_speed(4))
        ]

    def set_speed(self, speed):
        self.speed_multiplier = speed

    def update(self, dt):
        if self.game_over:
            return True

        if self.speed_multiplier == 0:
            return True

        self.time_accumulator += dt * self.speed_multiplier
        update_interval = 1000 / 60  # 60 FPS

        while self.time_accumulator >= update_interval:
            for unit in self.units:
                unit.update(self)
            
            # Remove dead units
            self.units = [unit for unit in self.units if not unit.is_dead or unit.current_frame < len(unit.animation_frames['die']) - 1]

            # Update all arrows
            all_arrows = [arrow for unit in self.units if isinstance(unit, Archer) for arrow in unit.arrows]
            for arrow in all_arrows:
                arrow.update()

            # Check for game over
            allies = [unit for unit in self.units if not unit.is_enemy]
            enemies = [unit for unit in self.units if unit.is_enemy]
            
            if not allies:
                self.game_over = True
                self.winner = "Enemy"
            elif not enemies:
                self.game_over = True
                self.winner = "Ally"
        
            self.time_accumulator -= update_interval
        
        return True

    def draw(self, screen):
        screen.fill(GREEN)
        for unit in self.units:
            unit.draw(screen)
            if self.debug_checkbox.checked:
                # Draw unit center point (now at the center of the hitbox)
                pygame.draw.circle(screen, (255, 0, 0), (int(unit.x), int(unit.y)), 3)
                
                # Draw unit hitbox
                hitbox = pygame.Rect(
                    unit.x - unit.hitbox_width // 2,
                    unit.y - unit.hitbox_height // 2,  # Adjust this line
                    unit.hitbox_width,
                    unit.hitbox_height
                )
                pygame.draw.rect(screen, (255, 0, 0), hitbox, 2)
        
        for unit in self.units:
            if isinstance(unit, Archer):
                for arrow in unit.arrows:
                    arrow.draw(screen)
                    if self.debug_checkbox.checked:
                        # Draw arrow center point
                        pygame.draw.circle(screen, (0, 0, 255), (int(arrow.x), int(arrow.y)), 3)
                        
                        # Draw arrow bounding box
                        arrow_bbox = arrow.image.get_rect(center=(arrow.x, arrow.y))
                        pygame.draw.rect(screen, (0, 0, 255), arrow_bbox, 2)
        
        for button in self.speed_buttons:
            button.draw(screen)
        self.debug_checkbox.draw(screen)

        if self.game_over:
            font = pygame.font.Font(None, 74)
            text = font.render(f"{self.winner} team wins!", True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(text, text_rect)
            self.restart_button.draw(screen)

        pygame.display.flip()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                return False
            for button in self.speed_buttons:
                button.handle_event(event)
            self.debug_checkbox.handle_event(event)
            if self.game_over:
                self.restart_button.handle_event(event)
        return True

    def restart(self):
        self.__init__()  # Reset the game state

# Create game instance
game = Game()

# Set up the game clock
clock = pygame.time.Clock()

# Main game loop
running = True
while running:
    # Calculate delta time
    dt = clock.tick(60)

    # Handle events
    events = pygame.event.get()
    running = game.handle_events(events)

    # Update game state
    game.update(dt)

    # Draw
    game.draw(screen)

# Quit the game
pygame.quit()