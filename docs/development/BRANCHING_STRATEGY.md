# Branching and stacked PRs

`feature/*` → `game` → `main`. `main` is stable; `game` is the continuously working
development integration branch. Do not develop features directly on either.
Feature branches normally start from `game`. `main` needs one eligible
non-author approval; **`game` has no approval requirement**. Both require PRs,
block force pushes/deletion, and are intended to require the same four CI jobs
after successful rollout. See [verified settings](GOVERNANCE_STATUS.md).

For planned work, prefer `feature/01-c01-description` (or `feature/p01-c01-description`)
so the phase validator can match the leading exact plan ID. Off-plan work may
use `fix/`, `maintenance/`, `docs/`, `ci/`, `refactor/`, or `hotfix/`, with a clear
scope/risk/test/interface explanation. This does not authorize disguised future
features. Phase kickoff uses a dedicated docs/kickoff-p## branch. Accepted prior
gate and explicit phase authorization are mandatory before application work;
see [phase policy](PHASE_GATE_POLICY.md).

Examples of future branch names: `feature/graph-model`, `feature/bfs-dfs`,
`feature/dijkstra-astar`, `feature/racing-engine`, `feature/resource-planning`,
`feature/event-system`, `feature/championship`, `feature/pygame-ui`, and
`feature/algorithm-lab`. These are examples, not created branches or assignments.

## Creating a stack (future authorized work)

Start the graph model from `origin/game`. Create BFS/DFS from the graph-model
branch and route-planner from its documented prerequisite. Target each PR at its
immediate parent and list dependencies explicitly. CI also runs for PRs targeting
`feature/**`; other parent naming schemes require adjusting CI before use.

```text
game <- feature/graph-model <- feature/bfs-dfs <- feature/route-planner
```

Merge in prerequisite order, never automatically. Keep repository automatic
branch deletion disabled: an open child PR may still depend on its parent.

## After a parent merges

1. Fetch the remote and record the old parent tip and the child-only commit range.
2. Prefer preserving history: merge `origin/game` into the child locally, resolve
   conflicts, retarget its PR to `game`, and inspect the entire PR diff.
3. With a merge commit for the parent, shared ancestry normally excludes parent
   changes. Squash/rebase merging the parent changes ancestry: do not assume the
   child PR diff is clean merely because the working tree matches.
4. If the diff contains parent work, create a replacement branch from current
   `origin/game` and cherry-pick only reviewed child commits. Open a replacement
   PR when authorized; link the superseded PR. Keep the old branch until no child
   depends on it. This avoids rewriting a published branch.
5. Retarget deeper PRs only when their own prerequisite has integrated; verify
   each PR diff, rerun CI, resolve conversations, and obtain fresh approval for
   `main` if the diff changed. `game` review remains optional.

Rebasing is suitable only for unpublished, privately owned work whose history
is safe to rewrite, or after explicit later team/user authorization. A typical
operation is `git rebase --onto origin/game <old-parent-tip> <child>`; confirm
the boundaries before using it. Use `git rebase --abort` or `git merge --abort`
to abandon an unresolved operation. Do not force-push shared branches. No
history rewrite or force push is authorized by this infrastructure task.

## Conflict resolution

Read both versions, agree contract semantics with owners, resolve locally, and
run relevant unit/integration tests plus CI. Do not use blanket ours/theirs
resolution. Escalate unresolved rule or architecture conflicts before merging.
After integration inspect open PR bases before deleting any feature branch.
