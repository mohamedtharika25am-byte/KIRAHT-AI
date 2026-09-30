import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Babu Game")

# Colors
BLACK = (18, 18, 24)
WHITE = (255, 255, 255)
GREEN = (46, 204, 113)
DARK_GREEN = (39, 174, 96)
RED = (231, 76, 60)
GRAY = (120, 120, 120)

# Snake settings
snake_block = 10
snake_speed = 15
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 22)
big_font = pygame.font.SysFont("Arial", 36, bold=True)

def show_score(score):
    score_surface = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_surface, [10, 10])

def game_loop():
    # Initial coordinates
    snake_x = SCREEN_WIDTH // 2
    snake_y = SCREEN_HEIGHT // 2

    # Movement velocity
    change_x = snake_block
    change_y = 0

    # Snake body tracking
    snake_body = []
    snake_length = 3

    # Generate initial food aligned with the grid
    food_x = round(random.randrange(0, SCREEN_WIDTH - snake_block) / 10.0) * 10.0
    food_y = round(random.randrange(0, SCREEN_HEIGHT - snake_block) / 10.0) * 10.0

    score = 0
    game_over = False

    while True:
        # Game Over Screen
        while game_over:
            screen.fill(BLACK)
            msg1 = big_font.render("Game Over!", True, RED)
            msg2 = font.render(f"Final Score: {score}", True, WHITE)
            msg3 = font.render("Press SPACE to Restart or Q to Quit", True, GRAY)

            screen.blit(msg1, [SCREEN_WIDTH // 2 - msg1.get_width() // 2, SCREEN_HEIGHT // 3])
            screen.blit(msg2, [SCREEN_WIDTH // 2 - msg2.get_width() // 2, SCREEN_HEIGHT // 2])
            screen.blit(msg3, [SCREEN_WIDTH // 2 - msg3.get_width() // 2, SCREEN_HEIGHT // 2 + 50])
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_SPACE:
                        return game_loop()

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if (event.key == pygame.K_LEFT or event.key == pygame.K_a) and change_x == 0:
                    change_x = -snake_block
                    change_y = 0
                elif (event.key == pygame.K_RIGHT or event.key == pygame.K_d) and change_x == 0:
                    change_x = snake_block
                    change_y = 0
                elif (event.key == pygame.K_UP or event.key == pygame.K_w) and change_y == 0:
                    change_y = -snake_block
                    change_x = 0
                elif (event.key == pygame.K_DOWN or event.key == pygame.K_s) and change_y == 0:
                    change_y = snake_block
                    change_x = 0

        # Update position
        snake_x += change_x
        snake_y += change_y

        # Check wall collision
        if snake_x < 0 or snake_x >= SCREEN_WIDTH or snake_y < 0 or snake_y >= SCREEN_HEIGHT:
            game_over = True

        # Check self collision
        snake_head = [snake_x, snake_y]
        if snake_head in snake_body:
            game_over = True

        snake_body.append(snake_head)
        if len(snake_body) > snake_length:
            del snake_body[0]

        # Check food collision
        if snake_x == food_x and snake_y == food_y:
            score += 1
            snake_length += 1
            food_x = round(random.randrange(0, SCREEN_WIDTH - snake_block) / 10.0) * 10.0
            food_y = round(random.randrange(0, SCREEN_HEIGHT - snake_block) / 10.0) * 10.0

        # Draw frame
        screen.fill(BLACK)

        # Draw food (Red apple)
        pygame.draw.rect(screen, RED, [food_x, food_y, snake_block, snake_block], border_radius=3)

        # Draw snake body
        for idx, segment in enumerate(snake_body):
            color = GREEN if idx == len(snake_body) - 1 else DARK_GREEN
            pygame.draw.rect(screen, color, [segment[0], segment[1], snake_block, snake_block], border_radius=2)

        show_score(score)
        pygame.display.update()
        clock.tick(snake_speed)

if __name__ == "__main__":
    game_loop()