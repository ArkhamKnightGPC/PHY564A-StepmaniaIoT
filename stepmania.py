import pygame
import time
import numpy as np
from pathlib import Path
from typing import Literal, Callable
from collections import deque
import threading

RESOURCE_PATH = Path("./Resources/").absolute()
DIR_DICT = {0: "left", 1: "down", 2: "up", 3: "right"}
ARROW_SIZE = 100
WIDTH, HEIGHT = 600, 800

def get_arrow_x(direction: str, screen_width: int, arrow_width: int, area_width: int):
    """Gets the x position of an arrow given its direction"""
    if direction == "left":
        return arrow_width * 1
    elif direction == "down":
        return arrow_width * 2
    elif direction == "up":
        return arrow_width * 3
    elif direction == "right":
        return arrow_width * 4

def random_arrow_line(count: int):
    """Gets a random arrow line with 'count' arrows"""    
    arrow_line = np.zeros(4, dtype=bool)
    arrow_line[:count] = True  # Set the first 'count' elements to True
    np.random.shuffle(arrow_line)  # Shuffle to randomize order
    return tuple(arrow_line)

class stepmania:
    """Class to simulate a stepmania game"""

    def __init__(self):
        """Class to simulate a stepmania game"""
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        Arrow._load_images()

        # Arrow properties
        self.bottom_y = HEIGHT - 100  # Where arrows should be hit
        self.SCROLL_SPEED = 50
        
        self.running = False
        self.arrows: list[Arrow] = []

        self.next_arrow_time = 0
        self.start_time = 0
        self.BPM = 300

        self.arrow_block_queue = deque()
        self.do_measure : Callable[[], None] = None # Function to call when a measure is reached


    def start(self):
        """Starts the game loop"""
        self.running = True
        self.start_time = time.perf_counter()
        self.next_arrow_time = self.start_time

        while self.running:
            self.screen.fill((0, 0, 0))
            current_time = time.perf_counter()

            # Spawn new arrows at whole measures (4 beats)
            if current_time >= self.next_arrow_time:
                self.next_arrow_time += 4*60 / self.BPM
                if len(self.arrow_block_queue) > 0:
                    block = self.arrow_block_queue.popleft()
                    self.spawn_arrow_block(current_time, block)
                if self.do_measure:
                    self.do_measure()
                
            
            # Update and draw arrows
            to_remove: list[Arrow] = []
            for arrow in self.arrows[:]:
                arrow.update(current_time, HEIGHT, self.SCROLL_SPEED, self.BPM)
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
                    elif event.key == pygame.K_a:
                        self.BPM += 20
                    elif event.key == pygame.K_q:
                        self.BPM -= 20
            
            pygame.display.flip()
            self.clock.tick(60)

    def stop(self):
        """Stops the game loop"""
        self.running = False
    
    def start_threaded(self):
        """Starts the game loop in a new thread"""
        self.running = True
        self.start_time = time.perf_counter()
        self.next_arrow_time = self.start_time
        self.thread = threading.Thread(target=self.start)
        self.thread.start()
        return self.thread
    
    def spawn_arrow(self, direction: Literal["left","up","right","down"], color: Literal["blue","red","green","yellow","purple","orange","cyan","white"], spawn_time: float):
        """Spawns an arrow at a given time"""
        arrow = Arrow(spawn_time, direction, color)
        self.arrows.append(arrow)
    
    def spawn_arrow_block(self, measure_begin_time: float, arrow_lines: "list[ tuple[ bool, bool, bool, bool] ]"):
        """Spawns a block of arrows at a given time"""
        if len(arrow_lines) == 0:
            return
        
        time_offset = 60 / self.BPM * 4 / len(arrow_lines)
        for i, arrow_line in enumerate(arrow_lines):
            if arrow_line[0]:
                self.spawn_arrow("left", "red", measure_begin_time + time_offset * i)
            if arrow_line[1]:
                self.spawn_arrow("down", "red", measure_begin_time + time_offset * i)
            if arrow_line[2]:
                self.spawn_arrow("up", "red", measure_begin_time + time_offset * i)
            if arrow_line[3]:
                self.spawn_arrow("right", "red", measure_begin_time + time_offset * i)
                

class Arrow:
    """Class to represent an arrow asset"""
    arrow_imgs : dict[str, pygame.Surface]= {}
    def __init__(self, spawn_time: float, direction: Literal["left","up","right","down"] = "left", color: Literal["blue","red","green","yellow","purple","orange","cyan","white"] = "red"):
        self.x = get_arrow_x(direction, WIDTH, ARROW_SIZE, WIDTH//2)
        self.y = 0
        self.spawn_time = spawn_time
        if direction == "left":
            self.img = Arrow.arrow_imgs[color]
        elif direction == "down":
            self.img = pygame.transform.rotate(Arrow.arrow_imgs[color], 90)
        elif direction == "right":
            self.img = pygame.transform.rotate(Arrow.arrow_imgs[color], 180)
        elif direction == "up":
            self.img = pygame.transform.rotate(Arrow.arrow_imgs[color], 270)
        else:
            raise ValueError(f"Invalid direction {direction}")
        
    def update(self, current_time, height: int, scroll_speed: int, BPM: int):
        beats_elapsed = (current_time - self.spawn_time) / (60 / BPM)
        self.y = height - (beats_elapsed * scroll_speed)

    def draw(self, screen: pygame.Surface):
        screen.blit(self.img, (self.x, self.y))

    @staticmethod
    def _load_images():
        Arrow.arrow_imgs.clear()
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
    game.start_threaded()
    # for i in range(10):
    #     block = []
    #     for i in range(np.random.randint(1,5)):
    #         block.append(random_arrow_line(np.random.randint(1,5)))
    #     game.arrow_block_queue.append(block)
    def do_measure_make_new_block():
        block = []
        for i in range(np.random.randint(1,5)):
            block.append(random_arrow_line(np.random.randint(1,5)))
        game.arrow_block_queue.append(block)
    game.do_measure = do_measure_make_new_block
    input("Keeping alive. Press enter to quit...")
    pygame.quit()
