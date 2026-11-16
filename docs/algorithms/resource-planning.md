# Resource planning contracts

## 0/1 pickup selection

Each pickup has a unique integer ID, non-negative integer cost and benefit. A
single integer budget represents one explicitly chosen scalar, such as extra
distance; it does not combine physical fuel, time and nitro. The table state
`dp[i][b]` is the best benefit using the first `i` pickups within budget `b`.
The base row is zero. For each item the recurrence chooses the best of the
previous row at `b` and, when the item fits, its benefit plus the previous row
at `b - cost`. Walking backward reconstructs selected items. This costs O(mB)
time and O(mB) space, pseudo-polynomial in numeric budget B.

The greedy alternative considers positive-benefit zero-cost items first, then
items by descending exact benefit/cost ratio and ascending ID for ties. Zero
benefit items are skipped. This is feasible but not guaranteed optimal. The
assignment's example and two additional counterexamples are recorded in the
study results and checked against exhaustive search.

The planner presents independent single-pickup route alternatives. It checks
the route's estimated difficulty-adjusted fuel and the three-charge nitro cap
before recommending a pickup. This avoids treating several independent detours
as one combined route without verifying their combined feasibility.
In ordered-lap mode, each candidate is inserted into a leg of the ordered
checkpoint route; the shared checkpoint router prevents a later checkpoint from
being passed early. Candidate evaluation accounts for other active pickups
encountered first and does not recommend a pickup that would arrive after nitro
capacity is full. Endpoint mode instead evaluates the chosen start and target;
it does not claim to plan a complete ordered lap. Recommendations assume no
nitro is spent and no road or service changes occur while following the route.

## Discrete refuelling

For each consecutive route segment, the state stores arrival fuel and the best
accumulated stop time. At an active station it considers buying zero through the
lesser of remaining tank capacity and 40 units. A positive purchase adds the
same three-second stop time as the game; the transition subtracts the next
segment's required fuel. Unreachable states are discarded, and a plan is
infeasible if no state reaches the destination. The straightforward search is
O(mC²), with `m` segments and `C` discrete tank units in the worst case.

The route planner uses tenths of a fuel unit: edge requirements round up and
starting fuel rounds down, so discretization is conservative. Purchases are
reconstructed with the plan. The engine fills by up to 40 units rather than
offering smaller purchase amounts; this uses the same stop time and can leave
more fuel than the minimum plan, without exceeding tank capacity.
The refuelling screen lists each planned station vertex and the quantity in the
reconstructed plan. It tells the player to press F, which applies the game's
actual automatic fill rule. The displayed route starts with a full tank and
assumes no nitro use, road changes or service changes.

The unit suite checks the refuelling DP against exhaustive purchase sequences
on small three-segment routes, including inactive stations and infeasible
routes. It checks the knapsack result against exhaustive item subsets and the
greedy implementation against the assignment example and two additional
counterexamples. The Lab and planner use the same selection functions.
