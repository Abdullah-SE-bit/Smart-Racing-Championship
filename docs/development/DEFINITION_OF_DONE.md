# Definition of Done

A feature is complete only when all applicable conditions hold:

- Its issue acceptance criteria and verified assignment requirements are met.
- Relevant unit, correctness, invariant, regression, determinism and integration
  tests pass; manifest gates reflect implemented capabilities.
- Available CI passes on the PR's current revision with no hidden failing checks.
- Integration with actual producers/consumers is verified, not simulated by
  unrelated example implementations.
- Documentation, contract decisions and the responsible member handoff are updated.
- Evidence identifies commands/results and separates local, remote and manual work.
- The team can explain the implementation, complexity, assumptions and edge cases.
- For `main`, one eligible non-author teammate approves the final diff, all
  conversations are resolved, and required protections are satisfied.
- For `game`, review is optional; no approval is required. CI and the other
  applicable merge gates still apply.
- The user authorizes merging; agents never auto-merge or start another phase.

GUI work additionally needs manual visual/input evidence. Experiment work needs
raw data, metadata, correctness and reproducible commands. Packaging needs a
real Windows executable containing required assets. A pending feature category
or an infrastructure-only check cannot establish application completion.

## Task versus phase completion

A planned task is finished only after scoped implementation, required verification,
contract/documentation and personal handoff updates, and actual PR integration.
Its issue records a merged PR and test/CI evidence. Writing source or closing an
issue alone is insufficient. Optional 04-P05 does not block P04 acceptance.

A phase is finished only after its gate is evidence-accepted: required tasks
complete, runnable demo/regression verified, handoffs reconciled, approved main
promotion merged, stable checkpoint recorded and human approval confirmed.
READY_FOR_PROMOTION precedes final integration closure; it is not ACCEPTED.
No subsequent phase begins without that gate plus new human authorization and
published kickoff. See PHASE_GATE_POLICY.md for the full evidence contract.
