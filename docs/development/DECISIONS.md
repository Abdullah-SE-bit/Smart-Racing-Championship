# Decision log

Initial record: 2026-11-15 (Asia/Karachi). Proposed design choices are not team
approvals. Add decisions with context, alternatives, reason, status and evidence.

| ID | Decision / alternative | Reason | Status |
| --- | --- | --- | --- |
| D001 | Keep existing src Python package layout; no application changes | Preserve scaffold and separation of algorithms, engine and UI | Existing baseline preserved |
| D002 | Feature → game → main with documented stacks; alternative direct feature → main | Support independent student work and final integration | Infrastructure task direction; game created remotely |
| D003 | main needs one eligible non-author approval; game review optional | User explicitly corrected game approval requirement | User direction; API verified |
| D004 | Classic protection, no repository rulesets | No existing rules; use one supported mechanism without conflicts | Enabled and verified; CI contexts deferred |
| D005 | Delay required status contexts and strict freshness until real successful CI | Avoid requiring nonexistent checks or deadlocking bootstrap | Game gates enabled after successful PR #1 run; main rollout pending |
| D006 | Four stable jobs, Python 3.12, Linux plus Windows; SHA-pinned actions | Student-friendly cross-platform CI with least privilege | Initial PR #1 GitHub Actions run passed all four jobs |
| D007 | Explicit feature validation manifest; alternative silently skip absent features | Distinguish infrastructure success from feature completion; fail activated missing gates | Prepared locally; team must refine per-capability paths |
| D008 | Ruff E4/E7/E9/F and PyYAML dev tools | Catch real Python mistakes and parse infrastructure configuration without strict style overhead | Infrastructure dependency additions; runtime unchanged |
| D009 | Omit CODEOWNERS until eligible usernames are supplied | Avoid invalid entries and impossible code-owner approval gates | Deferred; one main approval remains required |
| D010 | Keep auto-delete off; prefer merge-preserving stacks or replacement child branches | Avoid deleting active parents and rewriting published history | Existing GitHub setting preserved; workflow documented |
| D011 | Graph, route, event/resource/results contracts and ownership matrix | Establish integration discussion points without implementing or inventing game rules | Proposed; team approval and PDF verification required |

The assignment PDF is absent. No algorithm-family list, scoring formula, screen
definition or final schema has been approved by this log.

## Coordination decisions (current user task)

- User supplied A=Abdullah, B=Taha, C=Shaheer, preserving joint plan ownership.
  Verified logins: Abdullah-SE-bit, TahaSohail-Goat, Artfever. Taha/Shaheer are
  not currently assignable; account access remains a manual prerequisite.
- User confirmed 04-P05 remains optional; it is represented but does not block P04.
- All three coordinate handoffs. Shared responsibility uses one acting central
  writer per update and documented handover, not a permanent exclusive coordinator.
- Strict previous-gate acceptance and new authorization override the roadmap's
  early future-phase implementation examples. Planning is allowed; code is not.
- Gate audit is read-only. Premature closure is a failing diagnostic, not an
  automatic issue rewrite. No privileged PR execution or fake completion history.
- PR #190 targets main to bootstrap default-branch issue events. Initial Linux/
  Windows CI and Phase Gate Validation succeeded; main now requires the five
  actual observed contexts with strict freshness. Default audit and game phase
  check rollout remain pending the reviewed publication/synchronization.
