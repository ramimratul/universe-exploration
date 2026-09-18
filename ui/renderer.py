# =======================================#
# ui/renderer.py — Pygame drawing engine
# =======================================#

import math
import pygame
import random
from typing import Optional, Tuple, List



from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE,
    GRID_OFFSET_X, GRID_OFFSET_Y, GRID_COLS, GRID_ROWS,
    HUD_X, HUD_WIDTH,
    COLOR_BG, COLOR_GRID_LINE, COLOR_FOG, COLOR_FOG_PARTIAL,
    COLOR_STAR, COLOR_PLANET, COLOR_EXOPLANET, COLOR_SATELLITE,
    COLOR_ASTEROID, COLOR_COMET,
    COLOR_RESOURCE_COMMON, COLOR_RESOURCE_RARE,
    COLOR_RESOURCE_EXOTIC, COLOR_DISCOVERY,
    COLOR_PLAYER, COLOR_AI, COLOR_HAZARD,
    COLOR_HUD_BG, COLOR_HUD_TEXT, COLOR_HUD_ACCENT,
    COLOR_WHITE, COLOR_DIMWHITE,
    FONT_SIZE_LARGE, FONT_SIZE_MEDIUM, FONT_SIZE_SMALL,
    FOG_HIDDEN, FOG_PARTIAL, FOG_REVEALED,
    BODY_STAR, BODY_PLANET, BODY_EXOPLANET, BODY_SATELLITE,
    BODY_ASTEROID, BODY_COMET,
    RESOURCE_COMMON, RESOURCE_RARE, RESOURCE_EXOTIC, RESOURCE_DISCOVERY,
    RESOURCE_VALUES,
)

from core.map import GalaxyMap


## Colour maps

BODY_COLORS = {
    BODY_STAR:      COLOR_STAR,
    BODY_PLANET:    COLOR_PLANET,
    BODY_EXOPLANET: COLOR_EXOPLANET,
    BODY_SATELLITE: COLOR_SATELLITE,
    BODY_ASTEROID:  COLOR_ASTEROID,
    BODY_COMET:     COLOR_COMET,
}

RESOURCE_COLORS = {
    RESOURCE_COMMON:    COLOR_RESOURCE_COMMON,
    RESOURCE_RARE:      COLOR_RESOURCE_RARE,
    RESOURCE_EXOTIC:    COLOR_RESOURCE_EXOTIC,
    RESOURCE_DISCOVERY: COLOR_DISCOVERY,
}

## Symbols
RESOURCE_SYMBOLS = {
    RESOURCE_COMMON:    "*",
    RESOURCE_RARE:      "<>",
    RESOURCE_EXOTIC:    "**",
    RESOURCE_DISCOVERY: "!!",
}

RESOURCE_LABELS = {
    RESOURCE_COMMON:    "CMN",
    RESOURCE_RARE:      "RARE",
    RESOURCE_EXOTIC:    "EXT",
    RESOURCE_DISCOVERY: "DISC",
}



def _cell_rect(col: int, row: int) -> pygame.Rect:
    x = GRID_OFFSET_X + col * CELL_SIZE
    y = GRID_OFFSET_Y + row * CELL_SIZE
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

def _cell_center(col: int, row: int) -> Tuple[int, int]:
    r = _cell_rect(col, row)
    return r.centerx, r.centery

def _dim(color: tuple, factor: float) -> tuple:
    """Darken a colour by multiplying each channel by factor (0.0–1.0)."""
    return tuple(max(0, min(255, int(c * factor))) for c in color)

def _add(color: tuple, amount: int) -> tuple:
    """Brighten a colour by adding to each channel."""
    return tuple(max(0, min(255, c + amount)) for c in color)


## Floating popup

class FloatingText:
    """Floating score popup — shown when player or AI collects a resource."""
    def __init__(self, text: str, x: int, y: int, color: tuple,
                 big: bool = False):
        self.text  = text
        self.x     = float(x)
        self.y     = float(y)
        self.color = color
        self.alpha = 255
        self.alive = True
        self.big   = big   # big = discovery/exotic popup
        self.drift = random.uniform(-0.4, 0.4)
        self.speed = 1.8 if big else 1.3

    def update(self):
        self.y     -= self.speed
        self.x     += self.drift
        self.alpha -= 3 if self.big else 4
        if self.alpha <= 0:
            self.alive = False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font,
             font_big: pygame.font.Font = None):
        if not self.alive:
            return
        f = font_big if (self.big and font_big) else font
        # Glow/shadow layers — outer glow, dark shadow, bright text
        layers = [
            (0, 0,  _dim(self.color, 0.4), self.alpha // 2),   # glow
            (2, 2,  (0, 0, 0),             self.alpha),          # shadow
            (0, 0,  self.color,             self.alpha),          # main
        ]
        for off_x, off_y, color, alpha in layers:
            s = f.render(self.text, True, color)
            s.set_alpha(alpha)
            screen.blit(s, (int(self.x - s.get_width()//2 + off_x),
                            int(self.y + off_y)))


## Main Renderer
#-----------------

class Renderer:
    """
    Owns the Pygame screen and draws everything each frame.
    """

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0)
        pygame.display.set_caption("Universe Exploration")

        self.font_large  = pygame.font.SysFont("Verdana", 64,  bold=True)
        self.font_hud  = pygame.font.SysFont("Verdana", 32,  bold=True)
        self.font_medium = pygame.font.SysFont("Verdana", 22)
        self.font_small  = pygame.font.SysFont("Verdana", 18)
        self.font_tiny   = pygame.font.SysFont("courier", 14)

        self.scan_pulse_pos:  Optional[Tuple[int, int]] = None
        self.scan_pulse_max:  int = 0
        self.scan_pulse_tick: int = 0

        self.popups: List[FloatingText] = []

        self._bg_stars  = self._build_bg_stars()
        self._fog_stars = self._build_fog_stars()



    def _build_bg_stars(self):
        import random
        stars = []
        for _ in range(250): 
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            
            bright = random.randint(50, 150)
            size = 1 if random.random() > 0.1 else 2
            phase = random.uniform(0, 2 * math.pi)
            tint = random.randint(0, 1)
            
            stars.append((x, y, bright, size, phase, tint))
        return stars

    def _draw_bg_stars(self, tick: int):
        for (x, y, bright, size, phase, tint) in self._bg_stars:
            t = tick / 1400.0
            alpha = int(bright + 30 * math.sin(t + phase))
            alpha = max(30, min(210, alpha))
            
            if tint == 0:
                color = (alpha - 20, alpha - 10, min(255, alpha + 60))
            else:
                color = (min(255, alpha + 20), alpha, alpha - 15)
                
            pygame.draw.circle(self.screen, color, (x, y), size)
    
    
    def _build_fog_stars(self):
        """
        Randomly scattered faint stars across the grid area.
        """
        import random as _rnd
        _rnd.seed(99)
        grid_w = GRID_COLS * CELL_SIZE
        grid_h = GRID_ROWS * CELL_SIZE
        stars  = []
        for _ in range(400):
            x      = _rnd.randint(0, grid_w - 1)
            y      = _rnd.randint(0, grid_h - 1)
            bright = _rnd.randint(35, 90)
            tint   = _rnd.randint(0, 2)
            stars.append((x, y, bright, tint))
        return stars

    def _draw_fog_stars(self):
        for (x, y, bright, tint) in self._fog_stars:
            if tint == 0:
                color = (bright - 5, bright, min(255, bright + 30)) 
            elif tint == 1:
                color = (bright, bright, bright)
            else:
                color = (min(255, bright + 15), bright, bright - 8)
            color = tuple(max(0, c) for c in color)
            pygame.draw.circle(self.screen, color, (x, y), 1)

    ## Main draw call

    def draw_frame(self, galaxy: GalaxyMap, player, ai_agent,
                   tick: int, phase: str = "player") -> None:
        self.screen.fill(COLOR_BG)
        self._draw_bg_stars(tick)

        ###
        map_w = GRID_COLS * CELL_SIZE
        map_h = GRID_ROWS * CELL_SIZE
        map_rect = pygame.Rect(GRID_OFFSET_X - 80, GRID_OFFSET_Y - 20, map_w + 100, map_h + 40)

        pygame.draw.rect(self.screen, (10, 15, 30), map_rect)
        pygame.draw.rect(self.screen, (30, 45, 70), map_rect, 2)
        pygame.draw.line(self.screen, (70, 100, 150), map_rect.topleft, map_rect.topright, 1)


        self._draw_grid(galaxy, tick)
        self._draw_fog_stars()
        self._draw_scan_pulse(tick)
        self._draw_ships(player, ai_agent, phase)
        self._draw_hud(player, ai_agent, phase)
        self._update_and_draw_popups()

    ## Grid

    def _draw_grid(self, galaxy: GalaxyMap, tick: int):
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                self._draw_cell(galaxy, col, row, tick)

    
    def _draw_cell(self, galaxy, col, row, tick):
        fog  = galaxy.get_fog(col, row, who='player')
        rect = _cell_rect(col, row)
        body = galaxy.get(col, row)

        if fog == FOG_HIDDEN:
            pygame.draw.rect(self.screen, COLOR_FOG, rect)
            return

        bg_color = COLOR_FOG_PARTIAL if fog == FOG_PARTIAL else (25, 42, 95)
        pygame.draw.rect(self.screen, bg_color, rect)

        if body is None or body.is_empty: return
        cx, cy = _cell_center(col, row)
        color = BODY_COLORS.get(body.btype, COLOR_WHITE)
        if fog == FOG_PARTIAL: color = _dim(color, 0.35)

        self._draw_body(body.btype, cx, cy, color, tick)

        if body.is_hazard and fog == FOG_REVEALED:
            self._draw_hazard_marker(rect)

        if body.has_resource:
            if fog == FOG_REVEALED:
                self._draw_resource_indicator(body, rect, tick)
            else:
                self._draw_resource_ghost(body, rect)

    def _draw_resource_indicator(self, body, rect, tick):
        """Resource badge — bright and eye-catching, dims when collected."""
        rtype   = body.resource.rtype
        rcolor  = RESOURCE_COLORS.get(rtype, COLOR_WHITE)
        rsym    = RESOURCE_SYMBOLS.get(rtype, "?")
        p_done  = body.resource.collected_player
        ai_done = body.resource.collected_ai
        is_disc = (rtype == RESOURCE_DISCOVERY)
        is_exotic = (rtype == RESOURCE_EXOTIC)
        is_rare = (rtype in (RESOURCE_DISCOVERY, RESOURCE_EXOTIC))

        # Dim if collected by EITHER player or AI
        # 0.40 brightness — still recognisable, clearly dimmed
        collected = p_done or ai_done
        if collected:
            draw_color = _dim(rcolor, 0.40)
            bg_alpha   = 90
        else:
            draw_color = rcolor
            bg_alpha   = 220

        # Font sizing — clear visual hierarchy:
        #   discovery   → font_hud    (32px bold — special, unmissable)
        #   exotic      → font_medium (22px — clearly bigger than common/rare)
        #   rare/common → font_small  (18px — readable, not overwhelming)
        if is_disc:
            font = self.font_hud
        elif is_exotic:
            font = self.font_medium
        else:
            font = self.font_small
        sym_surf = font.render(rsym, True, draw_color)

        if is_disc:
            pad_x, pad_y = 10, 6   # discovery — tight pad, font is already big
        elif is_exotic:
            pad_x, pad_y = 8,  5   # exotic
        else:
            pad_x, pad_y = 6,  4   # rare / common
        tw = sym_surf.get_width()  + pad_x
        th = sym_surf.get_height() + pad_y
        tx = rect.right  - tw + 2
        ty = rect.bottom - th + 2
        tag_rect = pygame.Rect(tx, ty, tw, th)

        # Glow — only when uncollected
        if not collected:
            pulse = 0.5 + 0.5 * math.sin(tick / 300.0)
            if is_disc:
                # Discovery — large dramatic glow
                glow_r     = int(22 + 8 * pulse)
                glow_alpha = int(70 + 50 * pulse)
            elif is_exotic:
                # Exotic — smaller, subtler glow (clearly less than discovery)
                glow_r     = int(12 + 4 * pulse)
                glow_alpha = int(40 + 25 * pulse)
            else:
                glow_r     = 0   # rare and common — no glow

            if glow_r > 0:
                glow_surf = pygame.Surface((glow_r*2, glow_r*2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*rcolor, glow_alpha),
                                   (glow_r, glow_r), glow_r)
                gcx = tx + tw // 2
                gcy = ty + th // 2
                self.screen.blit(glow_surf, (gcx - glow_r, gcy - glow_r))

        # Discovery animated brackets (uncollected only)
        if is_disc and not collected:
            self._draw_discovery_brackets(tag_rect, rcolor, tick)

        # Background badge
        bg = pygame.Surface((tw, th), pygame.SRCALPHA)
        bg.fill((0, 0, 0, bg_alpha))
        self.screen.blit(bg, (tx, ty))

        # Left accent bar — thicker for rarer tiers
        bar_w = 5 if is_disc else (3 if is_exotic else 2)
        pygame.draw.rect(self.screen, draw_color, (tx, ty, bar_w, th))

        # Border (uncollected only)
        if not collected:
            pygame.draw.rect(self.screen, _dim(draw_color, 0.5),
                             (tx, ty, tw, th), 1)

        # Symbol
        self.screen.blit(sym_surf, (tx + pad_x//2 + 2, ty + pad_y//2))

    def _draw_discovery_brackets(self, rect, color, tick):
        breath = int(3 * math.sin(tick / 80.0))
        b_rect = rect.inflate(8 + breath, 8 + breath)
        l_len = 8 
        for pts in [
            [(b_rect.left, b_rect.top + l_len), (b_rect.left, b_rect.top), (b_rect.left + l_len, b_rect.top)],
            [(b_rect.right - l_len, b_rect.top), (b_rect.right, b_rect.top), (b_rect.right, b_rect.top + l_len)],
            [(b_rect.left, b_rect.bottom - l_len), (b_rect.left, b_rect.bottom), (b_rect.left + l_len, b_rect.bottom)],
            [(b_rect.right - l_len, b_rect.bottom), (b_rect.right, b_rect.bottom), (b_rect.right, b_rect.bottom - l_len)]
        ]:
            pygame.draw.lines(self.screen, color, False, pts, 3)

    def _draw_resource_ghost(self, body, rect):
        """Resource hint in partial fog — slightly more visible than before."""
        rtype = body.resource.rtype
        rsym  = RESOURCE_SYMBOLS.get(rtype, "?")
        # Brighter ghost — 40% brightness so player can see resource type
        c     = _dim(RESOURCE_COLORS.get(rtype, (255,255,255)), 0.40)
        s     = self.font_small.render(rsym, True, c)
        self.screen.blit(s, (rect.right - s.get_width() - 3,
                             rect.bottom - s.get_height() - 3))

    def _draw_hazard_marker(self, rect):
        size = 26
        pts = [(rect.left, rect.top), (rect.left + size, rect.top), (rect.left, rect.top + size)]
        pygame.draw.polygon(self.screen, (0, 0, 0), [(p[0]+1, p[1]+1) for p in pts])
        pygame.draw.polygon(self.screen, (230, 30, 30), pts)
        self.screen.blit(self.font_medium.render("!", True, (255, 255, 255)), (rect.left + 3, rect.top - 1))

    ## Celestial body drawing

    def _draw_body(self, btype: str, cx: int, cy: int, color: tuple, tick: int):
        if btype == BODY_STAR:
            self._draw_star(cx, cy, color, tick)
        elif btype == BODY_PLANET:
            self._draw_planet(cx, cy, color, tick)
        elif btype == BODY_EXOPLANET:
            self._draw_exoplanet(cx, cy, color, tick)
        elif btype == BODY_SATELLITE:
            self._draw_satellite(cx, cy, color)
        elif btype == BODY_ASTEROID:
            self._draw_asteroid(cx, cy, color)
        elif btype == BODY_COMET:
            self._draw_comet(cx, cy, color, tick)

    #########
    def _draw_hud_brackets(self, rect, color, thickness=2, length=20):
        """Draws sci-fi corner brackets around a rectangle."""
        pygame.draw.lines(self.screen, color, False, 
                        [(rect.left, rect.top + length), (rect.left, rect.top), (rect.left + length, rect.top)], thickness)
        
        pygame.draw.lines(self.screen, color, False, 
                        [(rect.right - length, rect.top), (rect.right, rect.top), (rect.right, rect.top + length)], thickness)
        
        pygame.draw.lines(self.screen, color, False, 
                        [(rect.left, rect.bottom - length), (rect.left, rect.bottom), (rect.left + length, rect.bottom)], thickness)
        
        pygame.draw.lines(self.screen, color, False, 
                        [(rect.right - length, rect.bottom), (rect.right, rect.bottom), (rect.right, rect.bottom - length)], thickness)
    
    def _draw_star(self, cx, cy, color, tick):
        """Large glowing star with a pulsing outer halo and bright hot core."""
        pulse   = 0.5 + 0.5 * math.sin(tick / 650.0)
        r_outer = 17 + int(2 * pulse)
        r_mid   = 11                     
        r_core  = 5                      

        glow_size = r_outer + 7
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*_dim(color, 0.35), 55),
                           (glow_size, glow_size), glow_size)
        self.screen.blit(glow_surf, (cx - glow_size, cy - glow_size))

        pygame.draw.circle(self.screen, _dim(color, 0.55), (cx, cy), r_outer)
        pygame.draw.circle(self.screen, _dim(color, 0.8), (cx, cy), r_mid)
        pygame.draw.circle(self.screen, _add(color, 50), (cx, cy), r_core)
        pygame.draw.circle(self.screen, COLOR_WHITE, (cx, cy), 2)

    def _draw_planet(self, cx, cy, color, tick):
        r = 15
        pygame.draw.circle(self.screen, _dim(color, 0.45), (cx, cy), r)
        pygame.draw.circle(self.screen, color, (cx - 1, cy - 1), r - 2)
        pygame.draw.circle(self.screen, _add(color, 65), (cx - 4, cy - 4), r // 3)
        pygame.draw.ellipse(self.screen, _add(color, 60),
                            (cx - r - 6, cy - 4, (r + 6) * 2, 8), 2)

    def _draw_exoplanet(self, cx, cy, color, tick):
        r = 13
        pygame.draw.circle(self.screen, _dim(color, 0.5), (cx, cy), r)
        pygame.draw.circle(self.screen, color, (cx, cy), r - 2)
        pygame.draw.circle(self.screen, _add(color, 70), (cx - 3, cy - 3), 4)
        angle = tick / 900.0
        ox = cx + int((r + 7) * math.cos(angle))
        oy = cy + int((r + 7) * math.sin(angle) * 0.35)
        pygame.draw.circle(self.screen, _add(color, 90), (ox, oy), 3)

    def _draw_satellite(self, cx, cy, color):
        s = 11   
        pts = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
        pygame.draw.polygon(self.screen, color, pts)
        pygame.draw.polygon(self.screen, _add(color, 40), pts, 1)
        panel = _dim(color, 0.6)
        pygame.draw.line(self.screen, panel, (cx - s - 9, cy - 2), (cx - s, cy - 2), 3)
        pygame.draw.line(self.screen, panel, (cx + s, cy - 2), (cx + s + 9, cy - 2), 3)

    def _draw_asteroid(self, cx, cy, color):
        offsets = [2, 5, -1, 4, 1, 5]
        pts = []
        for i in range(6):
            angle = math.radians(i * 60 + 8)
            r     = 11 + offsets[i]
            pts.append((cx + int(r * math.cos(angle)),
                         cy + int(r * math.sin(angle))))
        pygame.draw.polygon(self.screen, _dim(color, 0.65), pts)
        pygame.draw.polygon(self.screen, color, pts, 1)
        pygame.draw.circle(self.screen, _dim(color, 0.35), (cx - 3, cy - 2), 3)
        pygame.draw.circle(self.screen, _dim(color, 0.35), (cx + 3, cy + 2), 2)

    def _draw_comet(self, cx, cy, color, tick):
        for i in range(7):
            offset = i * 5 + 4
            tc     = _dim(color, max(0.08, 0.6 - i * 0.09))
            pygame.draw.line(self.screen, tc,
                             (cx, cy), (cx - offset, cy + offset // 2),
                             max(1, 4 - i))
        
        pygame.draw.circle(self.screen, _add(color, 55), (cx, cy), 7)
        pygame.draw.circle(self.screen, COLOR_WHITE,      (cx, cy), 3)

    ## Ships

    def _draw_ships(self, player, ai_agent, phase="player"):
        # During AI turn only show AI ship
        # During player turn show both
        if phase == "ai":
            self._draw_ai_ship(ai_agent.col, ai_agent.row)
        else:
            self._draw_player_ship(player.col, player.row)
            self._draw_ai_ship(ai_agent.col, ai_agent.row)

    def _draw_player_ship(self, col, row):
        cx, cy = _cell_center(col, row)
        s = CELL_SIZE // 2 - 5
        glow = pygame.Surface((s * 4, s * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*COLOR_PLAYER, 35), (s * 2, s * 2), s * 2)
        self.screen.blit(glow, (cx - s * 2, cy - s * 2))
        pts = [(cx, cy - s), (cx - s, cy + s - 2), (cx + s, cy + s - 2)]
        pygame.draw.polygon(self.screen, COLOR_PLAYER, pts)
        pygame.draw.polygon(self.screen, COLOR_WHITE,  pts, 1)

    def _draw_ai_ship(self, col, row):
        cx, cy = _cell_center(col, row)
        s = CELL_SIZE // 2 - 5
        glow = pygame.Surface((s * 4, s * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*COLOR_AI, 35), (s * 2, s * 2), s * 2)
        self.screen.blit(glow, (cx - s * 2, cy - s * 2))
        pts = [(cx, cy + s), (cx - s, cy - s + 2), (cx + s, cy - s + 2)]
        pygame.draw.polygon(self.screen, COLOR_AI, pts)
        pygame.draw.polygon(self.screen, COLOR_WHITE, pts, 1)


    def trigger_scan_pulse(self, col: int, row: int, radius: int) -> None:
        self.scan_pulse_pos  = _cell_center(col, row)
        self.scan_pulse_max  = radius * CELL_SIZE
        self.scan_pulse_tick = pygame.time.get_ticks()

    def _draw_scan_pulse(self, tick: int) -> None:
        if self.scan_pulse_pos is None:
            return
        elapsed  = tick - self.scan_pulse_tick
        duration = 700
        if elapsed > duration:
            self.scan_pulse_pos = None
            return
        progress = elapsed / duration
        radius   = int(progress * self.scan_pulse_max)
        alpha    = int(220 * (1 - progress))
        color    = (0, min(255, alpha + 50), min(255, alpha + 180))
        if radius > 0:
            pygame.draw.circle(self.screen, color, self.scan_pulse_pos, radius, 2)
            if radius > 6:
                pygame.draw.circle(self.screen, _dim(color, 0.5),
                                   self.scan_pulse_pos, max(2, radius - 6), 1)


    def spawn_popup(self, col: int, row: int, value: int, rtype: str,
                    is_ai: bool = False):
        cx, cy = _cell_center(col, row)
        color  = RESOURCE_COLORS.get(rtype, COLOR_WHITE)
        # AI popups offset slightly upward and labeled
        offset = -24 if is_ai else -10
        label  = f"AI +{value}" if is_ai else f"+{value}"
        # Big popup only for discovery (250pts) — exotic stays medium size
        big    = value >= 250
        self.popups.append(FloatingText(label, cx, cy + offset, color, big=big))

    def _update_and_draw_popups(self):
        for popup in self.popups:
            popup.update()
            popup.draw(self.screen, self.font_medium, self.font_hud)
        self.popups = [p for p in self.popups if p.alive]


    ## HUD
    #--------

    #########
    def _draw_hud(self, player, ai_agent, phase) -> None:
        """Main gameplay sidebar with balanced spacing."""
        hx = SCREEN_WIDTH - HUD_WIDTH + 20 
        y = 30 ## Initial top margin

        t1 = self.font_hud.render("UNIVERSE", True, COLOR_HUD_ACCENT)
        t2 = self.font_hud.render("EXPLORATION", True, COLOR_HUD_ACCENT)
        self.screen.blit(t1, (hx, y))
        y += t1.get_height() - 5
        self.screen.blit(t2, (hx, y))
        y += t2.get_height() + 15
        pygame.draw.line(self.screen, COLOR_HUD_ACCENT, (hx, y), (SCREEN_WIDTH - 20, y), 2)
        
        y += 45 

        y = self._draw_agent_info(hx, y, "[ PLAYER ]", player, COLOR_PLAYER)
        
        ## gap between Player and AI
        y += 50 

        y = self._draw_agent_info(hx, y, "[ AI AGENT ]", ai_agent, COLOR_AI)
        
        alg_surf = self.font_tiny.render("[A* Pathfinding Active]", True, COLOR_HUD_ACCENT)
        self.screen.blit(alg_surf, (hx + 5, y))
        
        ## Gap before the process log
        y += 60 

        ## Agent Process Log
        hdr = self.font_medium.render("AGENT PROCESS", True, (255, 255, 255))
        self.screen.blit(hdr, (hx, y))
        y += 35
        
        decision = getattr(ai_agent, 'decision_text', 'Scanning...')
        words = decision.split()
        line = ""
        for word in words:
            if self.font_small.size(line + word)[0] < (HUD_WIDTH - 40):
                line += word + " "
            else:
                s = self.font_small.render(line, True, (255, 255, 255))
                self.screen.blit(s, (hx + 5, y))
                y += 22
                line = word + " "
        s = self.font_small.render(line, True, (255, 255, 255))
        self.screen.blit(s, (hx + 5, y))

    def _draw_agent_info(self, x, y, title, agent, color):
        hdr = self.font_medium.render(title, True, color)
        self.screen.blit(hdr, (x, y))
        y += 40

        ## Stats Rows
        stats = [
            ("Fuel", str(int(agent.fuel))),
            ("Score", str(agent.score)),
            ("Res", str(agent.resources_collected))
        ]
        
        for label, val in stats:
            lbl_s = self.font_small.render(label + ":", True, (255, 255, 255))
            val_s = self.font_medium.render(val, True, (255, 220, 80) if label == "Score" else (255, 255, 255))
            
            self.screen.blit(lbl_s, (x + 5, y))
            vx = SCREEN_WIDTH - val_s.get_width() - 25
            self.screen.blit(val_s, (vx, y - 5))
            y += 35

        ## Fuel Bar
        y += 5
        bar_w = HUD_WIDTH - 40
        fill = int(bar_w * (max(0, agent.fuel) / agent.max_fuel))
        pygame.draw.rect(self.screen, (15, 15, 35), (x + 5, y, bar_w, 12))
        pygame.draw.rect(self.screen, color, (x + 5, y, fill, 12))
        pygame.draw.rect(self.screen, (100, 100, 120), (x + 5, y, bar_w, 12), 1)
        
        return y + 25


    def _draw_fuel_bar(self, x, y, fuel, max_fuel, color):
        bar_w  = HUD_WIDTH - 20
        bar_h  = 14
        filled = int(bar_w * max(0, fuel) / max(1, max_fuel))

        pygame.draw.rect(self.screen, (18, 22, 48), (x, y, bar_w, bar_h))
        if filled > 0:
            pygame.draw.rect(self.screen, color, (x, y, filled, bar_h))
            hi = _add(color, 60)
            pygame.draw.rect(self.screen, hi, (x, y, filled, 2))
        pygame.draw.rect(self.screen, _add(color, 20), (x, y, bar_w, bar_h), 1)


    def _draw_grid_border(self):
        border = pygame.Rect(
            GRID_OFFSET_X - 2, GRID_OFFSET_Y - 2,
            GRID_COLS * CELL_SIZE + 4, GRID_ROWS * CELL_SIZE + 4,
        )
        pygame.draw.rect(self.screen, COLOR_HUD_ACCENT, border, 2)

    ## Transition screen

    def draw_transition(self, title: str, subtitle: str,
                        COLOR_AI=None) -> None:
        
        self.screen.fill(COLOR_BG)
        tick = pygame.time.get_ticks()
        self._draw_bg_stars(tick)

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2

        _color_ai = (255, 100, 80)   #### same as config COLOR_AI
        if COLOR_AI is True:
            color = _color_ai
        elif COLOR_AI is False:
            color = COLOR_PLAYER
        else:
            color = COLOR_HUD_ACCENT

        ## Pulsing glow circle behind title
        pulse = 0.5 + 0.5 * math.sin(tick / 400.0)
        glow_r = int(120 + 20 * pulse)
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*_dim(color, 0.15), 60),
                           (glow_r, glow_r), glow_r)
        self.screen.blit(glow_surf, (cx - glow_r, cy - glow_r - 20))

        t_surf = self.font_large.render(title, True, color)
        self.screen.blit(t_surf, t_surf.get_rect(center=(cx, cy - 20)))

        pygame.draw.line(self.screen, _dim(color, 0.5),
                         (cx - 250, cy + 15), (cx + 250, cy + 15), 1)

        s_surf = self.font_medium.render(subtitle, True, COLOR_HUD_TEXT)
        self.screen.blit(s_surf, s_surf.get_rect(center=(cx, cy + 40)))

        dot_y = cy + 85
        for i in range(3):
            phase = (tick / 300.0 + i * 0.8) % (2 * math.pi)
            alpha = int(100 + 155 * (0.5 + 0.5 * math.sin(phase)))
            dc    = tuple(min(255, int(c * alpha / 255)) for c in color)
            pygame.draw.circle(self.screen, dc,
                               (cx - 20 + i * 20, dot_y), 5)

        ## Start screen
        #----------------

    
    def draw_start_screen(self) -> None:
        self.screen.fill(COLOR_BG)
        tick = pygame.time.get_ticks()
        self._draw_bg_stars(tick)

        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        t1 = self.font_large.render("UNIVERSE", True, COLOR_HUD_ACCENT)
        t2 = self.font_large.render("EXPLORATION", True, COLOR_HUD_ACCENT)
        self.screen.blit(t1, t1.get_rect(center=(cx, cy - 180)))
        self.screen.blit(t2, t2.get_rect(center=(cx, cy - 125)))
        
        panel_rect = pygame.Rect(cx - 320, cy - 60, 640, 190)
        bg_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        bg_surface.fill((5, 12, 30, 160)) 
        for i in range(0, panel_rect.height, 4):
            pygame.draw.line(bg_surface, (255, 255, 255, 15), (0, i), (panel_rect.width, i))
        self.screen.blit(bg_surface, panel_rect.topleft)
        self._draw_hud_brackets(panel_rect, COLOR_HUD_ACCENT, thickness=2)

        steps = [
            ("PHASE 1", "Watch the AI agent explore using A*"),
            ("PHASE 2", "Now your turn to explore"),
            ("GOAL", "Collect resources before fuel runs out!")
        ]
        
        y_offset = cy - 35
        for label, desc in steps:
            lbl_s = self.font_medium.render(label + ":", True, COLOR_HUD_ACCENT)
            self.screen.blit(lbl_s, (cx - 300, y_offset))
            desc_s = self.font_medium.render(desc, True, (255, 255, 255))
            self.screen.blit(desc_s, (cx - 150, y_offset))
            y_offset += 45

        pulse = 0.5 + 0.5 * math.sin(tick / 180.0)
        alpha = int(150 + 105 * pulse) 
        
        enter_text = "Press  ENTER  to launch"
        enter_surf = self.font_medium.render(enter_text, True, (255, 255, 255))
        enter_surf.set_alpha(alpha)
        
        shadow_surf = self.font_medium.render(enter_text, True, (10, 10, 20))
        rect = enter_surf.get_rect(center=(cx, cy + 190))
        
        self.screen.blit(shadow_surf, (rect.x + 2, rect.y + 2))
        self.screen.blit(enter_surf, rect)
        
        hint_surf = self.font_small.render("(Press  I  in-game for control reference)", True, (255, 255, 255))
        self.screen.blit(hint_surf, hint_surf.get_rect(center=(cx, cy + 240)))
    
    

    ## End screen
    #--------------

    def draw_end_screen(self, player, ai_agent) -> None:
        self.screen.fill(COLOR_BG)
        tick = pygame.time.get_ticks()
        self._draw_bg_stars(tick)

        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        cyan_accent = (0, 255, 215) ## COLOR_HUD_ACCENT

        title_surf = self.font_large.render("EXPLORATION COMPLETE", True, cyan_accent)
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, cy - 220)))
        pygame.draw.line(self.screen, cyan_accent, (cx - 350, cy - 185), (cx + 350, cy - 185), 2)

        p_w, p_h = 640, 220
        panel_rect = pygame.Rect(cx - p_w // 2, cy - 150, p_w, p_h)
        
        bg_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        bg_surface.fill((5, 12, 30, 160)) 
        for i in range(0, panel_rect.height, 4):
            pygame.draw.line(bg_surface, (255, 255, 255, 15), (0, i), (panel_rect.width, i))
        
        self.screen.blit(bg_surface, panel_rect.topleft)
        self._draw_hud_brackets(panel_rect, cyan_accent, thickness=2)

        p_hdr = self.font_medium.render("[ PLAYER ]", True, (0, 200, 255))
        a_hdr = self.font_medium.render("[ AI AGENT ]", True, (255, 80, 80))
        self.screen.blit(p_hdr, p_hdr.get_rect(centerx=cx - 160, y=panel_rect.top + 30))
        self.screen.blit(a_hdr, a_hdr.get_rect(centerx=cx + 160, y=panel_rect.top + 30))

        stats = [
            ("TOTAL SCORE", str(player.score), str(ai_agent.score), (255, 255, 255)),
            ("RESOURCES", str(player.resources_collected), str(ai_agent.resources_collected), cyan_accent),
        ]
        
        y_off = panel_rect.top + 85
        for label, p_val, a_val, val_col in stats:
            lbl_s = self.font_small.render(label, True, (150, 170, 200))
            self.screen.blit(lbl_s, lbl_s.get_rect(center=(cx, y_off + 10)))
            
            ps = self.font_medium.render(p_val, True, val_col)
            as_ = self.font_medium.render(a_val, True, val_col)
            self.screen.blit(ps, ps.get_rect(centerx=cx - 160, y=y_off))
            self.screen.blit(as_, as_.get_rect(centerx=cx + 160, y=y_off))
            y_off += 65

        if player.score > ai_agent.score:
            msg, col = "MISSION SUCCESS: PLAYER WINS", (0, 255, 150)
        elif ai_agent.score > player.score:
            msg, col = "MISSION FAILURE: AI DOMINANT", (255, 50, 50)
        else:
            msg, col = "SECTOR NEUTRALIZED: TIE", cyan_accent

        res_surf = self.font_medium.render(msg, True, col)
        self.screen.blit(res_surf, res_surf.get_rect(center=(cx, panel_rect.bottom + 60)))


        pulse = 0.5 + 0.5 * math.sin(tick / 400.0)
        alpha = int(150 + 105 * pulse)
        
        footer_text = "ENTER — RESTART GAME || ESC — QUIT"
        f_surf = self.font_small.render(footer_text, True, (255, 255, 255))
        f_surf.set_alpha(alpha)
        
        shadow = self.font_small.render(footer_text, True, (10, 10, 20))
        f_rect = f_surf.get_rect(center=(cx, panel_rect.bottom + 120))
        
        self.screen.blit(shadow, (f_rect.x + 2, f_rect.y + 2))
        self.screen.blit(f_surf, f_rect)


        ## Info overlay (press I)
        #-------------------------

    def draw_info_overlay(self) -> None:
        """
        When player presses I — shows resource key and controls.
        """
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2

        panel_w, panel_h = 720, 500
        panel = pygame.Rect(cx - panel_w//2, cy - panel_h//2, panel_w, panel_h)
        pygame.draw.rect(self.screen, (10, 14, 38), panel)
        cyan_accent = (0, 255, 215)
        pygame.draw.rect(self.screen, cyan_accent, panel, 2)

        # Title — font_hud (32px) not font_large (64px)
        title = self.font_hud.render("INFORMATION", True, cyan_accent)
        self.screen.blit(title, title.get_rect(center=(cx, panel.top + 32)))

        pygame.draw.line(self.screen, (40, 60, 90),
                         (panel.left + 30, panel.top + 62),
                         (panel.right - 30, panel.top + 62), 1)

        lx      = panel.left + 50
        rx      = panel.left + panel_w // 2 + 30
        y_start = panel.top + 80

        # ── Resource Key (left column) ──
        lbl = self.font_small.render("RESOURCE KEY", True, cyan_accent)
        self.screen.blit(lbl, (lx, y_start))

        resources = [
            (RESOURCE_COMMON,    "* Common",    RESOURCE_VALUES[RESOURCE_COMMON]),
            (RESOURCE_RARE,      "<> Rare",      RESOURCE_VALUES[RESOURCE_RARE]),
            (RESOURCE_EXOTIC,    "** Exotic",    RESOURCE_VALUES[RESOURCE_EXOTIC]),
            (RESOURCE_DISCOVERY, "!! Discovery", RESOURCE_VALUES[RESOURCE_DISCOVERY]),
        ]
        y = y_start + 32
        for rtype, name, val in resources:
            rc     = RESOURCE_COLORS[rtype]
            n_surf = self.font_small.render(name, True, rc)
            v_surf = self.font_small.render(f"+{val}", True, COLOR_WHITE)
            self.screen.blit(n_surf, (lx + 10, y))
            self.screen.blit(v_surf, (lx + 190, y))
            y += n_surf.get_height() + 14

        # ── Controls (right column) ──
        lbl2 = self.font_small.render("CONTROLS", True, cyan_accent)
        self.screen.blit(lbl2, (rx, y_start))

        controls = [
            ("Arrow Keys", "Move ship"),
            ("SPACE",      "Scan nearby area"),
            ("I",          "Toggle this info screen"),
            ("P",          "Pause / Resume game"),
            ("ESC",        "Quit game"),
            ("! on cell",  "Hazard — costs extra fuel"),
        ]
        y2 = y_start + 32
        for key, desc in controls:
            k_s = self.font_small.render(key, True, cyan_accent)
            d_s = self.font_small.render(desc, True, (200, 200, 200))
            self.screen.blit(k_s, (rx + 10, y2))
            y2 += k_s.get_height() + 2
            self.screen.blit(d_s, (rx + 10, y2))
            y2 += d_s.get_height() + 10

        # Close hint
        close = self.font_small.render("Press  I  or  ESC  to close",
                                        True, (120, 150, 180))
        self.screen.blit(close, close.get_rect(center=(cx, panel.bottom - 28)))

    ## Overlay

    def draw_pause_overlay(self) -> None:
        """Pause screen — semi-transparent overlay with PAUSED message."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2

        # Panel
        panel_w, panel_h = 460, 190
        panel = pygame.Rect(cx - panel_w//2, cy - panel_h//2, panel_w, panel_h)
        pygame.draw.rect(self.screen, (10, 14, 38), panel)
        pygame.draw.rect(self.screen, COLOR_HUD_ACCENT, panel, 2)

        # PAUSED title
        title = self.font_hud.render("GAME PAUSED", True, COLOR_HUD_ACCENT)
        self.screen.blit(title, title.get_rect(center=(cx, cy - 38)))

        # Divider
        pygame.draw.line(self.screen, _dim(COLOR_HUD_ACCENT, 0.4),
                         (cx - 160, cy - 10), (cx + 160, cy - 10), 1)

        # Hints
        h1 = self.font_small.render("P  —  Resume game", True, COLOR_DIMWHITE)
        h2 = self.font_small.render("I  —  View controls & resource info", True, COLOR_DIMWHITE)
        h3 = self.font_small.render("ESC  —  Quit game", True, COLOR_DIMWHITE)
        self.screen.blit(h1, h1.get_rect(center=(cx, cy + 12)))
        self.screen.blit(h2, h2.get_rect(center=(cx, cy + 38)))
        self.screen.blit(h3, h3.get_rect(center=(cx, cy + 64)))


    def draw_overlay(self, title: str, subtitle: str = "") -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))
        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2
        t  = self.font_large.render(title, True, COLOR_HUD_ACCENT)
        self.screen.blit(t, t.get_rect(center=(cx, cy - 20)))
        if subtitle:
            s = self.font_medium.render(subtitle, True, COLOR_HUD_TEXT)
            self.screen.blit(s, s.get_rect(center=(cx, cy + 20)))