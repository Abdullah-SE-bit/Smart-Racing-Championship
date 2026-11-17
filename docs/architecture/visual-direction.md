# Visual and motion direction

The screens use a motorsport broadcast palette inspired by Drive to Survive:
carbon black and graphite surfaces, cool white type and racing red primary
actions. The menu's featured circuit is drawn from the selected track's
stored main route and roads; the moving markers are decorative and never feed
the race engine. Original generated pit-lane artwork sits behind the menu and
appears more subtly behind other screens. Buttons use clipped corners and a
moving highlight; the backdrop pans slowly. Reduced motion holds the backdrop
and buttons still along with the circuit markers. Settings groups
keyboard inputs and race options into separate panels. The planner keeps its
map selection unobstructed by placing its resource and alternative-route
actions below the map. The race view uses wider road geometry and top-down car
markers derived from the engine's interpolated racer positions. Rendering does
not advance the simulation. Nitro and checkpoint indicators reflect the current
racer state, and the live order highlights the player. The Lab exposes the actual current trace record
and playback progress without overlaying the circuit. Results and championship
standings use the race's real classifications and points. The refuelling view
includes the selected route alongside the calculated stops.

At startup, a four-second title reveal and starting-light sequence leads to the
main menu. Enter, Space, Escape or a left click skips it; resize and quit remain
available during the sequence. The intro uses presentation time and does not
advance the race engine. If reduced motion is already enabled at startup, it is
skipped. The current settings are in-memory and reset when the app closes.

The circuit uses muted road colors, blue for the recommended line, red for the
selected road, and amber for hazards. Racer colors remain distinct
from one another. Flat surfaces and thin outlines keep the track legible.

Large, short headings establish hierarchy. Compact labels and tabular race data
should remain secondary but legible against their background. The map uses
actual graph geometry, checkpoint numbers, F/N service markers, obstacle
diamonds and road status marks. A selected road and the recommended route use
separate colors and are also described in text.

Motion carries information: cars interpolate along the engine's current edge,
Lab steps show real algorithm traces, and the selected road pulses. A short
screen transition helps orient navigation. The settings screen offers reduced
motion, which removes the transition, moving background and pulse while keeping
the simulation and car positions visible. Animation never decides race state or
changes simulation timing. Continue checking controls and readability through
both screenshots and a real playthrough.
