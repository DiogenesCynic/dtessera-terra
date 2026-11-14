"""
visual_backdrop.py
------------------
Renders full-window (800x600) background image plates for Region and Weather,
layered with continuous Solar Brightness BEFORE any UI panels are drawn.
"""

import os
import math
import pygame
import weather_engine as we

_IMAGE_CACHE = {}

# Mappings to match your map_data.py regions to your filenames
REGION_IMAGE_MAP = {
    "murum town": "bg_murum_town.png",
    "parvus town": "bg_parvus_town.png",
    "fluvius town": "bg_fluvius_town.png",
    "the forest": "bg_lignum_forest.png",
    "the caligo mountains": "bg_caligo_mountains.png",
    "the river fluvius": "bg_river_fluvius.png",
    "farm": "bg_farmlands.png",
    "the heath": "bg_heath.png",
    "road": "bg_road.png",
    "path": "bg_road.png",
    "lake": "bg_lake.png",
    "castle": "bg_castle.png",
}

WEATHER_IMAGE_MAP = {
    "RAIN": "weather_rain.png",
    "STORM": "weather_rain.png",
    "SNOW": "weather_snow.png",
    "HAIL": "weather_hail.png",
    "FOG": "weather_fog.png",
    "SUN": "weather_sunbeams.png",
}


def _load_and_scale_image(filepath, has_alpha=False):
    """Loads an image and scales it to 800x600. Returns a fallback surface if missing."""
    if filepath in _IMAGE_CACHE:
        return _IMAGE_CACHE[filepath]
    
    if os.path.exists(filepath):
        img = pygame.image.load(filepath)
        img = pygame.transform.scale(img, (800, 600))
        img = img.convert_alpha() if has_alpha else img.convert()
        _IMAGE_CACHE[filepath] = img
        return img
    else:
        # Fallback if the artist hasn't created the file yet
        surf = pygame.Surface((800, 600), pygame.SRCALPHA if has_alpha else 0)
        if not has_alpha:
            surf.fill((45, 42, 38)) # Dark Tate-grey fallback
        _IMAGE_CACHE[filepath] = surf
        return surf


def get_base_plate(region_name):
    """Determines the correct background image for the player's current region."""
    region_lower = region_name.lower()
    filename = "bg_default.png"
    
    for key, f_name in REGION_IMAGE_MAP.items():
        if key in region_lower:
            filename = f_name
            break
            
    filepath = os.path.join("assets", "backgrounds", filename)
    return _load_and_scale_image(filepath, has_alpha=False)


def get_weather_plate(w_key):
    """Loads the transparent weather overlay and sets opacity based on intensity."""
    w_spec = we.WEATHER_TYPES.get(w_key, we.WEATHER_TYPES["overcast"])
    cat = w_spec["category"]
    intensity = w_spec.get("intensity", 1)
    
    if cat not in WEATHER_IMAGE_MAP:
        return None
        
    filename = WEATHER_IMAGE_MAP[cat]
    filepath = os.path.join("assets", "weather", filename)
    surf = _load_and_scale_image(filepath, has_alpha=True)
    
    # Adjust transparency based on weather intensity (1 to 4)
    # Intensity 1 = 25% opaque, Intensity 4 = 100% opaque
    alpha_val = min(255, int((intensity / 4.0) * 255))
    
    # Create a copy so we don't modify the cached original's alpha globally
    overlay = surf.copy()
    overlay.set_alpha(alpha_val)
    return overlay


def get_continuous_sun_tint(player):
    """Calculates continuous daylight ebb and flow based on the Decimal Clock."""
    we.ensure_weather_initialized(player)
    m_idx, _, dec_hr = we.get_calendar_metrics(player.get("total_game_minutes", 0))
    _, dawn_hr, dusk_hr, _ = we.MONTH_PROFILES[m_idx]

    w_key = player.get("weather_current", "overcast")
    w_spec = we.WEATHER_TYPES.get(w_key, we.WEATHER_TYPES["overcast"])
    vis = w_spec.get("visibility", 1.0)

    midday = (dawn_hr + dusk_hr) / 2.0
    half_day = max(0.5, (dusk_hr - dawn_hr) / 2.0)

    if dawn_hr <= dec_hr <= dusk_hr:
        norm = (dec_hr - midday) / half_day
        sun_strength = math.cos(norm * (math.pi / 2.0))
        effective_bright = sun_strength * (0.60 + 0.40 * vis)

        horizon_factor = max(0.0, 1.0 - (sun_strength * 2.2))
        r = int(30 * (1.0 - horizon_factor) + 145 * horizon_factor)
        g = int(35 * (1.0 - horizon_factor) + 65 * horizon_factor)
        b = int(50 * (1.0 - horizon_factor) + 38 * horizon_factor)
        alpha = int((1.0 - effective_bright) * 105)
        return (r, g, b, max(0, min(135, alpha)))

    twilight_span = 0.65
    if (dawn_hr - twilight_span) <= dec_hr < dawn_hr:
        t = (dawn_hr - dec_hr) / twilight_span
    elif dusk_hr < dec_hr <= (dusk_hr + twilight_span):
        t = (dec_hr - dusk_hr) / twilight_span
    else:
        t = 1.0 

    r = int(85 * (1.0 - t) + 12 * t)
    g = int(42 * (1.0 - t) + 16 * t)
    b = int(48 * (1.0 - t) + 28 * t)
    alpha = int(105 * (1.0 - t) + 195 * t)
    return (r, g, b, alpha)


def draw_world_backdrop(screen, player, world_map=None):
    """
    Renders the full-window custom image backdrop, weather overlay,
    and continuous solar brightness BEFORE any UI elements.
    """
    # 1. Determine region
    region_name = "Wilderness"
    if player.get("current_building"):
        region_name = "Murum Town" # Default interior fallback region style
    elif world_map:
        pos = (player.get("x"), player.get("y"))
        if pos in world_map:
            region_name = world_map[pos].region

    # 2. Draw Base Image
    base_surf = get_base_plate(region_name)
    screen.blit(base_surf, (0, 0))

    # 3. Draw Weather Overlay
    we.ensure_weather_initialized(player)
    w_key = player.get("weather_current", "overcast")
    weather_surf = get_weather_plate(w_key)
    if weather_surf:
        screen.blit(weather_surf, (0, 0))

    # 4. Draw Continuous Solar Brightness & Torchlight
    r, g, b, alpha = get_continuous_sun_tint(player)
    if alpha > 0:
        shade = pygame.Surface((800, 600), pygame.SRCALPHA)
        light_info = we.get_daylight_state(player)
        
        if light_info["has_light"] and alpha >= 90:
            is_lantern = "Storm Lantern" in light_info["light_source"]
            reduced_alpha = max(35, alpha - (95 if is_lantern else 65))
            shade.fill((r, g, b, reduced_alpha))
            pygame.draw.circle(shade, (220, 145, 55, 38), (400, 300), 360)
        else:
            shade.fill((r, g, b, alpha))
            
        screen.blit(shade, (0, 0))
