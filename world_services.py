# =========================================================================
# REGIONAL SHOPS & PRIVATE CASTELLAN VAULTS (PHASE 3)
# =========================================================================
REGIONAL_SHOPS = {
    # Fluvius Blacksmith & General Store
    (11, 4): {
        "name": "Aldred's Fluvius Ironworks & Provisions",
        "inventory": ["iron dagger", "iron sword", "crossbow", "gambeson", "helmet", "crowbar", "rope", "torch", "waxed jacket", "iron screw-spindle"],
    },
    (18, 22): {
        "name": "Parvus Guild Foundry & Ship-Chandler",
        "inventory": ["steel longsword", "macuahuitl", "greek fire flask", "storm lantern", "ice crampons", "warm winter coat", "heavy winter blanket", "oak press-frame"],
    },
    # Castle Ragmore Private Armoury (Accessible if Allied/Staff)
    (4, 22): {
        "name": "Castle Ragmore Private Armoury & Forge",
        "inventory": ["steel longsword", "crossbow", "gambeson", "helmet", "horse armour", "dragon shaffron", "star-iron ingot"],
    },
}


def check_regional_shop_entry(player, world_map):
    """
    Called when interacting at shop coordinates in Fluvius, Parvus, or Ragmore.
    Opens the regional shop pop-out.
    """
    pos = (player["x"], player["y"])
    if pos not in REGIONAL_SHOPS:
        return False, None, "MAIN"

    shop = REGIONAL_SHOPS[pos]
    # Check access for castle armouries
    if pos == (4, 22) and player.get("chapter_2_route") != "Join Castellan's House Staff" and player.get("faction_guard", 0) < 5:
        return True, "Castle Ragmore guards cross their halberds: 'Private keep stores—authorized personnel only!'", "MAIN"

    player["active_shop"] = shop
    return True, f"You step into **{shop['name']}**. Browse their wares:", "MINIGAME_SHOP"


def draw_shop_ui(screen, player, font, font_bold, mouse_pos):
    """Renders the regional shop pop-out window."""
    overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    TATE_RED = (168, 50, 35)
    DIAL_CREAM = (244, 239, 225)
    CLOCK_BLACK = (28, 28, 28)

    panel = pygame.Rect(80, 50, 640, 440)
    pygame.draw.rect(screen, DIAL_CREAM, panel, border_radius=12)
    pygame.draw.rect(screen, TATE_RED, panel, width=4, border_radius=12)
    pygame.draw.rect(screen, CLOCK_BLACK, panel, width=1, border_radius=12)

    shop = player.get("active_shop", {})
    title = font_bold.render(shop.get("name", "REGIONAL SHOP").upper(), True, TATE_RED)
    screen.blit(title, (400 - title.get_width() // 2, 62))

    inv = shop.get("inventory", [])
    from crafting_engine import EXOTIC_GEAR_DATABASE
    from game_data import item_database

    y_cursor = 105
    for item_name in inv[:6]:
        data = EXOTIC_GEAR_DATABASE.get(item_name) or item_database.get(item_name, {"price": 10, "description": "Standard item."})
        price = data.get("price", 10)
        desc = data.get("description", "")

        r_rect = pygame.Rect(100, y_cursor, 600, 45)
        pygame.draw.rect(screen, (252, 248, 238), r_rect, border_radius=6)
        pygame.draw.rect(screen, TATE_RED, r_rect, width=1, border_radius=6)

        screen.blit(font_bold.render(f"{item_name.title()} — {price} Silver", True, CLOCK_BLACK), (115, y_cursor + 6))
        screen.blit(font.render(desc[:72], True, (90, 85, 80)), (115, y_cursor + 24))

        y_cursor += 52
