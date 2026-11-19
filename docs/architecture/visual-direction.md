# REDLINE visual and motion direction

REDLINE should read as a focused motorsport broadcast: fast, precise, and
legible. Use real track state, timing, and race consequences as the visual
material. Avoid decorative dashboards, fake data, generic neon overload, and
motion that competes with driving.

## Visual system

| Role | Current color | Use |
|---|---|---|
| Asphalt / page background | `#0C0E13` | Main canvas and quiet negative space. |
| Carbon panel | `#171A21` | Information cards and control surfaces. |
| Raised panel | `#282C35` | Secondary controls and selected neutral states. |
| Pit red | `#C5232B` | Primary action, REDLINE marks, and decisive race feedback. |
| Signal coral | `#FF6664` | Selection, urgency, and high-priority highlights. |
| Ice blue | `#73C4EF` | Planned route, checkpoint progress, and information. |
| Warm hazard | `#FFB471` | Oil, warnings, and track hazards. |
| Race white | `#F4F5F8` | Main type, critical values, and readable contrast. |
| Steel grey | `#B7BEC9` | Supporting labels and secondary information. |

Use color together with shape, label, or position so race state does not depend
on color alone. Reserve the brightest red for actionable emphasis; keep long
labels and tables calm. Use the bundled Barlow family: Condensed Bold Italic
for display moments, Condensed SemiBold for compact controls, and Barlow Regular
for body text.

## Screens and image treatment

- **Main menu:** keep `pit-lane-night.png` as the still hero-car background.
  Preserve dark space behind menu text. The selected circuit preview uses its
  matching venue artwork and live circuit geometry.
- **Planner:** use the selected circuit's venue backdrop, with a dark overlay
  that keeps the graph and route panel readable. Mark start, destination,
  checkpoints, hazards, and the selected route distinctly.
- **Race:** use a projected elevated broadcast view by default; let the player
  switch to the flat tactical graph without changing engine state. Render cars
  at their live road progress and show events, resources, and checkpoints from
  the same race state.
- **Algorithm Lab:** make the active operation visible on the actual graph,
  heap, ranking, or resource table. Counters and traces must come from the
  shared algorithm result, not illustrative sample data.
- **Championship:** use the track's venue image for race introductions and a
  restrained broadcast treatment for results, points movement, and the finale.

Venue backdrops may ease into view on non-menu screens. The menu hero image
itself stays still while idle; do not add a continuous menu pan or drift.
Generated scenery, geometry, and camera projection are presentation assets and
must not alter graph coordinates or simulation decisions.

## Motion language

| Moment | Direction | Timing rule |
|---|---|---|
| Startup intro | Starting lights, controlled reveal, then menu | Four seconds maximum; mouse, Enter, Space, or Escape skips it. |
| Screen change | Short composited transition with a clean settle | Keep the destination screen immediately understandable. |
| Buttons | Brief highlight or pressed response | Only while hovered, focused, or activated; never continuous idle pulsing. |
| Planner route | Reveal edges in route order, then settle on the final path | Reveal the computed route; do not imply progress through the simulation. |
| Quick Race grid | Countdown / lights out | Freeze simulation until release; skip input must not activate a race action. |
| Race camera | Smooth visual follow of live positions | Interpolation is presentation-only; fixed-step simulation remains authoritative. |
| Algorithm Lab | Interpolate between recorded trace states | Playback controls choose trace progress; drawing must not run extra algorithm steps. |
| Championship results | Count points and reorder drivers to match the result | End on the exact standings order; allow a skip. |

Use purposeful ease-in/out and short holds to make hierarchy clear. Keep motion
brief, predictable, and interruptible. Avoid shake, spin, parallax, or pulsing
as an idle effect. A visual transition may not change race time, route costs,
resource consumption, event order, algorithm counters, or standings.

## Accessibility and input

- The saved **Reduced Motion** setting removes timed presentation movement and
  reaches the useful screen state immediately. Do not hide information behind
  animation.
- Support mouse use and keyboard focus. Visible focus, hover, disabled, and
  selected states should be distinct.
- Keep text/background contrast strong, labels concise, and values tied to
  understandable units. Pair icons with text where their meaning is not obvious.
- On resize, preserve the logical layout and map input to the same controls.
- Play a distinct sound cue only when it communicates a real focus, action,
  countdown, resource, warning, or finish event. Respect the saved sound level.

## Implementation boundaries

- `ui/app.py` translates input and renders presentation.
- `ui/components/` contains reusable broadcast, menu, grid, title, and telemetry
  treatments.
- `ui/visualization/` renders the race scene and actual algorithm traces.
- `game/`, `algorithms/`, `tracks/`, and `championship/` own outcomes and data;
  they must not import Pygame.
- Use the app's presentation clock for visual interpolation. The fixed-step
  simulation clock controls race outcomes.
- Prefer existing bundled image, sound, and font assets; record provenance for
  any new asset in the matching `assets/*/README.md` file.

The current application includes a static menu hero, skip-capable race intro,
grid countdown, animated route reveal, two race cameras, trace-driven Lab
motion, and championship results presentations. See
[`docs/testing/assignment-requirements-audit.md`](../testing/assignment-requirements-audit.md)
for current test and release evidence.

## References

- [Pygame Surface documentation](https://www.pygame.org/docs/ref/surface.html)
- [W3C guidance on animation from interactions](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html)
- [Conventional binary heap representation](https://visualgo.net/en/heap)
