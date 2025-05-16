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

# Load and scale images
def create_player_sprite():
    surf = pygame.Surface((50, 40), pygame.SRCALPHA)
    # Main body (fuselage)
    pygame.draw.polygon(surf, GREEN, [(25, 0), (20, 35), (30, 35)])
    # Cockpit
    pygame.draw.ellipse(surf, (200, 255, 200), (20, 5, 10, 8))
    # Main wings
    pygame.draw.polygon(surf, (0, 200, 0), [(5, 25), (20, 20), (30, 20), (45, 25)])
    # Wing details
    pygame.draw.line(surf, (0, 150, 0), (15, 22), (35, 22), 2)
    # Tail wings
    pygame.draw.polygon(surf, (0, 200, 0), [(15, 30), (25, 30), (20, 35)])
    # Engine glow
    pygame.draw.ellipse(surf, (255, 255, 200), (22, 32, 6, 4))
    return surf

def create_enemy_sprite():
    surf = pygame.Surface((40, 35), pygame.SRCALPHA)
    # Main body (fuselage)
    pygame.draw.polygon(surf, RED, [(20, 0), (10, 25), (30, 25)])
    # Cockpit
    pygame.draw.ellipse(surf, (255, 200, 200), (15, 5, 10, 8))
    # Main wings
    pygame.draw.polygon(surf, (200, 0, 0), [(0, 15), (15, 20), (25, 20), (40, 15)])
    # Wing details
    pygame.draw.line(surf, (150, 0, 0), (10, 18), (30, 18), 2)
    # Tail wings
    pygame.draw.polygon(surf, (200, 0, 0), [(15, 22), (25, 22), (20, 25)])
    # Engine glow
    pygame.draw.ellipse(surf, (255, 200, 200), (17, 23, 6, 4))
    # Wing tips
    pygame.draw.polygon(surf, (150, 0, 0), [(0, 15), (5, 12), (5, 15)])
    pygame.draw.polygon(surf, (150, 0, 0), [(35, 15), (40, 15), (35, 12)])
    return surf

def create_bullet_sprite():
    surf = pygame.Surface((6, 20), pygame.SRCALPHA)
    # Bullet body
    pygame.draw.rect(surf, YELLOW, (1, 0, 4, 20))
    # Bullet tip
    pygame.draw.polygon(surf, YELLOW, [(3, 0), (0, 5), (6, 5)])
    # Glow effect
    pygame.draw.rect(surf, (255, 255, 200), (2, 2, 2, 16))
    # Trailing effect
    for i in range(3):
        alpha = 100 - (i * 30)
        glow = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 255, 0, alpha), (2, 2), 2)
        surf.blit(glow, (1, 16 + (i * 2)))
    return surf

def create_explosion_sprite():
    surf = pygame.Surface((40, 40), pygame.SRCALPHA)
    # Explosion center
    pygame.draw.circle(surf, (255, 200, 0), (20, 20), 12)
    # Inner glow
    pygame.draw.circle(surf, (255, 255, 200), (20, 20), 8)
    # Outer glow
    pygame.draw.circle(surf, (255, 100, 0), (20, 20), 20, 3)
    # Explosion particles
    for i in range(8):
        angle = i * (360 / 8)
        rad = math.radians(angle)
        x = 20 + math.cos(rad) * 15
        y = 20 + math.sin(rad) * 15
        pygame.draw.circle(surf, (255, 150, 0), (int(x), int(y)), 3)
    return surf

# Create sprites
player_img = create_player_sprite()
enemy_img = create_enemy_sprite()
bullet_img = create_bullet_sprite()
explosion_anim = []
for i in range(9):
    surf = create_explosion_sprite()
    # Scale the explosion based on frame
    scale = 1 + (i * 0.2)
    new_size = (int(surf.get_width() * scale), int(surf.get_height() * scale))
    scaled_surf = pygame.transform.scale(surf, new_size)
    explosion_anim.append(scaled_surf)

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

# Explosion class
class Explosion(pygame.sprite.Sprite):
    def __init__(self, center):
        pygame.sprite.Sprite.__init__(self)
        self.frame = 0
        self.image = explosion_anim[self.frame]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame_rate = 50
        self.last_update = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(explosion_anim):
                self.kill()
            else:
                center = self.rect.center
                self.image = explosion_anim[self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed = 8
        self.lives = 3
        self.shoot_delay = 250  # milliseconds
        self.last_shot = pygame.time.get_ticks()
        self.hidden = False
        self.hide_timer = pygame.time.get_ticks()
        self.power = 1
        self.power_time = pygame.time.get_ticks()

    def update(self):
        # Unhide if hidden
        if self.hidden and pygame.time.get_ticks() - self.hide_timer > 1000:
            self.hidden = False
            self.rect.centerx = SCREEN_WIDTH // 2
            self.rect.bottom = SCREEN_HEIGHT - 10

        if not self.hidden:
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
        if not self.hidden:
            if self.power == 1:
                bullet = Bullet(self.rect.centerx, self.rect.top)
                all_sprites.add(bullet)
                bullets.add(bullet)
            elif self.power >= 2:
                bullet1 = Bullet(self.rect.left, self.rect.centery)
                bullet2 = Bullet(self.rect.right, self.rect.centery)
                all_sprites.add(bullet1)
                all_sprites.add(bullet2)
                bullets.add(bullet1)
                bullets.add(bullet2)
            shoot_sound.play()

    def hide(self):
        # Hide the player temporarily
        self.hidden = True
        self.hide_timer = pygame.time.get_ticks()
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT + 200)

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, formation_pos):
        super().__init__()
        self.image = enemy_img
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
        self.image = bullet_img
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

def create_enemy_formation():
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

# Create initial enemy formation
create_enemy_formation()

# Game variables
score = 0
game_over = False
level = 1

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
            expl = Explosion(hit.rect.center)
            all_sprites.add(expl)

        # Check if all enemies are destroyed
        if len(enemies) == 0:
            level += 1
            create_enemy_formation()

        # Check for player collision with enemies
        hits = pygame.sprite.spritecollide(player, enemies, True)
        for hit in hits:
            player.lives -= 1
            explosion_sound.play()
            expl = Explosion(hit.rect.center)
            all_sprites.add(expl)
            if player.lives <= 0:
                game_over = True
                game_over_sound.play()
            else:
                player.hide()

    # Draw / render
    screen.fill(BLACK)
    all_sprites.draw(screen)
    
    # Draw score and level
    font = pygame.font.Font(None, 36)
    score_text = font.render(f'Score: {score}', True, WHITE)
    screen.blit(score_text, (10, 10))
    
    # Draw lives
    lives_text = font.render(f'Lives: {player.lives}', True, WHITE)
    screen.blit(lives_text, (SCREEN_WIDTH - 100, 10))

    # Draw level
    level_text = font.render(f'Level: {level}', True, WHITE)
    screen.blit(level_text, (SCREEN_WIDTH // 2 - 40, 10))

    if game_over:
        game_over_text = font.render('GAME OVER', True, RED)
        screen.blit(game_over_text, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2))
    
    # Flip the display
    pygame.display.flip()

pygame.quit()
sys.exit() 