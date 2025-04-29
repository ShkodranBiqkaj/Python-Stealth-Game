from .main_menu import Main_Menu
from .developer_options import DeveloperOptions
from .map_renderer import MapRenderer
import pygame
from Graphics.main_menu import SIZE_X,SIZE_Y


class MainGraphics:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
        self.start_menu = Main_Menu()
        self.developer_options = DeveloperOptions()

        # Default settings
        self.maze_difficulty = "hard"
        self.rows = 8
        self.cols = 8
        self.enemy_count = 2

        # Preload images
        self.crate_img = pygame.transform.scale(
            pygame.image.load("assets/walls.png").convert_alpha(), (40, 40)
        )
        self.hidden_img = pygame.transform.scale(
            pygame.image.load("assets/hidden_room.png").convert_alpha(), (40, 40)
        )
        self.key_img = pygame.transform.scale(
            pygame.image.load("assets/Key.png").convert_alpha(), (40, 40)
        )
        self.door_img = pygame.transform.scale(
            pygame.image.load("assets/Door_closed.png").convert_alpha(), (40, 40)
        )
        self.door_open_img = pygame.transform.scale(
            pygame.image.load("assets/Door_open.png").convert_alpha(), (40, 40)
        )

    def draw_pre_game(self):
        """Display menu and allow player to configure settings."""
        self.menu_choice = self.start_menu.show_main_menu()
        if self.menu_choice == 1:
            self.maze_difficulty, self.rows, self.cols, self.enemy_count = self.developer_options.draw_developer_options()

    def draw_map_in_game(
        self,
        border_tuples,
        matrix,
        grid_size,
        tile_size,
        player,
        enemies,
        overlay=True
    ):
        rows, cols = grid_size
        pixel_one_x, pixel_one_y = tile_size

        self.map_renderer = MapRenderer(
            border_tuples=border_tuples,
            matrix=matrix,
            grid_size=(rows, cols),
            tile_size=(pixel_one_x, pixel_one_y),
            crate_img=self.crate_img,
            hidden_img=self.hidden_img,
            key_img=self.key_img,
            door_img=self.door_img,
            door_open_img=self.door_open_img,
            enemies=enemies,
            player=player,
            screen=self.screen,
            overlay=overlay
        )
        self.map_renderer.draw_map()

    def get_logic_creation_attributes(self):
        """Provide the logic setup needed for the main game."""
        return self.maze_difficulty, self.rows, self.cols, self.enemy_count
