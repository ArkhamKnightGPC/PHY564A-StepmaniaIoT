import pygame
import time
import numpy as np
from pathlib import Path
from typing import Literal 

RESOURCE_PATH = Path("./Resources/").absolute()
DIR_DICT = {0: "left", 1: "down", 2: "up", 3: "right"}
ARROW_SIZE = 100

def get_spawn_coord(spawn_area_w: int, arrow_w: int, columns: int, column: int) -> int:
    column_w = spawn_area_w // columns
    return column_w * column + (column_w - arrow_w) // 2

class stepmania:
    def __init__(self):
        pygame.init()
        self.WIDTH, self.HEIGHT = 600, 800
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.clock = pygame.time.Clock()

        # Arrow properties
        self.arrow_img = pygame.Surface((50, 50))  # Placeholder
        self.arrow_img.fill((255, 0, 0))
        self.spawn_y = self.HEIGHT - 100  # Where arrows should be hit
        self.SCROLL_SPEED = 50
        
        self.running = False
        self.arrows: list[Arrow] = []

        self.next_arrow_time = 0
        self.start_time = 0
        self.BPM = 120

    def start(self):
        self.running = True
        self.start_time = time.perf_counter()
        self.next_arrow_time = self.start_time

        while self.running:
            self.screen.fill((0, 0, 0))
            current_time = time.perf_counter()

            # # Spawn new arrows at whole beats
            # if current_time >= self.next_arrow_time:
            #     dir = np.random.randint(4)
            #     spawn_x = self.WIDTH//4 + get_spawn_coord(self.WIDTH//2, 50, 4, dir)
            #     self.arrows.append(Arrow(self.next_arrow_time, spawn_x, self.spawn_y, "red", DIR_DICT[dir]))
            #     self.next_arrow_time += 60 / self.BPM
            
            # Update and draw arrows
            to_remove: list[Arrow] = []
            for arrow in self.arrows[:]:
                arrow.update(current_time, self.HEIGHT, self.SCROLL_SPEED, self.BPM)
                if arrow.y < -50:
                    to_remove.append(arrow)
                else:
                    arrow.draw(self.screen)
            for arrow in to_remove:
                self.arrows.remove(arrow)

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        self.SCROLL_SPEED += 50
                    elif event.key == pygame.K_s:
                        self.SCROLL_SPEED -= 50
            
            pygame.display.flip()
            self.clock.tick(60)



class Arrow:
    arrow_imgs : dict[str, pygame.Surface]= {}
    def __init__(self, spawn_time: float, spawn_x: int, spawn_y: int, arrow_img_name: str, direction: Literal["left","up","right","down"] = "up"):
        self.spawn_time = spawn_time  # When the arrow should appear
        self.y = spawn_y  # Start at the bottom
        self.x = spawn_x
        if not Arrow.arrow_imgs:
            self._load_images()
        if direction == "left":
            self.img = Arrow.arrow_imgs[arrow_img_name]
        elif direction == "down":
            self.img = pygame.transform.rotate(Arrow.arrow_imgs[arrow_img_name], 90)
        elif direction == "right":
            self.img = pygame.transform.rotate(Arrow.arrow_imgs[arrow_img_name], 180)
        elif direction == "up":
            self.img = pygame.transform.rotate(Arrow.arrow_imgs[arrow_img_name], 270)

    def update(self, current_time, height: int, SCROLL_SPEED: int, BPM: int, speed_multiplier=1.0):
        beats_elapsed = (current_time - self.spawn_time) / (60 / BPM)
        self.y = height - (beats_elapsed * SCROLL_SPEED * speed_multiplier)

    def draw(self, screen: pygame.Surface):
        screen.blit(self.img, (self.x, self.y))

    def _load_images(self):
        Arrow.arrow_imgs["blue"] = pygame.image.load(RESOURCE_PATH / "ArrowBlue.png")
        Arrow.arrow_imgs["red"] = pygame.image.load(RESOURCE_PATH / "ArrowRed.png")
        Arrow.arrow_imgs["green"] = pygame.image.load(RESOURCE_PATH / "ArrowGreen.png")
        Arrow.arrow_imgs["yellow"] = pygame.image.load(RESOURCE_PATH / "ArrowYellow.png")
        Arrow.arrow_imgs["purple"] = pygame.image.load(RESOURCE_PATH / "ArrowPurple.png")
        Arrow.arrow_imgs["orange"] = pygame.image.load(RESOURCE_PATH / "ArrowMagenta.png")
        Arrow.arrow_imgs["cyan"] = pygame.image.load(RESOURCE_PATH / "ArrowCyan.png")
        Arrow.arrow_imgs["white"] = pygame.image.load(RESOURCE_PATH / "ArrowPink.png")
        for arrow_name in Arrow.arrow_imgs:
            Arrow.arrow_imgs[arrow_name] = pygame.transform.scale(Arrow.arrow_imgs[arrow_name], (ARROW_SIZE, ARROW_SIZE))

        

if __name__ == "__main__":
    game = stepmania()
    game.start()
    pygame.quit()