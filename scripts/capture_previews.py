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
        for algorithm, step in (("Event heap", 9), ("Merge sort", 9), ("Knapsack", 1), ("Top-k", 4)):
            app.lab_algorithm = algorithm
            app.lab_step = step
            capture(f"06-{algorithm.lower().replace(' ', '-')}", app.draw_lab)
        app.time = 2
        app.generate()
        capture("07-generation", app.draw_generation)
        app.reduced_motion = False
        app.prepare_championship()
        app.time += 1
        capture("07b-title-fight-opener", app.draw_planner)
        app.start_planned_race()
        app.reduced_motion = True
        race = app.race
        human = race.racers[0]
        route = shortest_path(race.circuit.graph, human.vertex, race._destination(human))
        if len(route.vertices) > 1:
            race.choose(human.id, route.vertices[1])
        race.tick(.3)
        for tick in range(2400):
            if race.over:
                break
            if human.edge_id is None and not human.finished and not human.dnf:
                future = set(race.circuit.checkpoints[human.next_checkpoint + 1:])
                route = shortest_path(race.circuit.graph, human.vertex, race._destination(human),
                                      avoid_vertices=future)
                if len(route.vertices) > 1:
                    race.choose(human.id, route.vertices[1])
            race.tick(.1)
            if tick == 71:
                capture("08-racing", app.draw_race)
                app.toggle_race_camera()
                capture("08-tactical", app.draw_race)
                app.toggle_race_camera()
        if not race.over:
            raise RuntimeError("Preview race did not finish within the time limit")
        app.reduced_motion = False
        app.finish_race()
        app.time += 3
        capture("08b-title-fight-standings", app.draw_dashboard)
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        app.reduced_motion = True
        capture("09-results", app.draw_dashboard)
        app.go("standings")
        capture("10-standings", app.draw_standings)
        print(f"Wrote interface previews to {OUTPUT.resolve()}")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
