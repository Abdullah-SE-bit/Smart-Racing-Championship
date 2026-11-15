# Repository instructions

Current scope: repository infrastructure and development process only. No
playable application exists. Feature development needs explicit user instructions.

1. Read the relevant project documentation before modifying code, including
   `README.md`, `PROJECT_STRUCTURE.md`, and applicable documents under `docs/`.
2. Follow the assignment requirements. Read `Project.pdf` completely if it is
   available. It was absent during scaffolding and has not been verified; resolve
   missing specifications before implementing affected requirements.
3. Keep algorithms independent from Pygame rendering.
4. Implement mandatory algorithms manually instead of delegating them to
   external algorithm libraries.
5. Keep the racing engine separate from presentation logic.
6. Use deterministic behavior for computer opponents and race events, including
   explicit seeds, stable tie-breaking, and controlled simulation timing.
7. Prefer readable, understandable Python over clever or unnecessarily complex
   abstractions.
8. Use meaningful names and simple, maintainable designs.
9. Add meaningful tests when functionality is implemented in later phases.
10. Do not silently change game rules or algorithm requirements.
11. Do not introduce unnecessary dependencies.
12. Do not begin future implementation phases without explicit user instructions.
13. Do not modify unrelated modules; inspect existing files before changing them.
14. Document important architectural decisions under `docs/architecture/`.
15. Preserve compatibility with Windows and Python 3.12+.
16. Do not claim tests passed unless they were actually executed. An empty test
    collection is not a passing test suite.
17. Keep generated code understandable for students explaining it during a viva.

The Algorithm Lab and experiments must use the exact implementations used by
gameplay. Keep submitted assets, assignment documentation, datasets, and
experimental results trackable in Git. Do not create fake results or placeholder
tests. Application package files remain empty initializers until implementation
is authorized. Infrastructure validation scripts and meaningful infrastructure
tests are allowed in this task; do not add game entry points or gameplay logic.

## Development and agent coordination

- Read [WORKFLOW.md](docs/development/WORKFLOW.md), the relevant contracts,
  ownership proposal, and your member handoff before work. Inspect existing
  implementations before editing; do not rewrite working code unnecessarily.
- Follow issue-based development on a focused branch from `game`, or from an
  explicitly documented parent feature branch. Work only on assigned scope.
- Respect module boundaries and documented rules. Stop affected work and report
  unresolved architectural conflicts; continue unrelated authorized work.
- Keep readable Python, custom mandatory algorithms, deterministic simulation,
  shared gameplay/Lab implementations, and separation of engine and rendering.
- Add relevant tests with implementation. Activate applicable gates in
  `docs/development/validation.json` when declaring a capability implemented;
  update specific test paths as capabilities become available, not only at release.
- Update relevant documentation and your own handoff after meaningful work and
  before preparing a PR. Do not overwrite another member's handoff.
- PRs into `main` require one eligible non-author teammate approval. PRs into
  `game` do **not** require review; optional teammate feedback is welcome.
  Never self-approve or count author feedback as approval for `main`.
- Do not merge PRs without explicit user authorization. For `main`, also obtain
  the required teammate approval. Do not bypass CI or protections. Do not
  force-push shared branches or rewrite existing history in this task.
- Do not silently introduce dependencies or fabricate test/CI/assignment results.
- Never automatically begin another phase. See the current remote enforcement
  limits in [GOVERNANCE_STATUS.md](docs/development/GOVERNANCE_STATUS.md).

Do not create commits or push changes without explicit user permission.
