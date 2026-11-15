# Development workflow

Issue → Branch → Implementation → Tests → PR → Review where required → CI →
Merge → Handoff. This document authorizes no feature implementation or merges.

## Start or resume work

Read the assignment (currently unavailable), root instructions, relevant
contracts, issue, existing code, and your handoff. Confirm the assigned scope
and owner. No implementation issues have been created by this infrastructure
task. Once feature work is authorized, agree an issue before implementation.

Check `git status`, fetch the remote, and inspect the intended parent branch.
Do not overwrite dirty work. Start `feature/<descriptive-name>` from current
`origin/game`, or the documented parent branch for a stack. Resume an existing
branch rather than creating competing work. Record issue, branch, PR, and
dependencies in your own handoff; do not edit another member's progress.

## Implementation and PR preparation

Keep changes focused. Agree shared contracts before changing consumers.
Run repository validation, Ruff, compilation, and the pytest gate runner as
described in [CI policy](CI_POLICY.md). Add genuine correctness/regression tests
with functionality and activate its manifest gate. Record exact commands,
results, and unavailable checks. Inspect the diff for secrets, accidental large
binaries, unrelated changes, and generated files. Keep licensed required assets
and submitted experiment outputs tracked; never commit environments or builds.

Open a PR only when authorized. Feature PRs normally target `game`; stacked PRs
target their prerequisite. Complete the PR template, link the issue, identify
merge order, and update the handoff. No implementation issues or PRs are opened
automatically. No automated direct pushes, fixes, merges, or deployments.

## Review and CI

`main` requires one approving eligible teammate other than the author, resolved
conversations, and ultimately all verified required CI checks. `game` requires
no review approval; feedback is optional. All four CI contexts and strict
up-to-date enforcement are active on `game`. Main's status enforcement awaits
its separately authorized rollout and successful main-target run.
See [current remote status](GOVERNANCE_STATUS.md).

A main reviewer checks the requirement mapping, contracts, readable algorithm
reasoning, edge cases, determinism, tests, and evidence. Never treat the author
as an approving reviewer. New commits invalidate main approvals; request a fresh
review after the final update. Optional reviewers on `game` do not create an
approval gate. Follow [ownership](MODULE_OWNERSHIP.md) for review suggestions.

## Conflicts and dependent work

Use [the branching procedure](BRANCHING_STRATEGY.md). Inspect both sides and
consult affected owners; do not blindly accept ours/theirs. Stop affected work
if a contract conflict cannot be resolved. After resolving locally, rerun checks,
review the PR diff, update handoffs, and obtain any required fresh approval.

## Integration and handoff

Merge only with user authorization and applicable gates satisfied. Do not
auto-merge a stack. Keep parent branches while open dependent PRs target them.
Delete a feature branch only after confirming there are no dependants.

For `game` → `main`, review all included issues, run complete available CI on the
integration PR, summarize integrated behavior and remaining gaps, and get one
non-author approval. Keep `game` current with `main` by a PR when it diverges;
never reset or force-push it. After a merge record commit/PR, verified tests,
changed contracts, remaining issues, and the next explicit task in your handoff.
