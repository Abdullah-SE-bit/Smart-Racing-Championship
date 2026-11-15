# Critical path and phase dependencies

The authoritative task graph is the detailed backlog in
[implementation_plan.md](../../implementation_plan.md); actual issue URLs and
all expanded ranges are in [TASK_DEPENDENCIES.md](TASK_DEPENDENCIES.md).

```text
P00 accepted -> P01 Explorer -> P01 accepted -> P02 Routing
 -> P03 Race -> P04 Resources -> P05 Events -> P06 Tracks
 -> P07 Championship -> P08 Lab -> P09 Studies 1/2 -> P10 Studies 3/4
 -> P11 Study 5 -> P12 Mandatory baseline -> P13 Generator
 -> P14 Trade-offs -> P15 Live analytics -> P16 Final release
```

Each arrow between phases requires the preceding gate accepted, explicit new
human authorization and a published shared kickoff; no future code starts early.
This strict policy supersedes the plan's more permissive early-start examples.
Within an authorized phase, preserve the exact C/P/I task DAG; do not serialize
parallel tasks without a stated prerequisite. Proposed interfaces still need
agreement; no implementation schedule or dates are implied.

Current critical path is coordination publication, complete issue/native-link
audit, verified phase automation and human-reviewed main readiness acceptance.
Then Phase 01 may be authorized. Its graph contract/model feeds BFS and DFS in
parallel; UI/fixtures/tests consume the agreed contract; integration I01 feeds
promotion I02. 01-P04 can start from the scaffold only after phase kickoff.

04-P05 is user-confirmed optional; it does not block Phase 04. Final integration
promotion tasks are required for acceptance, but the gate may be ready for
promotion while that final task is still open. No circular gate dependency.
