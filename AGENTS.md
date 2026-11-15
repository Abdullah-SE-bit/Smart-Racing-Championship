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
- Follow issue-based planned development on a focused branch from `game`, or from an
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

## Mandatory startup and phase policy

Every agent must read this file, the complete `implementation_plan.md`,
`mandoff.md`, its named personal handoff, relevant upstream contracts and active
GitHub issues/PRs. Fetch latest remote game/main; check current human
authorization, preceding gate acceptance and whether its task is already
claimed. Use an independent worktree/branch. If a prerequisite is unsatisfied,
stop application implementation and report the blocker; safe authorized
coordination/maintenance may continue.

The plan is the authoritative task source; Project.pdf is the coursework source
and is currently absent. Do not claim its historical review was performed here.
Preserve exact task IDs and A=Abdullah, B=Taha, C=Shaheer, including joint owners.
User-confirmed 04-P05 remains optional and does not block P04 acceptance.

All phases are strictly sequential: previous gate must be evidence-accepted,
not merely closed. New human authorization is required after each accepted
phase. Planning future issues does not authorize claiming, implementing or
merging future features. READY_FOR_PROMOTION is distinct from ACCEPTED: do not
require the current gate closed before its own final main promotion.

## Mandatory concurrency and handoff publication

- Abdullah, Taha and Shaheer all coordinate handoffs, per user direction. Only
  one acting writer at a time modifies central `mandoff.md`; record writer and
  explicit handover. Others update only their own named handoff. Never rewrite
  the central file concurrently. Preserve legacy handoff records.
- Before any phase code, the acting coordinator fetches game/main, verifies the
  previous gate accepted, checks issues/PRs/claims, allocates current tasks,
  records critical/parallel work, shared interfaces, branch ownership and merge
  order, updates mandoff/personal allocations, creates a docs-only kickoff
  branch, commits/pushes, opens its game PR, gets CI and teammate approval,
  merges only when authorized and verifies handoffs are visible on remote game.
  No application code before that kickoff is published.
- After kickoff each agent fetches game, verifies its issue is available and
  the previous gate accepted, creates its own branch/worktree, updates only its
  personal handoff with task claim/branch/dependencies/planned work, commits the
  handoff separately, pushes and verifies success BEFORE writing source code.
  If push fails, stop implementation and resolve it; local edits are not synchronization.
- Use separate Git worktrees or clones for each agent. Never let two agents
  manipulate the same active tree or overwrite another developer's dirty work.
  Inspect active interface PRs and owners before changing shared contracts.
- Before a claim check assignee, comments/status, open PRs, central allocation
  and personal handoffs. An existing owner requires coordination, not duplicate
  work. Labels are not atomic locks; serialize kickoff allocations and handovers.
- All three may act as coordinator at different times; follow
  [CONCURRENCY_POLICY.md](docs/development/CONCURRENCY_POLICY.md) for serialized
  updates, lost connections, safe Git synchronization and reassignment.

## During development and PRs

Work only on authorized tasks or legitimate off-plan fixes/docs/CI/refactors.
Small maintenance needs a clear PR explanation, not a fabricated plan issue;
substantial maintenance needs a normal issue. New future-phase features cannot
be disguised as maintenance. See [PHASE_GATE_POLICY.md](docs/development/PHASE_GATE_POLICY.md).
Keep scope small, preserve working code and follow prerequisite merge order.
Do not edit others' personal handoffs or change agreed interfaces unilaterally.

After meaningful progress, before PR creation/update, after integration repairs,
before ending a session, on transfer and at phase completion, update/push your
own handoff: completed scope, files, interfaces, exact test results, limitations,
dependencies and next actions. Distinguish planned, in-progress, implemented,
verified, merged and accepted. Never fabricate successful tests or integrations.

After a PR, update its issue with PR URL, CI, review/merge status and follow-ups.
The acting coordinator consolidates verified central state after major events.
Main requires one eligible non-author approval; game remains zero-review.
Phase kickoff additionally requires the master prompt's teammate sign-off.
Do not bypass protections, CI, regression tests or conflict checks for handoffs
or off-plan work. Stop after authorized scope; never automatically start another phase.
