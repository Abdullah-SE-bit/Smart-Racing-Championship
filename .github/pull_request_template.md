## Summary

What does this PR change?

## Related Issue

Closes #... (or explain why an infrastructure PR has no issue).

## Target Branch

- [ ] game
- [ ] main
- [ ] Stacked feature branch

## Type of Change

- [ ] Algorithm
- [ ] Gameplay
- [ ] UI
- [ ] Testing
- [ ] Documentation
- [ ] Infrastructure
- [ ] Bug fix

## Implementation Details

Explain the important changes.

## Dependencies

List prerequisite PRs, their branches, and the required merge order. State none if independent.

## Algorithm Details

When applicable: name, data structures, time complexity, space complexity,
correctness assumptions, edge cases, and gameplay integration point.

## Testing

- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing
- [ ] CI checks
- [ ] Not applicable, with explanation

Include actual commands and results. Distinguish local checks, remote CI, and pending coverage.

## Screenshots / Demo

For GUI or gameplay changes, provide relevant evidence.

## Checklist

- [ ] Changes are focused.
- [ ] No unrelated files modified.
- [ ] Code follows project conventions.
- [ ] Existing functionality is preserved.
- [ ] Required tests added or updated.
- [ ] Documentation updated.
- [ ] Relevant handoff file updated.
- [ ] Dependencies are documented.
- [ ] No secrets committed.
- [ ] No unresolved conflicts.
- [ ] No unsupported claims of testing.
- [ ] Newly implemented capabilities activate the appropriate validation manifest gates.

## Reviewer Notes

What should the reviewer focus on?

## Viva Readiness

Explain the implementation in simple terms another student can understand.

## Phase governance declaration

Choose planned task, phase integration, phase promotion, kickoff, maintenance,
bug fix, or CI/documentation. For maintenance/bug fix/CI/docs use classification
`maintenance`; do not invent a task ID. Replace the example fields with actual
scope. Use exactly one machine-readable declaration:

<!-- phase-governance -->
```json
{"classification":"maintenance","phase":null,"task_ids":[],"reason":"Explain why","risks":"Describe risks","tests":"Commands and actual results","interfaces":"unchanged","affected_gate":"P00-GATE"}
```

For planned work specify phase `01`..`16`, exact task IDs and actual linked issue
numbers. Record previous gate ID and GitHub-verified acceptance, upstream issue/
PR dependencies and merge order. See docs/development/PHASE_GATE_POLICY.md.

## Handoff publication

- [ ] Personal named handoff updated, or infrastructure-only exemption explained.
- [ ] Separate remote personal-handoff claim commit pushed before source edits.
- [ ] Central handoff reconciled by the single acting coordinator where appropriate.

## Phase verification and review

Previous accepted gate and evidence:

Regression/CI results and manual demonstration:

Requested teammate (main/kickoff requires eligible non-author; game otherwise optional):

Known limitations and affected gate:
