import sys
import pygame

from config import (FPS, STATE_START, STATE_AI_INTRO, STATE_AI_TURN,
                    STATE_PLAYER_INTRO, STATE_PLAYER_TURN,
                    STATE_GAME_OVER, STATE_END,
                    TRANSITION_DURATION)
from core.map import GalaxyMap
from agents.player import Player
from agents.ai_astar import AStarAgent as AIAgent
from ui.renderer import Renderer


def new_game():
    galaxy   = GalaxyMap()
    player   = Player(galaxy)
    ai_agent = AIAgent(galaxy)
    return galaxy, player, ai_agent


def main():
    pygame.init()
    clock    = pygame.time.Clock()
    renderer = Renderer()

    galaxy, player, ai_agent = new_game()

    state          = STATE_START
    prev_score     = 0
    prev_ai_score  = 0   # track AI score for popup spawning
    show_info      = False
    paused         = False   # P key toggles pause
    transition_start = 0

    while True:
        tick = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    if show_info:
                        show_info = False
                    else:
                        pygame.quit(); sys.exit()

                
                elif state == STATE_START and event.key == pygame.K_RETURN:
                    state = STATE_AI_INTRO
                    transition_start = tick

                elif state == STATE_END and event.key == pygame.K_RETURN:
                    galaxy, player, ai_agent = new_game()
                    state            = STATE_START
                    prev_score       = 0
                    show_info        = False


                elif (event.key == pygame.K_p
                      and state in (STATE_AI_TURN, STATE_PLAYER_TURN)):
                    paused    = not paused
                    show_info = False   # close info overlay when pausing

                elif (event.key == pygame.K_i
                      and state in (STATE_AI_TURN, STATE_PLAYER_TURN)
                      and not paused):
                    show_info = not show_info

            
                elif state == STATE_PLAYER_TURN and not show_info and not paused:
                    player.handle_input(event, galaxy, renderer=renderer)

        
        elapsed = tick - transition_start

        if paused:
            pass   # frozen — no updates

        elif state == STATE_AI_INTRO:
            if elapsed >= TRANSITION_DURATION:
                state = STATE_AI_TURN

        elif state == STATE_AI_TURN:
            ai_agent.step(galaxy)

            # Spawn popup when AI collects a resource
            if ai_agent.score > prev_ai_score:
                gained = ai_agent.score - prev_ai_score
                body   = galaxy.get(ai_agent.col, ai_agent.row)
                rtype  = (body.resource.rtype
                          if body and body.resource else "common")
                renderer.spawn_popup(ai_agent.col, ai_agent.row,
                                     gained, rtype, is_ai=True)
            prev_ai_score = ai_agent.score

            if not ai_agent.alive:
                galaxy.reset_ai_reveal_for_player()
                state            = STATE_PLAYER_INTRO
                transition_start = tick
                prev_score       = player.score
                prev_ai_score    = 0

        elif state == STATE_PLAYER_INTRO:
            if elapsed >= TRANSITION_DURATION:
                state = STATE_PLAYER_TURN

        elif state == STATE_PLAYER_TURN:
            if player.score > prev_score:
                gained = player.score - prev_score
                body   = galaxy.get(player.col, player.row)
                rtype  = (body.resource.rtype
                          if body and body.resource else "common")
                renderer.spawn_popup(player.col, player.row, gained, rtype)
            prev_score = player.score

            if not player.alive:
                state = STATE_GAME_OVER
                transition_start = tick

        elif state == STATE_GAME_OVER:
            if elapsed >= TRANSITION_DURATION:
                state = STATE_END


        if state == STATE_START:
            renderer.draw_start_screen()

        elif state == STATE_AI_INTRO:
            renderer.draw_transition(
                "AI AGENT EXPLORATION",
                "Watch the AI navigate the galaxy using A* pathfinding...",
                COLOR_AI=True
            )

        elif state == STATE_AI_TURN:
            renderer.draw_frame(galaxy, player, ai_agent, tick, phase="ai")

        elif state == STATE_PLAYER_INTRO:
            renderer.draw_transition(
                "YOUR EXPLORATION BEGINS",
                "Use what you observed and your intuition. Good luck!",
                COLOR_AI=False
            )

        elif state == STATE_PLAYER_TURN:
            renderer.draw_frame(galaxy, player, ai_agent, tick, phase="player")

        elif state == STATE_GAME_OVER:
            renderer.draw_transition(
                "EXPLORATION COMPLETE",
                f"Player: {player.score} pts   |   AI Agent: {ai_agent.score} pts",
                COLOR_AI=None
            )

        elif state == STATE_END:
            renderer.draw_end_screen(player, ai_agent)

        if show_info and state in (STATE_AI_TURN, STATE_PLAYER_TURN):
            renderer.draw_info_overlay()

        if paused and state in (STATE_AI_TURN, STATE_PLAYER_TURN):
            renderer.draw_pause_overlay()

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()