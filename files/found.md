What I'd actually take
The expected-failure-message check. New, cheap, and it closes the gap between red and red for the right reason that assertion_check.py only half closes.
Refactor cards touch no test files. A gate, one line.
The "assert on real behavior, never on mock behavior" rule, which the skill references and which rung 0 can partly check — a test whose assertions are all on mock objects is statically detectable.
Say explicitly that per-assertion coverage means extracted helpers have no direct test, as a decision rather than an omission.

And I'd note the general lesson somewhere: the length of a rule's prose is inversely proportional to how well it's enforced. This document is thirteen red flags long because it has no worktree, no separate card, and no host-side checker. You have all three, so your version should be four lines — and if it ever starts growing toward this one, that's the signal the gate has stopped holding.