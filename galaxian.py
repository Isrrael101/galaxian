import pygame
import random
import sys
import math
import os
import numpy as np

# Initialize Pygame
pygame.init()
pygame.mixer.init(44100, -16, 2, 2048)

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Sound generation functions
def generate_shoot_sound():
    sample_rate = 44100
    duration = 0.1  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    frequency = 880  # Hz (higher pitch for shooting)
    # Generate stereo sound
    sound_array = np.zeros((len(t), 2))
    sound_array[:, 0] = np.sin(2 * np.pi * frequency * t) * 0.5  # Left channel
    sound_array[:, 1] = sound_array[:, 0]  # Right channel (same as left)
    sound_array = (sound_array * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(sound_array)

def generate_explosion_sound():
    sample_rate = 44100
    duration = 0.3  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # Create a descending frequency sweep
    frequency = np.linspace(440, 110, len(t))
    # Generate stereo sound
    sound_array = np.zeros((len(t), 2))
    base_sound = np.sin(2 * np.pi * frequency * t) * 0.5
    # Add some noise for explosion effect
    noise = np.random.default_rng().normal(0, 0.1, len(t))
    sound_array[:, 0] = base_sound + noise  # Left channel
    sound_array[:, 1] = base_sound + noise  # Right channel
    sound_array = np.clip(sound_array, -1, 1)
    sound_array = (sound_array * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(sound_array)

def generate_game_over_sound():
    sample_rate = 44100
    duration = 1.0  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # Create a descending arpeggio
    frequencies = [440, 392, 349, 330]  # A4, G4, F4, E4
    # Generate stereo sound
    sound_array = np.zeros((len(t), 2))
    for i, freq in enumerate(frequencies):
        start = int(i * len(t) / len(frequencies))
        end = int((i + 1) * len(t) / len(frequencies))
        note = np.sin(2 * np.pi * freq * t[start:end]) * 0.5
        sound_array[start:end, 0] = note  # Left channel
        sound_array[start:end, 1] = note  # Right channel
    sound_array = (sound_array * 32767).astype(np.int16)
    return pygame.sndarray.make_sound(sound_array)

# Create sound effects
shoot_sound = generate_shoot_sound()
explosion_sound = generate_explosion_sound()
game_over_sound = generate_game_over_sound()

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 30))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed = 8
        self.lives = 3
        self.shoot_delay = 250  # milliseconds
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
        
        # Shooting
        if keys[pygame.K_SPACE]:
            now = pygame.time.get_ticks()
            if now - self.last_shot > self.shoot_delay:
                self.shoot()
                self.last_shot = now

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        bullets.add(bullet)
        shoot_sound.play()

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, formation_pos):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.formation_pos = formation_pos
        self.original_x = x
        self.original_y = y
        self.speed = 2
        self.dive_speed = 5
        self.is_diving = False
        self.dive_target_x = random.randint(0, SCREEN_WIDTH)
        self.dive_target_y = SCREEN_HEIGHT + 100
        self.returning = False

    def update(self):
        if not self.is_diving:
            # Move in formation
            self.rect.x = self.original_x + math.sin(pygame.time.get_ticks() * 0.001) * 30
            
            # Random chance to dive
            if random.random() < 0.001:  # 0.1% chance per frame
                self.is_diving = True
                self.dive_target_x = random.randint(0, SCREEN_WIDTH)
        else:
            # Diving movement
            if not self.returning:
                # Move towards dive target
                dx = self.dive_target_x - self.rect.x
                dy = self.dive_target_y - self.rect.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 0:
                    self.rect.x += (dx / dist) * self.dive_speed
                    self.rect.y += (dy / dist) * self.dive_speed
                
                # Start returning if reached target
                if self.rect.y > SCREEN_HEIGHT:
                    self.returning = True
            else:
                # Return to formation
                dx = self.original_x - self.rect.x
                dy = self.original_y - self.rect.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 0:
                    self.rect.x += (dx / dist) * self.dive_speed
                    self.rect.y += (dy / dist) * self.dive_speed
                
                # Reset dive state if back in formation
                if dist < 5:
                    self.is_diving = False
                    self.returning = False
                    self.rect.x = self.original_x
                    self.rect.y = self.original_y

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = -10

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

# Game setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Galaxian")
clock = pygame.time.Clock()

# Create sprite groups
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
player = Player()
all_sprites.add(player)

# Create enemies in formation
enemy_rows = 4
enemies_per_row = 8
spacing_x = 60
spacing_y = 50
start_x = (SCREEN_WIDTH - (enemies_per_row - 1) * spacing_x) // 2
start_y = 50

for row in range(enemy_rows):
    for col in range(enemies_per_row):
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y
        enemy = Enemy(x, y, (col, row))
        all_sprites.add(enemy)
        enemies.add(enemy)

# Game variables
score = 0
game_over = False

# Game loop
running = True
while running:
    # Keep loop running at the right speed
    clock.tick(FPS)
    
    # Process input/events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    if not game_over:
        # Update
        all_sprites.update()

        # Check for bullet hits
        hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
        for hit in hits:
            score += 100
            explosion_sound.play()
            enemy = Enemy(hit.original_x, hit.original_y, hit.formation_pos)
            all_sprites.add(enemy)
            enemies.add(enemy)

        # Check for player collision with enemies
        hits = pygame.sprite.spritecollide(player, enemies, True)
        for hit in hits:
            player.lives -= 1
            explosion_sound.play()
            if player.lives <= 0:
                game_over = True
                game_over_sound.play()

    # Draw / render
    screen.fill(BLACK)
    all_sprites.draw(screen)
    
    # Draw score
    font = pygame.font.Font(None, 36)
    score_text = font.render(f'Score: {score}', True, WHITE)
    screen.blit(score_text, (10, 10))
    
    # Draw lives
    lives_text = font.render(f'Lives: {player.lives}', True, WHITE)
    screen.blit(lives_text, (SCREEN_WIDTH - 100, 10))

    if game_over:
        game_over_text = font.render('GAME OVER', True, RED)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2))
    
    # Flip the display
    pygame.display.flip()

pygame.quit()
sys.exit() 