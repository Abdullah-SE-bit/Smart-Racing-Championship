# Phase gates and authorization

The exact task rows in [implementation_plan.md](../../implementation_plan.md)
are the task authority; `Project.pdf` remains the coursework authority but is
absent. Its historical review claim in the plan has not been independently
verified here. The master coordination policy overrides the plan's permission
to start noncritical future phases early. No application phase is authorized.

Every phase P01–P16 requires the preceding accepted gate, explicit human phase
authorization, a published kickoff PR, and a pushed personal handoff claim before
application code. Planning/backlog creation does not claim implementation work.
All 171 task rows receive issues. User-confirmed optional task 04-P05 has an
issue and its own prerequisites, but does not block P04 acceptance.

## Gate states and evidence

BLOCKED/NOT_STARTED, IN_PROGRESS, READY_FOR_PROMOTION, and ACCEPTED are distinct.
Labels and checkboxes alone never establish acceptance. A closed gate is accepted
only when the audit verifies real task completion, merged PRs, applicable CI,
manual/demo/test evidence, current handoffs, approved main promotion and a stable
checkpoint. Reopening a required task invalidates acceptance until corrected.

Sequence: task PRs → game integration → phase verification → approved main
promotion → final integration task closure → gate closure. The final I02 task
may remain open while its promotion PR runs; the current phase gate must not
block that promotion. It must be complete before gate acceptance. Main always
needs one eligible non-author approval. Game retains zero required reviews;
the master prompt additionally requires teammate approval for a phase kickoff,
which is a documented kickoff-specific prerequisite, not a changed branch rule.

## Machine-readable PR declaration

Use one fenced JSON block introduced by `<!-- phase-governance -->` in the PR body:

```json
{"classification":"maintenance","phase":null,"task_ids":[],"reason":"Explain the change","risks":"Describe actual risks","tests":"Actual commands/results","interfaces":"unchanged","affected_gate":"P00-GATE"}
```

Other classifications: `planned`, `integration`, `promotion`, `kickoff`.
Planned/integration work must list exact plan IDs and its phase, e.g. `"01"`.
`feature/01-c01-description` and `feature/p01-c01-description` are supported.
Promotion must be `game` → `main`. Kickoff uses `docs/kickoff-p01` and only docs.

Maintenance, bug fixes, CI/docs, refactors and hotfixes use `maintenance/`,
`fix/`, `docs/`, `ci/`, `refactor/` or `hotfix/`. Small changes need no fake task
ID, but must explain reason, files/diff, risk, tests, interfaces and affected gate.
Docs/CI/tooling-only changes use a validated path allowlist. Source/data/assets
maintenance requires explicit human approval bound to the PR revision and must
repair accepted functionality; new future functionality is not maintenance.
No exception bypasses branch protection, review, CI or regression checks.

## Trusted state and acceptance records

`phase_state.json` records authorized phase, shared coordinator policy, kickoff
and claims. In PR CI, policy/registry are read from the target's base revision,
not accepted from an untrusted PR's self-authorizing changes. Bootstrap only
permits a strict infrastructure-only maintenance diff when the trusted base has
no phase policy yet. A missing task/gate/declaration otherwise fails.

Gate bodies use `<!-- gate-evidence -->` followed by a fenced JSON object, added
only when evidence exists. Required keys: `status`, `demo_url`, `test_url`,
`ci_run_id`, `handoff_commit`, `acceptance_document`, `approval_comment_id`.
Accepted gates additionally need `promotion_pr`, `main_commit`, `checkpoint_ref`.
P00 additionally needs `audit_run_id` for a successful Issue Gate Audit run on
the promoted main commit, proving default-branch publication and execution.
The approval comment must be by an eligible human collaborator, contain
`gate-approved:P##-GATE:<main_commit>`, and cannot be replaced by bot approval.
The audit validates linked run success, merged main PR/approval, main ancestry,
checkpoint resolution, handoff/document presence and required task completion.
Evidence files must contain real records; maintainers review their substance.

Completed task issues use `<!-- task-evidence -->` plus a fenced JSON object
with `pr`, `ci_run_id`, and `test_url`. The PR must actually be merged into game
or main, identify the exact task, and have successful CI for its cited revision.
The kickoff state names its phase and merged `pr`. Trusted kickoff allocations
map task IDs to `owner` and `branch`. After publishing the personal handoff,
the PR declaration supplies `handoff_commit` as evidence (not new authorization);
it must change only the named member's handoff and be a remote ancestor of the
implementation PR. No extra coordinator PR is needed just to record that SHA. Authorization
state references an eligible human issue comment containing `phase-authorized:P##`.
Update trusted state through a reviewed/validated infrastructure PR before it
can authorize another PR; a feature's own state edits cannot authorize itself.

## Native dependencies and audits

Task issues block their own phase gate; later-phase tasks depend on the previous
gate plus exact plan prerequisites. Parallel tasks are not chained arbitrarily.
`sync_backlog.py` creates/reuses unique IDs across open and closed issues,
retains human body additions, paces writes, retries rate limits and checkpoints
progress in the registry. Rerun after interruption; never blindly repeat a POST
after an ambiguous transport failure. Native relationships are read back from
GitHub; Markdown links are navigational, not enforcement.

Generated issue metadata is delimited by coordination comments. Keep free-form
handoff, task-evidence and gate-evidence records outside that managed block.
Refreshes preserve checked progress and human text outside the block; review
intentional source-scope changes rather than erasing or inventing work history.

`Phase Gate Validation` is a read-only PR check. The issue gate audit is read-only
and fails clearly for prematurely closed gates; it does not automatically reopen
issues without a separately authorized write-capable workflow. Issue events
require the workflow on the default branch. Bootstrap PRs remain unmerged until
authorized and required approvals exist. Never require a new check until a real
successful run confirms its actual name and target availability.

P00 remains open until the plan, handoffs, registry, dependencies and automation
are published and verified, including default-branch audit activation and human
infrastructure acceptance. Existing scaffold/main commits are not accepted
functional phases. After P00 acceptance, Phase 01 is the first candidate, still
requiring a new human instruction and shared kickoff.

References: [native dependency API](https://docs.github.com/en/rest/issues/issue-dependencies),
[GitHub rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).
