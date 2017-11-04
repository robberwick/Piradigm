import logging
import pygame

import colours


class TextButton:
    """Returns an object representing a TextButton"""
    def __init__(
        self,
        index=None,
        coords=None,
        surface=None,
        fill_colour=colours.BLUE,
        fill_colour_hover=colours.YELLOW,
        fill_colour_active=colours.WHITE,
        border_colour=colours.CREAM,
        label="",
        label_colour=colours.WHITE,
        label_colour_hover=colours.BLUE,
        label_colour_active=colours.BLUE,
    ):
        self.index = index
        self.coords = coords
        self.target_surface = surface
        self.fill_colour = fill_colour
        self.fill_colour_active = fill_colour_active
        self.fill_colour_hover = fill_colour_hover
        self.border_colour = border_colour
        self.label = label
        self.label_colour = label_colour
        self.label_colour_hover = label_colour_hover
        self.label_colour_active = label_colour_active
        self.is_active = False
        self.is_hovering = False

        logging.debug(
            "Making button with text '%s' at (%s)",
            self.label,
            self.coords
        )

        self.button_surface = pygame.Surface((100, 65))

        self.font = pygame.font.Font(None, 24)

        self.draw()

    def draw(self):
        label_surface = self.draw_label()
        self.draw_button_background()
        self.button_surface.blit(label_surface, (5, 5))
        self.rect = self.target_surface.blit(self.button_surface, self.coords)

    def draw_button_background(self):
        if self.is_active:
            colour = self.fill_colour_active
        elif self.is_hovering:
            colour = self.fill_colour_hover
        else:
            colour = self.fill_colour
        self.button_surface.fill(colour)
        rect = pygame.draw.rect(
            self.button_surface,
            self.border_colour,
            (0, 0, 100, 65),
            1
        )
        return rect

    def draw_label(self):
        if self.is_active:
            colour = self.label_colour_active
        elif self.is_hovering:
            colour = self.label_colour_hover
        else:
            colour = self.label_colour
        return self.font.render(
            str(self.label), 1, (colour)
        )

    def hover(self, is_hovering=False):
        self.is_hovering = is_hovering
        self.draw()

    def click(self):
        """redraw with active colours and kick off a custom event to
        reset the button"""
        self.is_active = True
        self.draw()
