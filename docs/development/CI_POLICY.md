# CI policy

## Triggers and stable jobs

`.github/workflows/ci.yml` runs on PRs targeting `main`, `game`, or `feature/**`
(including base edits/retargets), pushes to `main`/`game`, and manual dispatch.
No feature push trigger duplicates ordinary feature PR runs. Push validation on
integration branches is retained because it validates the merged result. Older
runs for the same event/ref or PR are cancelled. No path filters suppress
required checks. Manual dispatch requires the workflow on the default branch.

| Job name | Runner / Python | Current validation |
| --- | --- | --- |
| Repository Validation | Ubuntu / 3.12 | Editable dependency installation, pip check, metadata/TOML, package directories, docs/links, YAML/forms, conflict markers and manifest schema. |
| Python Quality | Ubuntu / 3.12 | compileall on source/tests/scripts and Ruff. |
| Automated Tests | Ubuntu / 3.12 | Full pytest discovery and activated feature gates. |
| Integration Validation | Windows / 3.12 | Dependency consistency, installed package import, dummy SDL display infrastructure and full pytest/gates on Windows. |

Workflow display may show `CI / <job>`, but required check contexts are the
actual check-run names, expected to be the four job names above. **No names have
yet been observed in remote Actions runs.** Do not configure assumed contexts.

Ruff explicitly selects `E4`, `E7`, `E9`, and `F` for import/statement errors,
syntax/common mistakes, unused imports and undefined names. No line-length,
format, docstring, naming, or advanced abstraction policy is enforced. Ruff and
PyYAML are dev tools; runtime dependencies are unchanged. Version constraints
remain in `pyproject.toml`, with requirements delegating to the dev extra.

## Local commands

After installing `-e ".[dev]"` in a Python 3.12 virtual environment:

```powershell
python -m pip check
python scripts/validate_repository.py
python -m compileall -q src tests scripts
python -m ruff check src tests scripts
python scripts/run_tests.py
```

Set `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`, and a fixed
`PYTHONHASHSEED` before launching headless test processes, as the workflow does.

## Pending and activated checks

`validation.json` records pending feature categories and required pytest file
patterns. Pending entries are printed to logs and the Actions summary and are
never represented as verified features. If no tests exist, pytest exit 5 is
reported as no tests, not a passed suite; infrastructure can still pass if no
capability is declared implemented. All other pytest failures remain failures.

Once a capability is implemented, add/split its manifest entry with specific
test patterns and set status to `implemented`. The runner requires collected
tests and at least one passing call in each matching file; missing or wholly
skipped gates fail. Never revert a gate to pending to evade broken coverage.
All discovered tests run even for capabilities not yet activated. A reviewer
must check that implemented code does not remain incorrectly marked pending.

Experiment gates must actually invoke benchmark drivers, validate correctness,
raw schemas and output existence. Packaging gates must invoke real PyInstaller
builds on Windows and verify executable and bundled assets. Packaging activation
must also add installation of `.[packaging]` to the Windows job; it is deliberately
not installed while no real entry point exists. Platform-specific packaging
tests should collect on both OSes with an explicit passing Linux
validation of the build configuration, and run the executable build on Windows.
Do not silently skip the whole required packaging file. These tests do not yet
exist and no build is claimed.

## Rollout and merge gates

1. With explicit publication authorization, create an infrastructure branch,
   commit/push these files, and open a PR to `game`. Review there is optional.
2. Observe successful runs and retrieve `check_runs[].name` and the Actions app
   ID from the PR commit. Check actual conclusions; do not infer from local runs.
3. Merge into `game` only when authorized, then open `game` → `main`. Keep current
   main approval protection; one eligible non-author teammate must approve.
4. Confirm checks for each target before making them required. Enable strict
   up-to-date status checks with all four actual contexts, bound to the GitHub
   Actions app where supported. Verify the resulting API responses.
5. Do not require a context that has never run successfully, invent check
   results, disable review, or bypass protection to bootstrap CI.

See [remote status and manual paths](GOVERNANCE_STATUS.md). Until rollout, review
protections exist but required CI and up-to-date enforcement do not.

Fix failures on the feature branch, rerun relevant local checks and CI, and
refresh main review after changing the diff. Do not bypass failing checks.
Changing job names requires coordinated protection migration after the new
names succeed; never leave branches waiting on removed checks.

## Security and final submission

Actions are SHA-pinned to verified upstream v4 checkout/v5 setup-python commits.
Review upstream releases periodically before updating pins. Tokens are
read-only; checkout does not persist credentials. No `pull_request_target`,
secrets, privileged PR code, automated writes, deployment, or publishing exists.
Pip caching uses dependency metadata; exact experiments still need recorded
versions or a reviewed lock strategy.

Final submission needs all assignment-mapped gates active, all five studies,
Windows packaging with real assets, manual gameplay/visual evidence, eligible
main review and successful full CI. The missing PDF, performance interpretation,
viva understanding and visual quality cannot be resolved by a green job alone.

References: [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
[required checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks),
[pytest exit codes](https://docs.pytest.org/en/stable/reference/exit-codes.html),
[Ruff rules](https://docs.astral.sh/ruff/rules/).
