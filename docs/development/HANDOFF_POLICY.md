# Handoff policy

[mandoff.md](../../mandoff.md) is the single source for current team activity,
immediate blockers and next actions. Personal files preserve independent detail:
[Abdullah](handoffs/HANDOFF_ABDULLAH.md), [Taha](handoffs/HANDOFF_TAHA.md),
[Shaheer](handoffs/HANDOFF_SHAHEER.md). Legacy MEMBER files remain archived
references; no meaningful progress is deleted or invented.

All three share coordination, with one acting central writer per update and
explicit handover; see [concurrency policy](CONCURRENCY_POLICY.md). Agents do
not edit another member's personal file. The authorized kickoff coordinator may
initialize allocations across the three files before implementation.

Update concise factual records:

1. Before implementation, as a separate pushed personal-handoff commit after
   the shared kickoff is merged and confirmed on remote game.
2. After meaningful progress.
3. Before opening or updating a PR; push the handoff with the task branch.
4. After integration problems are resolved.
5. Before ending a session, including failed tests and unpushed work.
6. When transferring a task, with last verified commit and receiving owner.
7. At phase completion, with accepted gate and checkpoint evidence.

Distinguish PLANNED, IN_PROGRESS, IMPLEMENTED_UNVERIFIED, VERIFIED, MERGED and
PHASE_ACCEPTED. Writing code does not prove an algorithm correct; merging a task
does not accept a phase. Record exact test commands/results and CI URLs; do not
attribute bootstrap agent checks to students who did not run them.

After PR creation/update, the owner updates its issue with PR URL, CI, review,
merge state and follow-ups. The acting coordinator reconciles central state
from personal handoffs, actual issues/PRs, CI and accepted gates after major
integrations. Last update times use Asia/Karachi with explicit offset.
