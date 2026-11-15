# Team ownership and review policy

The user supplied the provisional A/B/C mapping below. Exact per-task ownership,
including joint owners, comes from implementation_plan.md and the issue registry.
Primary responsibility is not exclusive file ownership or permission to claim
future implementation. All students must contribute and understand the project.

| Role | Developer | Verified account | Primary responsibility | Suggested review / backup |
| --- | --- | --- | --- | --- |
| A | Abdullah | Abdullah-SE-bit | Algorithms, graph modelling, optimization | Reviews B; backup C |
| B | Taha | TahaSohail-Goat | Racing simulation, opponents, events, championship | Reviews C; backup A |
| C | Shaheer | Artfever | Pygame UI, visualization, tests, demos, tooling | Reviews A; backup B |

Account identities were supplied by the user and verified through GitHub's user
API. Only Abdullah is currently assignable in this repository; other issue
assignees remain unset with human-readable ownership preserved. Actual teammate
access must be added before eligible main/kickoff review. No registration numbers
are known or invented. Joint ownership remains joint even when only one owner
can be represented by an eligible GitHub assignee.

All three share coordination under the one-writer-at-a-time central handoff
procedure. Each kickoff names an acting writer and one integrator per task;
explicitly hand over that role rather than editing shared state concurrently.

Shared graph/route/trace, simulation/event/resource and result/metrics interfaces
need producer/consumer agreement before dependent code. Per-task plan ownership
overrides this broad module map. Escalate conflicts, serialize changes, record
accepted decisions and add contract tests. No silent interface/rule changes.

Main requires one eligible non-author approval; game retains zero required
reviews. Kickoff teammate sign-off is an additional phase-start policy. Optional
feedback otherwise follows the review suggestions above; never require both
primary and backup reviewer. CODEOWNERS remains omitted until eligible accounts
and final paths are agreed; code-owner approval is not enabled.
