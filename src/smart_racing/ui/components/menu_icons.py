"""Small motorsport pictograms for the five main menu controls."""

import pygame


def draw_mode_icon(surface, title, center, color):
    x, y = center

    def stroke(points):
        pygame.draw.lines(surface, color, False, [(x + a, y + b) for a, b in points], 2)

    if title == "CHAMPIONSHIP":
        stroke([(-6, -8), (6, -8), (5, 0), (2, 4), (-2, 4), (-5, 0), (-6, -8)])
        stroke([(-6, -6), (-10, -6), (-9, -2), (-5, 0)])
        stroke([(6, -6), (10, -6), (9, -2), (5, 0)])
        stroke([(0, 4), (0, 9)])
        stroke([(-5, 9), (5, 9)])
    elif title == "QUICK RACE":
        for dx in (-6, 1):
            stroke([(dx - 3, -7), (dx + 4, 0), (dx - 3, 7)])
    elif title == "ROUTE PLANNER":
        stroke([(-8, 6), (-4, -5), (4, 5), (8, -6)])
        for a, b in ((-8, 6), (8, -6)):
            pygame.draw.circle(surface, color, (x + a, y + b), 3)
    elif title == "ALGORITHM LAB":
        stroke([(-8, 7), (0, -6), (8, 7)])
        for a, b in ((-8, 7), (8, 7), (0, -6)):
            pygame.draw.rect(surface, color, (x + a - 2, y + b - 2, 5, 5))
    elif title == "CONTROLS & SETTINGS":
        for dy, knob in ((-6, -3), (0, 5), (6, -1)):
            stroke([(-9, dy), (9, dy)])
            pygame.draw.rect(surface, color, (x + knob - 1, y + dy - 2, 3, 5))
