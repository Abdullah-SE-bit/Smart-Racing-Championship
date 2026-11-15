# Viva preparation guide

No application algorithm or subsystem is implemented yet. Fill this guide with
links to actual code and tested examples as each issue completes; do not invent
explanations for nonexistent implementations.

For each implemented algorithm or subsystem, record:

1. Requirement reference, why it exists, and where gameplay uses it.
2. Code location, caller and relationship to the shared Algorithm Lab implementation.
3. Inputs, outputs, units, failure states and correctness assumptions.
4. A small worked example traced through the actual implementation.
5. Data structures and the invariants they maintain.
6. Time/space complexity, what input size means, and implementation-specific costs.
7. Empty, singleton, disconnected, duplicate, invalid and resource-limit cases as relevant.
8. Deterministic tie rules, seeds, clock behavior and repeated-run evidence.
9. Important decisions, alternatives, limitations and integration contracts.
10. Tests and experiment evidence, including what they do not establish.

Each owner should explain the implementation to another member, who traces an
edge case without relying on the owner. Keep notes understandable and consistent
with the code. Do not memorize claims that have not been verified.
