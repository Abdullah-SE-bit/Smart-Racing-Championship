# Proposed ownership and review policy

Temporary identifiers only. This matrix is a **proposal**, not accepted team
assignments. No real identities, account permissions, or registration numbers
are inferred.

| Scope | Proposed primary | Suggested reviewer | Backup reviewer |
| --- | --- | --- | --- |
| Core graphs, traversal, routing, generation, track validation | Member 1 | Member 2 | Member 3 |
| Engine, racers, events, resources, optimization | Member 2 | Member 3 | Member 1 |
| UI, Algorithm Lab, championship, sorting, experiments | Member 3 | Member 1 | Member 2 |
| Shared structures, integration tests, contracts, CI, final packaging | All; name one owner per issue | A non-author member | The remaining non-author member |

All three review shared interfaces. Member 1 proposes graph/route contracts,
Member 2 proposes simulation/event/resource contracts, and Member 3 proposes
presentation/result/metrics consumers. Integration responsibility belongs to
the issue owner with affected consumers participating. These roles need team
confirmation before implementation.

Only `main` requires one eligible teammate approval; `game` requires none.
Optional feedback may follow this matrix. Never require both suggested and
backup reviewers, and never count author approval. A reviewer must have eligible
repository access; assign actual collaborators before the first main merge.

As verified on 2026-11-15, the API lists only the repository owner as a
collaborator. The other students' accounts and access remain unconfigured; the
owner cannot satisfy their own PR's main approval requirement. Do not switch
accounts to impersonate a teammate or bypass this requirement.

CODEOWNERS is intentionally omitted until real eligible usernames and paths
are agreed. It is optional and never replaces the one-approval rule. Do not
enable required code-owner review without actual eligible owners.

For overlapping edits, stop the affected edits, compare contracts and diffs,
agree one issue owner, record the decision, and have an unaffected member
resolve disagreement. Escalate unresolved architecture or assignment conflicts
to the user rather than silently changing behavior.
