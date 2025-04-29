import pygame
from Graphics.main_graphics  import MainGraphics
from Logic.logic_setup      import LogicSetup
from Graphics.post_game_menu import PostGameMenu
from Graphics.pre_game_tip  import PreGameTip
from Graphics.pause         import Pause

def main():
    pygame.init()
    screen = pygame.display.set_mode((1000, 750))
    clock  = pygame.time.Clock()

    gfx       = MainGraphics()
    post_menu = PostGameMenu(screen, clock)
    app_running = True

    while app_running:
        gfx.draw_pre_game()
        if gfx.menu_choice == 2:  #Quit
            break

        in_game = True
        while in_game and app_running:
            logic = LogicSetup(
                gfx.maze_difficulty,
                gfx.rows,
                gfx.cols,
                gfx.enemy_count
            )

            # show the one-second “Press SPACE to pause” tip
            PreGameTip(screen).show()

            logic.generate_game()
            bt, mat, grid_size, tile_size, key_pos, door_pos, player, enemies = \
                logic.get_graphics_attributes()

            # initialize the map_renderer for this level
            gfx.draw_map_in_game(bt, mat, grid_size, tile_size, player, enemies)

            # ─── PLAY LOOP ───────────────────────────────────────────────
            result = {'won': False, 'lost': False}
            while True:
                # 1) Poll events
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        app_running = False
                        in_game     = False
                    elif e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                        # Pause overlay (leaves the last frame on screen)
                        try:
                            Pause(screen).draw_pause()
                        except KeyboardInterrupt:
                            # Player pressed Q in the pause → back to main menu
                            in_game = False
                            break

                if not app_running or not in_game:
                    break

                # 2) Handle input & update logic
                logic.handle_input(pygame.key.get_pressed())
                result = logic.update()

                # 3) Draw the current game frame
                gfx.map_renderer.draw_map()

                # 4) Cap to 60fps
                clock.tick(60)

                # 5) Check for end-of-level
                if result['won'] or result['lost']:
                    break

            if not app_running:
                break

            # ─── POST-GAME MENU ─────────────────────────────────────────
            choice = post_menu.show(won=result['won'])
            if choice == 'next':
                # bump up difficulty/size for next run
                gfx.rows += 1
                gfx.cols += 1
                continue  # stay in_game
            if choice == 'exit':
                app_running = False
            # for 'new' or 'menu' we just fall through and re-show PRE-GAME
            in_game = False

    pygame.quit()

if __name__ == '__main__':
    main()
