# Concurrent work and shared coordination

Abdullah, Taha and Shaheer all coordinate handoffs, per user instruction. There
is no permanent single coordinator. **Only one writer at a time** edits central
`mandoff.md`; each consolidation records the acting writer and ownership handover.
Other members update their own handoffs while that update is in flight. Inspect
open central-handoff PRs and coordinate before starting another. Serialize phase
kickoff allocations; GitHub assignees/labels are not atomic locks.

## Mandatory phase kickoff, before application code

1. Acting coordinator fetches remote game/main and confirms the preceding gate
   is closed AND evidence-accepted; inspect open issues, PRs and existing claims.
2. Confirm human authorization. Allocate only current-phase tasks without
   duplicate claims; record critical path, parallel groups, shared interfaces,
   branch owners and integration order in mandoff and personal handoffs.
3. Use a dedicated docs-only kickoff branch, commit/push it, open a PR to game,
   obtain successful CI and the master prompt's kickoff teammate approval.
4. Merge only when authorized through normal protection. Confirm the kickoff
   and handoffs are visible on remote game. No application implementation before this.

## Personal publication, before source edits

After kickoff, fetch game, inspect assignee, issue comments/status, related PRs,
central allocation and all relevant handoffs. Confirm preceding gate acceptance
and that nobody else claimed the task. Create a separate branch/worktree; update
only your own handoff with claim, branch, dependencies and planned work. Commit
that handoff separately, push, verify remote commit exists, then begin code.
A failed push stops implementation. Planned owner is not an active task claim.

## Worktree isolation and synchronization

Never share an active working directory or uncommitted changes between agents.
Prefer sibling worktrees outside the repository to avoid accidentally tracking
nested checkouts. Example after assignment, not commands to run concurrently:

```powershell
git fetch origin
git worktree add -b feature/01-c01-graph-contract ..\smart-racing-worktrees\abdullah origin/game
```

Taha and Shaheer use their own directory/branch. Use separate clones if more
convenient. Check status before fetching/merging; never discard another person's
dirty work. Do not switch a branch already active in another worktree.

Read active interface PRs before editing contracts; producers and consumers
agree changes first. Merge prerequisites in order. Resolve conflicts by reading
both sides and discussing semantics, rerun tests, update handoffs and CI. Never
blindly use ours/theirs or force-push shared branches.

## Lost connection and reassignment

An interrupted agent's task remains claimed until an explicit handover. Inspect
its remote branch, last pushed handoff, open PR and CI before resuming. Do not
assume unpushed work exists remotely. Contact the owner/acting coordinator,
record a handover with old/new owner and last verified SHA, then resume in a new
worktree. Preserve old records and branches while dependants exist. Do not let
two agents simultaneously resume an abandoned task.
