"""Render reproducible, headless previews of the application screens."""

import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from smart_racing.algorithms.routing.shortest import shortest_path
from smart_racing.ui.app import App


OUTPUT = Path("output/previews")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    app = App()

    def capture(name, draw):
        app.buttons = []
        app.background()
        draw()
        pygame.image.save(app.surface, str(OUTPUT / f"{name}.png"))

    try:
        app.start_intro()
        for name, moment in (("00a-intro-reveal", .7), ("00b-intro-lights", 1.6),
                             ("00c-intro-finale", 3.5)):
            app.intro_elapsed = moment
            capture(name, app.draw_intro)
        app.intro_elapsed = 2.5
        capture("00-startup-intro", app.draw_intro)
        app.intro_active = False
        app.reduced_motion = True
        capture("01-menu", app.draw_menu)
        app.go("settings")
        capture("02-settings", app.draw_settings)
        app.open_quick_planner()
        capture("03-planner", app.draw_planner)
        app.open_refuel_plan()
        capture("03b-refuel-plan", app.draw_refuel_plan)
        app.open_alternatives()
        capture("04-alternatives", app.draw_alternatives)
        app.go("compare")
        capture("05-comparison", app.draw_comparison)
        app.go("lab")
        app.lab_step = 4
        capture("06-algorithm-lab", app.draw_lab)
        app.time = 2
        app.generate()
        capture("07-generation", app.draw_generation)
        app.prepare_championship()
        app.start_planned_race()
        race = app.race
        human = race.racers[0]
        route = shortest_path(race.circuit.graph, human.vertex, race._destination(human))
        if len(route.vertices) > 1:
            race.choose(human.id, route.vertices[1])
        race.tick(.3)
        capture("08-racing", app.draw_race)

        for _ in range(2400):
            if race.over:
                break
            if human.edge_id is None and not human.finished and not human.dnf:
                future = set(race.circuit.checkpoints[human.next_checkpoint + 1:])
                route = shortest_path(race.circuit.graph, human.vertex, race._destination(human),
                                      avoid_vertices=future)
                if len(route.vertices) > 1:
                    race.choose(human.id, route.vertices[1])
            race.tick(.1)
        if not race.over:
            raise RuntimeError("Preview race did not finish within the time limit")
        app.finish_race()
        capture("09-results", app.draw_dashboard)
        app.go("standings")
        capture("10-standings", app.draw_standings)
        print(f"Wrote interface previews to {OUTPUT.resolve()}")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
