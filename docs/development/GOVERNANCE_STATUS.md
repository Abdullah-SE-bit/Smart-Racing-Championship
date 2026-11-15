# Verified governance status

Inspected/configured 2026-11-15, Asia/Karachi. Repository:
[Abdullah-SE-bit/Smart-Racing-Championship](https://github.com/Abdullah-SE-bit/Smart-Racing-Championship).
This is an observation record, not a guarantee that later settings remain unchanged.

## Repository and branches

- Public repository; authenticated account `Abdullah-SE-bit` has admin access.
- GitHub CLI 2.98.0 installed and authenticated. Account plan name was not exposed
  by the user API (`null`); no paid plan is assumed. Public repositories support
  classic branch protection, and successful API mutations/read-back verify support.
- `main` remains at `ab22643faaf574df8d986009d0f65eb44213ec0c`.
- Remote `game` was created from that exact current main commit, without rewriting history.
- Local `game` tracks `origin/game`. Infrastructure branch
  `chore/repository-governance` is published as PR #1 into `game`, with user
  authorization to push and merge after successful CI. No main merge is authorized.
- No feature implementation issues or branches were created. The remote `game`
  reference was created using the GitHub API; infrastructure commits and PR #1
  were subsequently published with explicit user authorization.
- No existing workflow, template, ruleset or protection was found initially.
  Classic protection is now the sole configured mechanism; rulesets remain empty.
- Automatic branch deletion and auto-merge remain disabled. No visibility,
  billing, subscription, deployment or publishing settings were changed.

## Protection read back from GitHub API

| Rule | main | game |
| --- | --- | --- |
| PR required / ordinary direct pushes disallowed | Enabled and verified | Enabled and verified |
| Approving reviews | 1 eligible non-author | 0; review optional per user instruction |
| Dismiss stale approvals | Enabled and verified | Disabled; no approval gate |
| Resolve conversations | Enabled and verified | Enabled and verified |
| Administrator enforcement | Enabled and verified | Enabled and verified |
| Force pushes | Blocked and verified | Blocked and verified |
| Branch deletion | Blocked and verified | Blocked and verified |
| Required status checks | Five observed successful contexts configured, including Phase Gate Validation | Four original verified CI contexts; additional phase context pending rollout |
| Require branch up to date | Enabled and verified (strict checks) | Enabled and verified (strict checks) |
| Code-owner approval | Not enabled; no eligible ownership entries | Not enabled |
| Explicit PR bypass allowances | None returned by protection API | None returned by protection API |

GitHub prevents authors satisfying their own review requirement. Admin
enforcement applies the active rules to administrators; administrators can still
edit repository settings, so this is not an immutable security boundary.

Only the owner is currently listed as a collaborator. Add eligible teammates
before attempting a main PR authored by the owner. No extra review accounts or
team approvals were invented. The main approval gate must not be bypassed.

## Publication and remaining main rollout

The user authorized pushing and merging the infrastructure branch into `game`.
[PR #1](https://github.com/Abdullah-SE-bit/Smart-Racing-Championship/pull/1)
published the workflow. The first
[CI run](https://github.com/Abdullah-SE-bit/Smart-Racing-Championship/actions/runs/43735487239)
succeeded on Linux and Windows. Its actual check names are Repository Validation,
Python Quality, Automated Tests, and Integration Validation. All four are now
required on `game`, bound to the GitHub Actions app, with strict freshness and
zero required approvals; configuration was read back from the API.

PR #1 subsequently passed the final revision and merged into game at
f66889e70e83f27d95a256c97cb08c45cd34c125; the merge-triggered CI also passed.
Main integration requires explicit authorization and one eligible non-author
approval. PR #190 supplied the first successful main-target run; five exact
contexts are now configured with strict freshness. The PR remains open and the
issue audit is not active on the default branch. Do not bypass review to bootstrap CI.

Manual paths in this repository:

- **Settings → Collaborators → Add people**: invite the actual teammate accounts
  with appropriate write access; acceptance is required for eligible review.
- **Settings → Branches → Branch protection rules → Edit** `main` or `game`:
  preserve the table above. For main, after actual successful runs, enable **Require
  status checks to pass before merging**, select all four actual job contexts
  from GitHub Actions, and enable **Require branches to be up to date before
  merging**. Keep game's required approval count at zero; main's at one.
- **Actions → CI**: inspect real job conclusions on the relevant PR revision.
  Dispatch only once the workflow exists on the default branch.
- **Settings → General → Pull Requests**: keep automatic head-branch deletion
  disabled while stacks exist; manually check dependants before deletion.

No unsupported setting was encountered. If visibility later becomes private
and the plan cannot enforce protection, stop claiming protection, record the
API error, and discuss an eligible paid plan or public visibility with the
user; never change visibility/billing automatically.

## Local verification evidence

Executed on Windows with Python 3.12.16 in ignored `.venv`:

- Editable `.[dev]` installation succeeded; `python -m pip check` found no broken requirements.
- `python scripts/validate_repository.py` passed metadata, structure, docs/links,
  YAML/forms, action pins, stable job-name and conflict-marker checks.
- `python -m compileall -q src tests scripts` and `python -m ruff check src tests scripts` passed.
- `python scripts/run_tests.py`: **7 infrastructure regression tests passed**.
  These exercise empty-suite reporting, activated missing gates, successful
  gates, failure propagation, skipped gates and collection errors in isolated
  temporary fixtures. No application functionality is verified by them.
- Installed package import and a dummy SDL display initialized successfully.
- Upstream actionlint v1.7.12 passed the workflow; its downloaded Windows binary
  archive was checked against the upstream SHA256 release checksum.
- `git diff --check` passed. All 20 application initializers remain empty and
  unchanged. Virtual environment and generated bytecode remain ignored.

Selected installed tool versions: pytest 9.2.0, Ruff 0.17.5, PyYAML 6.0.3,
Pygame 2.6.1, Matplotlib 3.11.2. These observations are not a dependency lock.
Remote Linux and Windows execution subsequently passed in the linked initial CI
run. This verifies infrastructure only; later revisions require fresh checks.
Algorithm correctness, game integration, determinism, experimental
reproducibility and Windows executable packaging remain pending in the manifest.

Verification commands (read-only):

```powershell
gh api repos/Abdullah-SE-bit/Smart-Racing-Championship/branches
gh api repos/Abdullah-SE-bit/Smart-Racing-Championship/branches/main/protection
gh api repos/Abdullah-SE-bit/Smart-Racing-Championship/branches/game/protection
gh api repos/Abdullah-SE-bit/Smart-Racing-Championship/rulesets
gh api repos/Abdullah-SE-bit/Smart-Racing-Championship/actions/workflows
```

References: [protected branches and public-plan availability](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches),
[protection API](https://docs.github.com/en/rest/branches/branch-protection).

## Phase coordination bootstrap (2026-11-15)

The new task authorizes creating real backlog issues/dependencies and publishing
an infrastructure PR, but no gameplay or automatic phase advancement. Branch
maintenance/phase-gate-governance prepares named handoffs, central mandoff,
strict phase policy and read-only Phase Gate Validation / Issue Gate Audit.
Publication, CI results and activation status are recorded in the final bootstrap
report; local files alone do not activate enforcement. PR #190 passed all five
checks on initial revision 7eb1402, and main's five required contexts were read
back from the API. The workflow files remain unmerged; P00 remains open.

Accounts TahaSohail-Goat (Taha) and Artfever (Shaheer) were user-supplied and
verified via GitHub user API; neither is currently assignable. Their issue
ownership remains in bodies, and eligible teammate access/review is unresolved.
All three share coordination, with one central writer at a time. 04-P05 remains
optional by explicit user decision. No real student implementation is recorded.

Requesting reviews from TahaSohail-Goat and Artfever on PR #190 returned HTTP 422:
GitHub permits review requests only from collaborators. Add eligible access and
obtain a real non-author approval before main integration. After main merge,
synchronize infrastructure into game through a validated PR, verify the new
phase check there and add it as required. Run the default-branch issue audit and
complete actual P00 acceptance evidence; do not begin Phase 01 automatically.
