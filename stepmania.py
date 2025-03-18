import pygame
import time
import numpy as np
from pathlib import Path
from typing import Literal, Callable
from collections import deque
import threading
from itertools import chain
from BluetoothImplementation import bluetooth_definition as bt

BTCLIENTS = ["E8:31:CD:CB:2F:EE", "44:17:93:E0:D8:A2"]
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

class Stepmania:
    """Class to simulate a stepmania game"""

    def __init__(self):
        """Class to simulate a stepmania game"""
        print(f"Setting up bluetooth connections for {BTCLIENTS}")
        self.bluetooth_clients = [ bt.setup_bluetooth(BTCLIENTS[i], use_mac_addresses=True) for i in range(2)]
        self.bluetooth_clients[0][0].recv_message_callback = self._bluetooth_player1_callback
        self.bluetooth_clients[1][0].recv_message_callback = self._bluetooth_player2_callback

        print("Initializing pygame...")
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        
        print("Loading resources...")
        Arrow._load_images()
        MarkerArrow._load_image()
        BeatSoundMaker._load_beat_sounds()
        MarkerSpawn._load_image()
        PlayerBtMarker._load_images()

        print("Final setups...")
        self.is_p2 = False # whether p2 is playing
        self.score_recorder = ScoreRecorder(10)
        self.score_recorder_p2 = ScoreRecorder(10)
        self.font = pygame.font.Font(None, 36)
        self.beat_sound_maker = BeatSoundMaker()

        # Arrow properties
        self.bottom_y = HEIGHT - 100  # Where arrows should be hit
        self.SCROLL_SPEED = 350
        
        self.running = False
        self.playerbtmarkers : tuple[PlayerBtMarker, PlayerBtMarker] = (
            PlayerBtMarker("player1"),
            PlayerBtMarker("player2")
        )
        self.arrow_markers: tuple[MarkerArrow, MarkerArrow, MarkerArrow, MarkerArrow] = (
            MarkerArrow("left"),
            MarkerArrow("down"),
            MarkerArrow("up"),
            MarkerArrow("right")
        )
        self.spawn_markers: tuple[MarkerSpawn, MarkerSpawn, MarkerSpawn, MarkerSpawn] = (
            MarkerSpawn("left"),
            MarkerSpawn("down"),
            MarkerSpawn("up"),
            MarkerSpawn("right")
        )
        self.arrows: tuple[list[Arrow]] = ([], [], [], []) # Arrows for each direction
        self.measure_lines: list[MeasureLine] = []

        self.next_measure_time= 0
        self.start_time = 0
        self.BPM = 120
        self.is_gen_random = True # whether to generate random arrow blocks

        self.arrow_block_queue = deque()
        self.do_measure : Callable[[], None] = None # Function to call when a measure is reached


    def start(self):
        """Starts the game loop"""
        print("Starting game loop...")
        self.running = True
        self.start_time = time.perf_counter()
        self.next_measure_time = self.start_time
        self.next_beat_time = self.start_time

        while self.running: # Main loop
            self.screen.fill((0, 0, 0))
            current_time = time.perf_counter()
            
            # Play beat sound at each beat
            if current_time >= self.next_beat_time:
                self.next_beat_time += 60 / self.BPM
                self.beat_sound_maker.play_beat_sound()   

            # Spawn new arrows at whole measures (4 beats)
            if current_time >= self.next_measure_time and self.is_gen_random:
                self.next_measure_time += 4*60 / self.BPM
                if len(self.arrow_block_queue) > 0:
                    block = self.arrow_block_queue.popleft()
                    self.spawn_arrow_block(current_time, block)
                if self.do_measure:
                    self.do_measure()
                
                # spawn measure line
                self.measure_lines.append(MeasureLine(current_time))
                         
            
            # Draw and updates
            self.draw_text(f"Score: {self.score_recorder.score} (combo: {self.score_recorder.combo})", 10, 10)
            self.draw_text(f"BPM: {self.BPM:.2f}", 10, 40)
            self.draw_text(f"Speed: {self.SCROLL_SPEED:.2f}", 10, 70)
            if self.is_p2:
                self.draw_text(f"Score P2: {self.score_recorder_p2.score} (combo: {self.score_recorder_p2.combo})", 10, 100)
            for marker_arrow in self.arrow_markers: # Draw arrow markers
                marker_arrow.draw(self.screen)
            for marker_arrow in self.arrow_markers: # Reset arrow markers
                marker_arrow.is_pressed = False
            for marker_spawn in self.spawn_markers: # Draw arrow spawn markers
                marker_spawn.draw(self.screen)
            for measure_line in self.measure_lines: # Draw measure lines
                measure_line.update(current_time, HEIGHT, self.SCROLL_SPEED, self.BPM)
                if measure_line.y < -50:
                    self.measure_lines.remove(measure_line)
                else:
                    measure_line.draw(self.screen)
            for i in range(len(self.bluetooth_clients)): # Draw bluetooth markers
                if self.bluetooth_clients[i][0].client.is_connected:
                    self.playerbtmarkers[i].draw(self.screen)

            def do_arrow_draw(dir_index: int) -> None: # for all arrows
                for arrow in self.arrows[dir_index]:
                    arrow.update(current_time, HEIGHT, self.SCROLL_SPEED, self.BPM)
                    if arrow.y < -50:
                        self.arrows[dir_index].remove(arrow)
                        self.score_recorder.register_miss()
                        self.score_recorder_p2.register_hit(2)
                    else:
                        arrow.draw(self.screen)    
            for dir_index in range(len(self.arrows)):
                do_arrow_draw(dir_index)

            # Event handling
            for event in pygame.event.get():
                def do_arrow_hit(dir_index: int) -> None:
                    to_remove = []
                    time_1_measure = 4*60/self.BPM
                    for arrow in self.arrows[dir_index]:
                        arrow_0_time = arrow.spawn_time + time_1_measure * 4
                        if self.score_recorder.check_hit(current_time, arrow_0_time, dir_index):
                            self.score_recorder.register_hit()
                            self.score_recorder_p2.register_miss()
                            to_remove.append(arrow)
                            break # only hit one arrow
                    for arrow in to_remove:
                        self.arrows[dir_index].remove(arrow)
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
                    elif event.key == pygame.K_r:
                        self.is_gen_random = not self.is_gen_random # toggle random generation
                    else:
                        if event.key == pygame.K_LEFT:
                            do_arrow_hit(DIR_DICT_INV["left"])
                            self.arrow_markers[0].is_pressed = True
                        elif event.key == pygame.K_DOWN:
                            do_arrow_hit(DIR_DICT_INV["down"])
                            self.arrow_markers[1].is_pressed = True
                        elif event.key == pygame.K_UP:
                            do_arrow_hit(DIR_DICT_INV["up"])
                            self.arrow_markers[2].is_pressed = True
                        elif event.key == pygame.K_RIGHT:
                            do_arrow_hit(DIR_DICT_INV["right"])
                            self.arrow_markers[3].is_pressed = True
                        elif event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_u:
                            self._spawn_arrow_now(0)
                            self.is_p2 = True
                            self.score_recorder_p2.register_miss() # cost 1
                        elif event.key == pygame.K_i:
                            self._spawn_arrow_now(1)
                            self.is_p2 = True
                            self.score_recorder_p2.register_miss() # cost 1
                        elif event.key == pygame.K_o:
                            self._spawn_arrow_now(2)
                            self.is_p2 = True
                            self.score_recorder_p2.register_miss() # cost 1
                        elif event.key == pygame.K_p:
                            self._spawn_arrow_now(3)
                            self.is_p2 = True
                            self.score_recorder_p2.register_miss() # cost 1
                        # else:
                        #     print(f"Key pressed: {event.key}, {pygame.key.name(event.key)}, {pygame.K_LEFT}")
                elif event.type == pygame.USEREVENT:
                    if "dir_index" in event.dict:
                        dir_index = event.dict["dir_index"]
                        print(f"Received event: dir_index={dir_index}")
                        self.arrow_markers[dir_index].is_pressed = True
                        # self.score_recorder.check_hit(current_time, event.dict["arrow_timestamp"], event.dict["dir_index"])
                        do_arrow_hit(dir_index)
            pygame.display.flip()
            self.clock.tick(60)

    def stop(self):
        """Stops the game loop"""
        self.running = False

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

    def _bluetooth_player1_callback(self, data: bytearray):
        """Callback for bluetooth messages"""
        print(f"Received message from player 1: {data}")
        EventBT_parse_message_and_send_events(data, self)
        
    def _bluetooth_player2_callback(self, data: bytearray):
        """Callback for bluetooth messages"""
        print(f"Received message from player 2: {data}")
        try:
            message_str = data.decode("ascii")
            hit_str_, i = message_str.split(" ")
            i = int(i) - 1
        except Exception as e:
            print(f"Error parsing message: {e}")
            return
        self._spawn_arrow_now(i)

    def _spawn_arrow_now(self, dir_index: int):
        """Spawns an arrow now"""
        time_offset = 60 / self.BPM * 4 / 4  
        self.spawn_arrow(DIR_DICT[dir_index], "white", time.perf_counter() + time_offset * dir_index)
        self.spawn_markers[dir_index].schedule_draw()

class ScoreRecorder:
    """Class to record the score of a player"""
    ACCEPTABLE_SOUNDS = [28, 35, 40, 44, 47, 52, 56, 59, 64]

    def __init__(self, initial_score: int = 0):
        """Class to record the score of a player"""
        self.score = initial_score
        self.combo = 0
        # self.tap_sound = pygame.mixer.Sound(RESOURCE_PATH / "GameplayAssist clap.ogg")
        self.current_sound_index = 0
        self.last_dir_index = 0
        self.tap_sounds = {"clap": pygame.mixer.Sound(RESOURCE_PATH / "GameplayAssist clap.ogg")}
        for i in self.ACCEPTABLE_SOUNDS:
            self.tap_sounds[f"piano_{i:03}"] = pygame.mixer.Sound(RESOURCE_PATH / "piano" / f"jobro__piano-ff-{i:03}.ogg")
            # print(f"Loaded piano_{i:03} at {RESOURCE_PATH / 'piano' / f'jobro__piano-ff-{i:03}.ogg'}")
    
    def check_hit(self, current_time: float, arrow_0_time: float, dir_index: int) -> bool:
        """Checks if the player hit an arrow. Returns True if the arrow was hit."""
        if abs(current_time - arrow_0_time) < 0.1:
            self.play_sound(dir_index)
            return True
        return False

    def play_sound(self, dir_index: int):
        """Plays a sound"""
        new_index = 0
        if dir_index == self.last_dir_index: # same
            new_index = self.current_sound_index
        else:
            new_index_offset = dir_index - self.last_dir_index
            if new_index_offset > 0: # right
                min_index = self.current_sound_index + new_index_offset
                min_index = min(min_index, len(self.ACCEPTABLE_SOUNDS)-2)
                max_index = len(self.ACCEPTABLE_SOUNDS)-1
                new_index = np.random.randint(min_index, max_index)
            else: # left
                min_index = 0
                max_index = self.current_sound_index + new_index_offset
                max_index = max(1, max_index)
                new_index = np.random.randint(min_index, max_index)

        sound = self.tap_sounds[f"piano_{self.ACCEPTABLE_SOUNDS[new_index]:03}"]
        sound.play(maxtime=500)
        # print(f"======\ndir_index: {dir_index}\nlast_dir_index: {self.last_dir_index},\ncurrent_sound_index: {self.current_sound_index},\nnew_index: {new_index}")
        self.last_dir_index = dir_index # update
        self.current_sound_index = new_index

    def register_hit(self, points: int = 1):
        """Registers a hit"""
        self.score += points
        self.combo += 1
    
    def register_miss(self, points: int = 1):
        """Registers a miss"""
        self.score -= points
        self.combo = 0

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
        self.is_pressed = False
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
        if self.is_pressed:
            pygame.draw.rect(screen, (255, 255, 255), (self.x, self.y, ARROW_SIZE, ARROW_SIZE), 3)
        screen.blit(self.img, (self.x, self.y))

    @staticmethod
    def _load_image():
        MarkerArrow.marker_img = pygame.image.load(RESOURCE_PATH / "ArrowMarker.png")
        MarkerArrow.marker_img = pygame.transform.scale(MarkerArrow.marker_img, (ARROW_SIZE, ARROW_SIZE))

class MarkerSpawn:
    """Class to represent an marker arrow spawn asset"""
    marker_img: pygame.Surface = None
    SHOWN_FRAMES = 5
    def __init__(self, direction: Literal["left","up","right","down"] = "left"):
        self.x = get_arrow_x(direction, WIDTH, ARROW_SIZE, WIDTH//2)
        # self.y = HEIGHT - ARROW_SIZE//2
        self.y = HEIGHT - 80
        self.draw_counter = 0
    
    def schedule_draw(self):
        self.draw_counter = MarkerSpawn.SHOWN_FRAMES
    
    def draw(self, screen: pygame.Surface):
        if self.draw_counter > 0:
            self.draw_counter -= 1
            screen.blit(MarkerSpawn.marker_img, (self.x, self.y))
    
    @staticmethod
    def _load_image():
        MarkerSpawn.marker_img = pygame.image.load(RESOURCE_PATH / "ArrowSpawn.png")
        MarkerSpawn.marker_img = pygame.transform.scale(MarkerSpawn.marker_img, (ARROW_SIZE, ARROW_SIZE))

class PlayerBtMarker:
    player1_img: pygame.Surface = None
    player2_img: pygame.Surface = None
    SIZE = 50
    def __init__(self, player: Literal["player1", "player2"]):
        self.x = 0
        self.y = HEIGHT - PlayerBtMarker.SIZE
        if player == "player1":
            self.img = PlayerBtMarker.player1_img
            self.x = 0
        elif player == "player2":
            self.img = PlayerBtMarker.player2_img
            self.x = WIDTH - PlayerBtMarker.SIZE
        else:
            raise ValueError(f"Invalid player {player}")
        
    def draw(self, screen: pygame.Surface):
        screen.blit(self.img, (self.x, self.y))
    
    @staticmethod
    def _load_images():
        PlayerBtMarker.player1_img = pygame.image.load(RESOURCE_PATH / "Player1.png")
        PlayerBtMarker.player1_img = pygame.transform.scale(PlayerBtMarker.player1_img, (PlayerBtMarker.SIZE, PlayerBtMarker.SIZE))
        PlayerBtMarker.player2_img = pygame.image.load(RESOURCE_PATH / "Player2.png")
        PlayerBtMarker.player2_img = pygame.transform.scale(PlayerBtMarker.player2_img, (PlayerBtMarker.SIZE, PlayerBtMarker.SIZE))
        

class BeatSoundMaker:
    beatTic: pygame.mixer.Sound = None
    beatTac: pygame.mixer.Sound = None
    def __init__(self):
        self.count = 0
    
    def play_beat_sound(self):
        """Plays a beat sound"""
        if self.count % 4 == 0:
            self.beatTac.play()
        else:
            self.beatTic.play()
        self.count += 1

    @staticmethod
    def _load_beat_sounds():
        BeatSoundMaker.beatTic = pygame.mixer.Sound(RESOURCE_PATH / "Tic.ogg")
        BeatSoundMaker.beatTac = pygame.mixer.Sound(RESOURCE_PATH / "Tac.ogg")



def EventBT_parse_message_and_send_events(message: bytearray, game) -> None:
    """Parses a bluetooth message to spawn the relevant events."""
    # decode bluetooth message as string as ascii
    try:
        message_str = message.decode("ascii")
        hit_str_, i = message_str.split(" ")
        i = int(i) - 1
    except Exception as e:
        print(f"Error parsing message: {e}")
        return 
    type_ = pygame.USEREVENT
    dict_ = {"dir_index": i}
    event = pygame.event.Event(type_, dict_)
    pygame.event.post(event)

if __name__ == "__main__":
    game = Stepmania()

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