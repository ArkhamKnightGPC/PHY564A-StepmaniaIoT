import pygame
import time
import numpy as np
from pathlib import Path
from typing import Literal, Callable
from collections import deque
import threading
from itertools import chain
from BluetoothImplementation import bluetooth_definition as bt

BTCLIENTS = ["E8:31:CD:CB:2F:EE"]
RESOURCE_PATH = Path("./Resources/").absolute()
DIR_DICT = {0: "left", 1: "down", 2: "up", 3: "right"}
DIR_DICT_INV = {"left": 0, "down": 1, "up": 2, "right": 3}
ARROW_SIZE = 100
WIDTH, HEIGHT = 600, 800
MEASURE_MARGIN = 4 # number of measures to summon the arrows before they reach the markers at ZERO_Y
ZERO_Y = 80

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
        self.bluetooth_clients = bt.setup_bluetooth(*BTCLIENTS, use_mac_addresses=True)

        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        Arrow._load_images()
        MarkerArrow._load_image()
        self.score_recorder = ScoreRecorder()
        self.font = pygame.font.Font(None, 36)

        # Arrow properties
        self.bottom_y = HEIGHT - 100  # Where arrows should be hit
        self.SCROLL_SPEED = 200
        
        self.running = False
        self.arrow_markers: tuple[MarkerArrow, MarkerArrow, MarkerArrow, MarkerArrow] = (
            MarkerArrow("left"),
            MarkerArrow("down"),
            MarkerArrow("up"),
            MarkerArrow("right")
        )
        self.arrows: tuple[list[Arrow]] = ([], [], [], []) # Arrows for each direction
        self.measure_lines: list[MeasureLine] = []

        self.next_measure_time= 0
        self.start_time = 0
        self.BPM = 120

        self.arrow_block_queue = deque()
        self.do_measure : Callable[[], None] = None # Function to call when a measure is reached


    def start(self):
        """Starts the game loop"""
        self.running = True
        self.start_time = time.perf_counter()
        self.next_measure_time = self.start_time

        while self.running: # Main loop
            self.screen.fill((0, 0, 0))
            current_time = time.perf_counter()

            # Spawn new arrows at whole measures (4 beats)
            if current_time >= self.next_measure_time:
                self.next_measure_time += 4*60 / self.BPM
                if len(self.arrow_block_queue) > 0:
                    block = self.arrow_block_queue.popleft()
                    self.spawn_arrow_block(current_time, block)
                if self.do_measure:
                    self.do_measure()
                
                # spawn measure line
                self.measure_lines.append(MeasureLine(current_time))
                
            
            # Draw and updates
            self.draw_text(f"Score: {self.score_recorder.score}", 10, 10)
            self.draw_text(f"BPM: {self.BPM}", 10, 40)
            self.draw_text(f"Speed: {self.SCROLL_SPEED}", 10, 70)
            for marker_arrow in self.arrow_markers:
                marker_arrow.draw(self.screen)
            for measure_line in self.measure_lines:
                measure_line.update(current_time, HEIGHT, self.SCROLL_SPEED, self.BPM)
                if measure_line.y < -50:
                    self.measure_lines.remove(measure_line)
                else:
                    measure_line.draw(self.screen)

            def do_arrow_draw(dir_index: int) -> None: # for all arrows
                for arrow in self.arrows[dir_index]:
                    arrow.update(current_time, HEIGHT, self.SCROLL_SPEED, self.BPM)
                    if arrow.y < -50:
                        self.arrows[dir_index].remove(arrow)
                        self.score_recorder.record_miss()
                    else:
                        arrow.draw(self.screen)    
            for dir_index in range(len(self.arrows)):
                do_arrow_draw(dir_index)

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        self.SCROLL_SPEED = self.SCROLL_SPEED * 1.1
                    elif event.key == pygame.K_s:
                        self.SCROLL_SPEED = self.SCROLL_SPEED * 0.9
                    elif event.key == pygame.K_a:
                        self.BPM += 20
                    elif event.key == pygame.K_q:
                        self.BPM -= 20
                    else:
                        def do_arrow_hit(dir_index: int) -> None:
                            to_remove = []
                            time_1_measure = 4*60/self.BPM
                            for arrow in self.arrows[dir_index]:
                                arrow_0_time = arrow.spawn_time + time_1_measure * 4
                                if self.score_recorder.check_hit(current_time, arrow_0_time, dir_index):
                                    to_remove.append(arrow)
                                    break # only hit one arrow
                            for arrow in to_remove:
                                self.arrows[dir_index].remove(arrow)
                        if event.key == pygame.K_LEFT:
                            do_arrow_hit(DIR_DICT_INV["left"])
                        elif event.key == pygame.K_DOWN:
                            do_arrow_hit(DIR_DICT_INV["down"])
                        elif event.key == pygame.K_UP:
                            do_arrow_hit(DIR_DICT_INV["up"])
                        elif event.key == pygame.K_RIGHT:
                            do_arrow_hit(DIR_DICT_INV["right"])
                        elif event.key == pygame.K_ESCAPE:
                            self.running = False
                        # else:
                        #     print(f"Key pressed: {event.key}, {pygame.key.name(event.key)}, {pygame.K_LEFT}")
            pygame.display.flip()
            self.clock.tick(60)

    def stop(self):
        """Stops the game loop"""
        self.running = False
    
    # def start_threaded(self):
    #     """Starts the game loop in a new thread"""
    #     self.running = True
    #     self.start_time = time.perf_counter()
    #     self.next_measure_time = self.start_time
    #     self.thread = threading.Thread(target=self.start)
    #     self.thread.start()
    #     return self.thread
    
    def spawn_arrow(self, direction: Literal["left","up","right","down"], color: Literal["blue","red","green","yellow","purple","orange","cyan","white"], spawn_time: float):
        """Spawns an arrow at a given time"""
        arrow = Arrow(spawn_time, direction, color)
        self.arrows[DIR_DICT_INV[direction]].append(arrow)
    
    def spawn_arrow_block(self, measure_begin_time: float, arrow_lines: "list[ tuple[ bool, bool, bool, bool] ]"):
        """Spawns a block of arrows at a given time"""
        if len(arrow_lines) == 0:
            return
        
        time_offset = 60 / self.BPM * 4 / len(arrow_lines)       

        for i, arrow_line in enumerate(arrow_lines):
            # Supported up to 24 beats per tempo
            if (48*4) % len(arrow_lines) != 0:
                raise ValueError(f"Invalid number of arrows {len(arrow_lines)} for a measure, should divide 48*4.")
            
            color = "white" # default color
            beat_offset = (i * (48 * 4 // len(arrow_lines))) % 48

            if beat_offset == 0: # i % 48 == 0
                color = "red" # beat
            elif beat_offset % 24 == 0:
                color = "blue" # 1/2 beat
            elif beat_offset % 16 == 0: 
                color = "purple" # 1/3 beat
            elif beat_offset % 12 == 0:
                color = "green" # 1/4 beat
            elif beat_offset % 8 == 0:
                color = "pink" # 1/6 beat
            elif beat_offset % 6 == 0:
                color = "yellow" # 1/8 beat
            elif beat_offset % 4 == 0:
                color = "cyan" # 1/16 beat
            elif beat_offset % 3 == 0:
                color = "magenta" # 1/12 beat
            else:
                color = "white"            
            
            if arrow_line[0]:
                self.spawn_arrow("left", color, measure_begin_time + time_offset * i)
            if arrow_line[1]:
                self.spawn_arrow("down", color, measure_begin_time + time_offset * i)
            if arrow_line[2]:
                self.spawn_arrow("up", color, measure_begin_time + time_offset * i)
            if arrow_line[3]:
                self.spawn_arrow("right", color, measure_begin_time + time_offset * i)
                
    def draw_text(self, text: str, x: int, y: int):
        """Draws text on the screen"""
        text_surface = self.font.render(text, True, (255, 255, 255))
        self.screen.blit(text_surface, (x, y))
class ScoreRecorder:
    """Class to record the score of a player"""
    def __init__(self):
        """Class to record the score of a player"""
        self.score = 0
        # self.tap_sound = pygame.mixer.Sound(RESOURCE_PATH / "GameplayAssist clap.ogg")
        self.tap_sounds = {"clap": pygame.mixer.Sound(RESOURCE_PATH / "GameplayAssist clap.ogg")}
        for i in range(1,65):
            self.tap_sounds[f"piano_{i:03}"] = pygame.mixer.Sound(RESOURCE_PATH / "piano" / f"jobro__piano-ff-{i:03}.ogg")
            print(f"Loaded piano_{i:03} at {RESOURCE_PATH / 'piano' / f'jobro__piano-ff-{i:03}.ogg'}")
    def check_hit(self, current_time: float, arrow_0_time: float, dir_index: int) -> bool:
        """Checks if the player hit an arrow. Returns True if the arrow was hit."""
        if abs(current_time - arrow_0_time) < 0.1:
            self.score += 1
            self.play_sound(dir_index)
            return True
        return False

    def play_sound(self, dir_index: int):
        """Plays a sound"""
        # sound_name = np.random.choice(list(self.tap_sounds.keys())) # select random sound from dict
        # self.tap_sounds[sound_name].play(maxtime=500)
        
        sound_left = self.tap_sounds[f"piano_{40:03}"] # do
        sound_down = self.tap_sounds[f"piano_{44:03}"] # mi
        sound_up = self.tap_sounds[f"piano_{47:03}"] # sol
        sound_right = self.tap_sounds[f"piano_{52:03}"] # do
        match dir_index:
            case 0:
                sound_left.play(maxtime=500)
            case 1:
                sound_down.play(maxtime=500)
            case 2:
                sound_up.play(maxtime=500)
            case 3:
                sound_right.play(maxtime=500)
    
    def record_miss(self):
        """Records a miss"""
        self.score -= 1
    

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
        time_1_measure = 4*60/BPM
        speed = scroll_speed
        spawn_y = ZERO_Y + 4 * time_1_measure * speed

        t = current_time - self.spawn_time
        self.y = ZERO_Y + (spawn_y - ZERO_Y)*(1 - t / (4 * time_1_measure)) - ARROW_SIZE//2



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
        Arrow.arrow_imgs["magenta"] = pygame.image.load(RESOURCE_PATH / "ArrowMagenta.png")
        Arrow.arrow_imgs["cyan"] = pygame.image.load(RESOURCE_PATH / "ArrowCyan.png")
        Arrow.arrow_imgs["pink"] = pygame.image.load(RESOURCE_PATH / "ArrowPink.png")
        Arrow.arrow_imgs["white"] = pygame.image.load(RESOURCE_PATH / "ArrowWhite.png")
        for arrow_name in Arrow.arrow_imgs:
            Arrow.arrow_imgs[arrow_name] = pygame.transform.scale(Arrow.arrow_imgs[arrow_name], (ARROW_SIZE, ARROW_SIZE))


class MeasureLine:
    H = 10
    def __init__(self, spawn_time: float):
        self.spawn_time = spawn_time
        self.x = 0
        self.y = 0
        # # red
        self.img = pygame.Surface((WIDTH, MeasureLine.H))
        self.img.fill((255, 0, 0))

    def update(self, current_time, height: int, scroll_speed: int, BPM: int):
        time_1_measure = 4*60/BPM
        speed = scroll_speed
        spawn_y = ZERO_Y + 4 * time_1_measure * speed

        t = current_time - self.spawn_time
        self.y = ZERO_Y + (spawn_y - ZERO_Y)*(1 - t / (4 * time_1_measure)) - MeasureLine.H//2

    def draw(self, screen: pygame.Surface):
        screen.blit(self.img, (self.x, self.y))

class MarkerArrow:
    marker_img: pygame.Surface = None
    """Class to represent an marker arrow asset"""
    arrow_imgs : dict[str, pygame.Surface]= {}
    def __init__(self, direction: Literal["left","up","right","down"] = "left"):
        self.x = get_arrow_x(direction, WIDTH, ARROW_SIZE, WIDTH//2)
        self.y = ZERO_Y - ARROW_SIZE//2
        if direction == "left":
            self.img = MarkerArrow.marker_img
        elif direction == "down":
            self.img = pygame.transform.rotate(MarkerArrow.marker_img, 90)
        elif direction == "right":
            self.img = pygame.transform.rotate(MarkerArrow.marker_img, 180)
        elif direction == "up":
            self.img = pygame.transform.rotate(MarkerArrow.marker_img, 270)
        else:
            raise ValueError(f"Invalid direction {direction}")
        
    def draw(self, screen: pygame.Surface):
        screen.blit(self.img, (self.x, self.y))

    @staticmethod
    def _load_image():
        MarkerArrow.marker_img = pygame.image.load(RESOURCE_PATH / "ArrowMarker.png")
        MarkerArrow.marker_img = pygame.transform.scale(MarkerArrow.marker_img, (ARROW_SIZE, ARROW_SIZE))

class BeatSoundMaker:
    def __init__(self):
        self.beat_sounds = {}
        # TODO

# class EventExt(pygame.event.Event):

if __name__ == "__main__":
    game = stepmania()
    block1 = []
    for i in range(np.random.randint(1,5)):
        block1.append(random_arrow_line(np.random.randint(1,2)))
    game.arrow_block_queue.append(block1)
    def do_measure_make_new_block():
        block = []
        choices_p = { # num of arrows : probability
            1: 1/6,
            2: 1/3,
            4: 1/3,
            8: 1/6,}
        keys = [i for i in choices_p.keys()]
        values = [i for i in choices_p.values()]
        for i in range(np.random.choice(keys, p=values)): # 4 beats
            block.append(random_arrow_line(np.random.randint(1,2)))
        game.arrow_block_queue.append(block)
    game.do_measure = do_measure_make_new_block
    game.start()
    pygame.quit()