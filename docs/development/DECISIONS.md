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
definition, final schema or team identity has been approved by this log.
