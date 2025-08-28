import pygame
import random
import sys
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# --- Game Constants ---
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# --- Colors ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
DARK_RED = (180, 0, 0)
DARK_BLUE = (0, 0, 150)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# --- Game Setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Enhanced Stick Man Shooter")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)
large_font = pygame.font.Font(None, 64)
title_font = pygame.font.Font(None, 80)

# --- Game State ---
game_state = "START"
wave_number = 1
wave_state = "SPAWNING"  # SPAWNING, BREAK, COMPLETED
wave_break_timer = 0
wave_break_duration = 180  # 3 seconds at 60 FPS
enemy_spawn_timer = 0
enemy_spawn_delay = 30  # Much faster spawning (0.5 seconds)

# --- Particle System ---
class Particle:
    def __init__(self, x, y, color, velocity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 5)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # gravity
        self.lifetime -= 1
        return self.lifetime > 0
    
    def draw(self, surface):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color_with_alpha = (*self.color, alpha)
        s = pygame.Surface((self.size * 2, self.size * 2))
        s.set_alpha(alpha)
        pygame.draw.circle(s, self.color, (self.size, self.size), self.size)
        surface.blit(s, (self.x - self.size, self.y - self.size))

particles = []

def create_explosion(x, y, color, count=10):
    for _ in range(count):
        velocity = (random.uniform(-3, 3), random.uniform(-3, 3))
        particles.append(Particle(x, y, color, velocity, random.randint(30, 60)))

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 25
        self.height = 70
        self.gun_length = 35
        self.gun_angle = 0
        self.health = 100
        self.max_health = 100
        self.rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)
        self.last_shot = 0
        self.shot_cooldown = 15  # frames between shots
        self.invulnerable_timer = 0
        
    def aim_at_mouse(self, mouse_pos):
        """Aim the gun at the mouse cursor position."""
        dx = mouse_pos[0] - self.x
        dy = mouse_pos[1] - self.y
        self.gun_angle = math.atan2(dy, dx)
    
    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot > self.shot_cooldown * (1000 // FPS)
    
    def take_damage(self, damage):
        if self.invulnerable_timer <= 0:
            self.health -= damage
            self.invulnerable_timer = 60  # 1 second of invulnerability
            create_explosion(self.x, self.y, RED, 5)
    
    def update(self):
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
        self.rect.center = (self.x, self.y)
    
    def draw(self, surface):
        # Add flashing effect when invulnerable
        if self.invulnerable_timer > 0 and self.invulnerable_timer % 10 < 5:
            return
            
        gun_end_x = self.x + self.gun_length * math.cos(self.gun_angle)
        gun_end_y = self.y + self.gun_length * math.sin(self.gun_angle)
        
        # Shadow effect
        shadow_offset = 2
        pygame.draw.circle(surface, GRAY, (self.x + shadow_offset, self.y - self.height // 2 + shadow_offset), self.width // 2)
        
        # Head
        pygame.draw.circle(surface, BLACK, (self.x, self.y - self.height // 2), self.width // 2)
        pygame.draw.circle(surface, WHITE, (self.x, self.y - self.height // 2), self.width // 2, 2)
        
        # Body
        pygame.draw.line(surface, BLACK, (self.x, self.y - self.height // 2 + self.width // 2), 
                        (self.x, self.y + self.height // 4), 4)
        
        # Legs
        pygame.draw.line(surface, BLACK, (self.x, self.y + self.height // 4), 
                        (self.x - self.width // 2, self.y + self.height // 2), 4)
        pygame.draw.line(surface, BLACK, (self.x, self.y + self.height // 4), 
                        (self.x + self.width // 2, self.y + self.height // 2), 4)
        
        # Gun
        pygame.draw.line(surface, DARK_BLUE, (self.x, self.y), (gun_end_x, gun_end_y), 6)
        pygame.draw.circle(surface, DARK_BLUE, (int(gun_end_x), int(gun_end_y)), 4)

class Enemy:
    def __init__(self, target_x, target_y):
        self.target_x = target_x
        self.target_y = target_y
        
        # Spawn from random side
        side = random.choice(['top', 'bottom', 'left', 'right'])
        margin = 80
        if side == 'top':
            self.x = random.randint(margin, SCREEN_WIDTH - margin)
            self.y = -50
        elif side == 'bottom':
            self.x = random.randint(margin, SCREEN_WIDTH - margin)
            self.y = SCREEN_HEIGHT + 50
        elif side == 'left':
            self.x = -50
            self.y = random.randint(margin, SCREEN_HEIGHT - margin)
        else:
            self.x = SCREEN_WIDTH + 50
            self.y = random.randint(margin, SCREEN_HEIGHT - margin)
        
        self.width = 18
        self.height = 55
        self.speed = random.uniform(2.5, 4.5)  # Much faster enemies
        self.health = 2
        self.max_health = 2
        self.rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)
        self.hit_timer = 0
        
    def move(self):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.hypot(dx, dy)
        
        if distance > 1:
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed
        
        self.rect.center = (self.x, self.y)
        
        if self.hit_timer > 0:
            self.hit_timer -= 1
    
    def take_damage(self, damage):
        self.health -= damage
        self.hit_timer = 10
        create_explosion(self.x, self.y, ORANGE, 3)
        return self.health <= 0
        
    def draw(self, surface):
        # Change color when hit
        color = RED if self.hit_timer <= 0 else YELLOW
        shadow_color = GRAY if self.hit_timer <= 0 else (200, 200, 0)
        
        # Shadow effect
        shadow_offset = 2
        pygame.draw.circle(surface, shadow_color, 
                          (self.x + shadow_offset, self.y - self.height // 2 + shadow_offset), 
                          self.width // 2)
        
        # Head
        pygame.draw.circle(surface, color, (self.x, self.y - self.height // 2), self.width // 2)
        pygame.draw.circle(surface, WHITE, (self.x, self.y - self.height // 2), self.width // 2, 2)
        
        # Body
        pygame.draw.line(surface, color, 
                        (self.x, self.y - self.height // 2 + self.width // 2), 
                        (self.x, self.y + self.height // 4), 4)
        
        # Arms
        arm_y = self.y - 5
        pygame.draw.line(surface, color, 
                        (self.x, arm_y), 
                        (self.x - self.width // 2, arm_y - 5), 3)
        pygame.draw.line(surface, color, 
                        (self.x, arm_y), 
                        (self.x + self.width // 2, arm_y - 5), 3)
        
        # Legs
        pygame.draw.line(surface, color, 
                        (self.x, self.y + self.height // 4), 
                        (self.x - self.width // 2, self.y + self.height // 2), 4)
        pygame.draw.line(surface, color, 
                        (self.x, self.y + self.height // 4), 
                        (self.x + self.width // 2, self.y + self.height // 2), 4)
        
        # Health bar
        if self.health < self.max_health:
            bar_width = 20
            bar_height = 4
            bar_x = self.x - bar_width // 2
            bar_y = self.y - self.height // 2 - 15
            
            pygame.draw.rect(surface, DARK_RED, (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(surface, GREEN, (bar_x, bar_y, 
                           bar_width * (self.health / self.max_health), bar_height))

class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.speed = 12
        self.radius = 6
        self.angle = angle
        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed
        self.rect = pygame.Rect(x - self.radius, y - self.radius, self.radius * 2, self.radius * 2)
        self.trail = [(self.x, self.y)]
        
    def move(self):
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)
        
        # Add to trail
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)
    
    def draw(self, surface):
        # Draw trail
        for i, pos in enumerate(self.trail):
            alpha = int(255 * (i + 1) / len(self.trail))
            size = int(self.radius * (i + 1) / len(self.trail))
            s = pygame.Surface((size * 2, size * 2))
            s.set_alpha(alpha // 2)
            pygame.draw.circle(s, BLUE, (size, size), size)
            surface.blit(s, (pos[0] - size, pos[1] - size))
        
        # Draw bullet
        pygame.draw.circle(surface, BLUE, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), self.radius // 2)

def draw_health_bar(surface, x, y, current, maximum, width=200, height=20):
    # Background
    pygame.draw.rect(surface, DARK_RED, (x, y, width, height))
    # Health
    health_width = int(width * (current / maximum))
    pygame.draw.rect(surface, GREEN, (x, y, health_width, height))
    # Border
    pygame.draw.rect(surface, BLACK, (x, y, width, height), 2)
    # Text
    health_text = font.render(f"Health: {current}/{maximum}", True, BLACK)
    surface.blit(health_text, (x, y - 25))

def draw_wave_info(surface, wave, wave_state, enemies_left, break_timer=0):
    wave_text = font.render(f"Wave: {wave}", True, BLACK)
    surface.blit(wave_text, (SCREEN_WIDTH - 150, 20))
    
    if wave_state == "SPAWNING":
        enemies_text = font.render(f"Enemies: {enemies_left}", True, BLACK)
        surface.blit(enemies_text, (SCREEN_WIDTH - 150, 50))
    elif wave_state == "BREAK":
        break_seconds = max(0, break_timer // 60)
        break_text = font.render(f"Next wave in: {break_seconds + 1}", True, BLUE)
        surface.blit(break_text, (SCREEN_WIDTH - 180, 50))
        
        # Healing message
        heal_text = font.render("+ Health restored!", True, GREEN)
        surface.blit(heal_text, (SCREEN_WIDTH - 180, 80))

def draw_button(surface, text, x, y, width, height, color, text_color, border_color=BLACK):
    pygame.draw.rect(surface, color, (x, y, width, height))
    pygame.draw.rect(surface, border_color, (x, y, width, height), 3)
    
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
    surface.blit(text_surface, text_rect)
    
    return pygame.Rect(x, y, width, height)

def reset_game():
    global player, enemies, bullets, enemy_count_to_spawn, score, wave_number, enemy_spawn_timer, particles, wave_state, wave_break_timer, enemies_spawned_this_wave
    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    bullets = []
    enemies = []
    particles = []
    enemy_count_to_spawn = 5  # Start with 5 enemies per wave
    score = 0
    wave_number = 1
    wave_state = "SPAWNING"
    wave_break_timer = 0
    enemy_spawn_timer = 0
    enemies_spawned_this_wave = 0

# Initialize game objects
player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
bullets = []
enemies = []
enemy_count_to_spawn = 5
score = 0
enemies_spawned_this_wave = 0

# Main Game Loop
running = True
reset_game()

while running:
    dt = clock.tick(FPS)
    mouse_pos = pygame.mouse.get_pos()
    
    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                
            if game_state == "START":
                if event.key == pygame.K_SPACE:
                    reset_game()
                    game_state = "PLAYING"
                    
            elif game_state == "PLAYING":
                pass  # Shooting now handled by mouse click
                    
            elif game_state == "GAME_OVER":
                if event.key == pygame.K_r:
                    reset_game()
                    game_state = "PLAYING"
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            if game_state == "START":
                start_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 20, 200, 50)
                if start_button_rect.collidepoint(mouse_pos):
                    reset_game()
                    game_state = "PLAYING"
            elif game_state == "PLAYING":
                # Shoot with left mouse click
                if player.can_shoot():
                    gun_end_x = player.x + player.gun_length * math.cos(player.gun_angle)
                    gun_end_y = player.y + player.gun_length * math.sin(player.gun_angle)
                    bullets.append(Bullet(gun_end_x, gun_end_y, player.gun_angle))
                    player.last_shot = pygame.time.get_ticks()
            elif game_state == "GAME_OVER":
                restart_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)
                if restart_button_rect.collidepoint(mouse_pos):
                    reset_game()
                    game_state = "PLAYING"
    
    # Game Logic
    if game_state == "PLAYING":
        player.update()
        player.aim_at_mouse(mouse_pos)  # Manual aiming with mouse
        
        # Wave system logic
        if wave_state == "SPAWNING":
            # Spawn enemies quickly
            if len(enemies) + enemies_spawned_this_wave < enemy_count_to_spawn:
                enemy_spawn_timer += 1
                if enemy_spawn_timer >= enemy_spawn_delay:
                    enemies.append(Enemy(player.x, player.y))
                    enemies_spawned_this_wave += 1
                    enemy_spawn_timer = 0
            
            # Check if all enemies are spawned and defeated
            if enemies_spawned_this_wave >= enemy_count_to_spawn and len(enemies) == 0:
                wave_state = "BREAK"
                wave_break_timer = wave_break_duration
                # Heal player between waves
                player.health = min(player.health + 30, player.max_health)
        
        elif wave_state == "BREAK":
            wave_break_timer -= 1
            if wave_break_timer <= 0:
                # Start next wave
                wave_number += 1
                enemy_count_to_spawn = min(wave_number * 3 + 2, 25)  # Increase enemies per wave
                enemies_spawned_this_wave = 0
                wave_state = "SPAWNING"
        
        # Update bullets
        for bullet in bullets[:]:
            bullet.move()
            if not pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).colliderect(bullet.rect):
                bullets.remove(bullet)
        
        # Update enemies
        for enemy in enemies:
            enemy.move()
        
        # Update particles
        particles = [p for p in particles if p.update()]
        
        # Collision Detection
        for bullet in bullets[:]:
            for enemy in enemies[:]:
                if bullet.rect.colliderect(enemy.rect):
                    if bullet in bullets: bullets.remove(bullet)
                    if enemy.take_damage(1):
                        enemies.remove(enemy)
                        score += 10
                        create_explosion(enemy.x, enemy.y, RED, 8)
                    break
        
        # Player-Enemy collision
        for enemy in enemies:
            if player.rect.colliderect(enemy.rect):
                player.take_damage(20)
                if player.health <= 0:
                    game_state = "GAME_OVER"
        
        # Check wave completion
        # (This logic is now handled in the wave system above)
    
    # Drawing
    screen.fill(LIGHT_GRAY)
    
    # Draw grid background
    for x in range(0, SCREEN_WIDTH, 50):
        pygame.draw.line(screen, WHITE, (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, 50):
        pygame.draw.line(screen, WHITE, (0, y), (SCREEN_WIDTH, y), 1)
    
    if game_state == "START":
        # Title
        title_text = title_font.render("STICK MAN SHOOTER", True, BLACK)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle = font.render("Survive the waves of enemies!", True, GRAY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(subtitle, subtitle_rect)
        
        # Start button
        draw_button(screen, "START GAME", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 20, 200, 50, GREEN, BLACK)
        
        # Controls
        controls = [
            "Mouse - Aim",
            "Left Click - Shoot",
            "ESC - Quit"
        ]
        for i, control in enumerate(controls):
            text = font.render(control, True, BLACK)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120 + i * 30))
            screen.blit(text, text_rect)
    
    elif game_state == "PLAYING":
        # Draw game objects
        player.draw(screen)
        
        for enemy in enemies:
            enemy.draw(screen)
            
        for bullet in bullets:
            bullet.draw(screen)
            
        for particle in particles:
            particle.draw(screen)
        
        # Draw UI
        draw_health_bar(screen, 20, 20, player.health, player.max_health)
        
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (20, 70))
        
        draw_wave_info(screen, wave_number, wave_state, 
                      len(enemies) + (enemy_count_to_spawn - enemies_spawned_this_wave) if wave_state == "SPAWNING" else 0, 
                      wave_break_timer if wave_state == "BREAK" else 0)
        
        # Aim line (shows where player is aiming)
        aim_length = 100
        aim_end_x = player.x + aim_length * math.cos(player.gun_angle)
        aim_end_y = player.y + aim_length * math.sin(player.gun_angle)
        pygame.draw.line(screen, (255, 0, 0, 100), (player.x, player.y), (aim_end_x, aim_end_y), 2)
        
        # Crosshair at mouse position
        pygame.draw.circle(screen, RED, mouse_pos, 12, 2)
        pygame.draw.line(screen, RED, (mouse_pos[0] - 8, mouse_pos[1]), (mouse_pos[0] + 8, mouse_pos[1]), 2)
        pygame.draw.line(screen, RED, (mouse_pos[0], mouse_pos[1] - 8), (mouse_pos[0], mouse_pos[1] + 8), 2)
    
    elif game_state == "GAME_OVER":
        # Game over screen
        game_over_text = large_font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(game_over_text, game_over_rect)
        
        final_score_text = font.render(f"Final Score: {score}", True, BLACK)
        score_rect = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        screen.blit(final_score_text, score_rect)
        
        wave_text = font.render(f"Waves Survived: {wave_number - 1}", True, BLACK)
        wave_rect = wave_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        screen.blit(wave_text, wave_rect)
        
        # Restart button
        draw_button(screen, "RESTART", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50, GREEN, BLACK)
        
        restart_text = font.render("Press R to restart", True, GRAY)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        screen.blit(restart_text, restart_rect)
    
    pygame.display.flip()

pygame.quit()
sys.exit()