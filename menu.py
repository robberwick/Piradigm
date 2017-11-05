import logging
import os
import sys
import time

import pygame
from pygame.locals import *

from buttons import TextButton
import colours

# Global variables

# screen size
SCREEN_SIZE = width, height = 240, 320

logging.basicConfig(
    filename='piradigm.log',
    level=logging.DEBUG,
    format='%(asctime)s %(message)s'
)


def setup_environment():
    """Set up all the required environment variables"""
    env_vars = [
        ("SDL_FBDEV", "/dev/fb1"),
        ("SDL_MOUSEDEV", "/dev/input/touchscreen"),
        ("SDL_MOUSEDRV", "TSLIB"),
    ]
    for var_name, val in env_vars:
        os.environ[var_name] = val


def setup_menu(surface, background_colour=colours.BLUE):
    """Set up the menu on the specified surface"""
    # flood fill the surface with the background colour
    surface.fill(background_colour)

    # set up the fixed items on the menu
    # Add buttons and labels
    menu_config = [
        ("Speed", (20, 10)),
        ("Maze", (125, 10)),
        ("Rainbow", (20, 80)),
        ("Golf", (125, 80)),
        ("Pi Noon", (20, 150)),
        ("Obstacle", (125, 150)),
        ("Shooting", (20, 220)),
        ("RC", (125, 220)),
        ("Exit", (20, 290)),
    ]

    # perform list comprehension on menu_config, wherein we call
    # make_button with the index, and individual item arguments
    # note *item performs unpacking of the tuple and provides them
    # as individual arguments to make_button
    return [
        TextButton(surface=surface, index=index, label=item[0], coords=item[1])
        for index, item
        in enumerate(menu_config)
    ]


def get_button_at_position(pos):
    """Returns the TextButton object at the specified position.
    Returns None if No corresponding button"""
    # Iterate through our list of buttons and get the first one
    # whose rect returns True for pygame.Rect.collidepoint()
    try:
        button = next(obj for obj in menu_buttons if obj.rect.collidepoint(pos))
    except StopIteration:
        button = None
    return button


def on_click(mousepos):
    """Click handling function to check mouse location"""
    logging.debug("on_click: %s", mousepos)
    button = get_button_at_position(mousepos)

    if button:
        logging.info(
            "%s clicked - launching %d",
            button.label, button.index
        )
        # Call button_handler with the matched button's index value
        button_handler(button.index)
    else:
        logging.debug(
            "Click at pos %s did not interact with any button",
            mousepos
        )


def on_mouse_move(mousepos):
    """Mouse move handler to check mouse location"""
    logging.debug("on_mouse_move: %s", mousepos)
    active_button = get_button_at_position(mousepos)

    for button in menu_buttons:
        button.hover(is_hovering=button == active_button)


def button_handler(number):
    """Button action handler. Currently differentiates between
    exit and other buttons only"""
    logging.debug("button %d pressed", number)
    if number == 0:    # specific script when exiting
        time.sleep(1)

    if number == 8:
        time.sleep(1)  # do something interesting here
        logging.info("Exit button pressed. Exiting now.")
        sys.exit()


setup_environment()

logging.info("Initialising pygame")
pygame.init()

logging.info("Hiding Cursor")
pygame.mouse.set_visible(False)

logging.info("Setting screen size to %s", SCREEN_SIZE)
screen = pygame.display.set_mode(SCREEN_SIZE)
menu_buttons = setup_menu(screen)

# While loop to manage touch screen inputs
while True:
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            logging.debug("screen pressed: %s", event.pos)

            # for debugging purposes - adds a small dot
            # where the screen is pressed
            # pygame.draw.circle(screen, WHITE, pos, 2, 0)
            on_click(event.pos)

        if event.type == pygame.MOUSEMOTION:
            logging.debug("Mouse over: %s", get_button_at_position(event.pos))
            on_mouse_move(event.pos)

        # ensure there is always a safe way to end the program
        # if the touch screen fails
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                sys.exit()

    pygame.display.update()
