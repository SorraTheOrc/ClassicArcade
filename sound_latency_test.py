#!/usr/bin/env python3
"""Simple interactive sound latency test.
Click the button to play a sound and measure the delay.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

import pygame

import audio
import config

# Set minimal buffer BEFORE init
os.environ["SDL_AUDIO_BUFFER_SIZE"] = "128"

pygame.init()
pygame.mixer.init()

# Initialize audio with preloaded sounds
config.MUTE = False
audio.init()

# Load a sound for testing
sound_path = "/home/rogardle/projects/classic-arcade/test_1/assets/sounds/pong/wall.wav"
sound = pygame.mixer.Sound(sound_path)

# Setup display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sound Latency Test - Click to Play")

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 48)

click_time = None
latency_samples = []
button_rect = pygame.Rect(300, 250, 200, 100)


def draw_text(text, x, y, color=WHITE, size=36, font_obj=None):
    if font_obj is None:
        font_obj = font
    text_surface = font_obj.render(text, True, color)
    screen.blit(text_surface, (x, y))


clock = pygame.time.Clock()
running = True

print("=" * 70)
print("SOUND LATENCY TEST")
print("=" * 70)
print()
print("Instructions:")
print("1. Click the PLAY SOUND button")
print("2. The test measures delay between click and sound playback")
print("3. Press ESC or close to exit")
print()
print("Audio buffer size: 128 (very low latency)")
print("Sounds preloaded at startup")
print()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if button_rect.collidepoint(event.pos):
                click_time = time.perf_counter()
                sound.play()

    # Clear screen
    screen.fill(BLACK)

    # Draw title
    draw_text("SOUND LATENCY TEST", 200, 50, BLUE, 48, large_font)
    draw_text("Click PLAY SOUND to test latency", 200, 110, WHITE, 28)

    # Draw button
    mouse_pos = pygame.mouse.get_pos()
    if button_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen, GREEN, button_rect)
        draw_text("PLAY SOUND", 320, 285, BLACK, 36)
    else:
        pygame.draw.rect(screen, RED, button_rect)
        draw_text("PLAY SOUND", 320, 285, WHITE, 36)

    # Show results
    if latency_samples:
        avg = sum(latency_samples) / len(latency_samples)
        draw_text(f"Average Latency: {avg:.2f} ms", 250, 420, GREEN, 36)
        draw_text(f"Last Latency: {latency_samples[-1]:.2f} ms", 250, 460, WHITE, 36)
        draw_text(f"Samples: {len(latency_samples)}", 250, 500, WHITE, 36)
    else:
        draw_text("Click PLAY SOUND to start measuring", 250, 420, WHITE, 36)

    # Calculate latency
    if click_time is not None and not pygame.mixer.get_busy():
        current_time = time.perf_counter()
        latency = (current_time - click_time) * 1000
        latency_samples.append(latency)
        print(f"Latency: {latency:.2f} ms")
        click_time = None

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

print()
print("=" * 70)
if latency_samples:
    print(f"FINAL RESULTS: {len(latency_samples)} samples")
    print(f"Average latency: {sum(latency_samples)/len(latency_samples):.2f} ms")
    print(f"Min latency: {min(latency_samples):.2f} ms")
    print(f"Max latency: {max(latency_samples):.2f} ms")
else:
    print("No measurements collected")
print("=" * 70)
