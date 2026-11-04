# ADR-0011: What a workspace or provider failure costs a card

**Status:** Accepted
**Date:** 2026-11-03
**Amends:** ADR-0007's "Workspace failures have defined outcomes" and its recorded cost "Free retries
have no attempt ceiling"; core §4.2, §5.3, §5.4, §5.8, §6, §10, §11; policy §2.2; `odoo-adaptation`
§6.1, §6.3, §6.8, §11.1; rules 68 and 86
**Adds:** rule 142
**Guarded by:** core §11's kill tests; the count of free-retry quarantines in a run
**Informed by:** `NousResearch/hermes-agent` at `fd267bb3`, read 3 November 2026 and not run here:
`_record_task_failure(infrastructure=True)`, `test_infrastructure_spawn_refusal_never_charges_the_card`,
`FailoverReason`, `test_stale_crash_reset_rejected_for_reclaimed_task`.

## Context

ADR-0007 made provisioning failures consume an attempt, kept a failed worktree reset as a blocker on
requeue, and recorded that free retries have no ceiling. Three problems follow.

**An outage scraps the board.** Backoff starts at 10 seconds and doubles, and `max_attempts` defaults
to 3. A provisioning outage of about 30 seconds therefore quarantines every card it reaches, none of
which did anything wrong, and each then needs a person. Core §10 lists this as the expected response.

**Nothing stops a run that cannot succeed.** A rejected credential or an exhausted account fails every
card. Each one spends attempts until the board is quarantined, though no retry can help.

**A slow reaper can wipe the next attempt.** Reapers run concurrently by design (core §5.4). Two can
select one candidate. The first kills, resets and flips the row, and the card is claimed again. The
second then runs `reset --hard` on the shared path `<workspace_root>/<key>`, inside the new attempt's
work. `$2` fences the flip, not the teardown.

## Decision

1. **Provisioning failures and drain releases are free.** `provision_failed` and `released` join the
   free classes. As ADR-0007 set out, a free retry raises `max_attempts` by one and never lowers
   `attempts`. Backoff still applies.
2. **Free retries have a ceiling.** `runs.max_free_retries` is set at run start, with no default, and
   lives outside the pin like `max_cost_usd`. A card's count comes from its `task_attempts` rows, so no
   counter is added. Past the limit the failure is charged and the card quarantines with its class
   named. This closes ADR-0007's recorded cost, and it is what stops a card that can never provision
   from retrying forever. **Start at 12**, about 40 minutes at the current backoff. That number is a
   guess.
3. **Some failures halt the run.** `auth_rejected`, `billing_exhausted` and `model_unavailable` set
   `runs.halted_class` in the failing transaction and charge nothing. The claim refuses while it is
   set, as it does for Budget, and `ready(t)` stays pure. Cards in flight finish. A person fixes the
   cause and clears it, or abandons the run. **Only an unambiguous provider signal counts**: an ambiguous
   body stays `provider_refused`, because a wrong halt stops everything.
4. **A free failure is invisible to the card.** Layer 7 renders the last *charged* attempt, not the
   last attempt. The card was not at fault, has nothing to learn, and its prompt stays byte-identical
   so the replay cache still serves.
5. **Escalation counts charged attempts** (policy §2.2, rule 68), which are `attempts` less the card's
   free rows. Otherwise an outage raises a card's effort and tier for nothing.
6. **The worktree and its branch are per attempt:** `card_<key>_attempt<n>`, as the container and
   database already are. A slow reaper then acts only on the attempt it selected. `integrate` merges the
   branch of the committed attempt, which is `tasks.attempts`. Failing to remove a worktree is logged and
   no longer blocks requeue, because a retry never reuses the path. **Failing to kill still blocks.**

## Alternatives considered

**Keep charging, and raise `max_attempts`.** Simple, but it weakens the crash-loop bound for real card
failures to survive outages, and still loses to a long enough outage.

**A circuit breaker: refuse claims when recent failures span unrelated cards.** Handles outages
centrally, and it may yet be right. It needs a window and a threshold, and it is a judgement about the
system where this ADR has only typed classes. Add it if free retries prove too blunt.

**Hold the row lock through teardown, or re-check the fence before each step.** A lock would span
`docker kill` and a filesystem removal inside a transaction. A re-check narrows the race and leaves it
open. Unique paths remove the shared target instead.

**Keep one branch per card, with worktrees per attempt.** Git refuses to check out a branch that a
stale worktree still holds, so a failed removal would become a failed provision.

**Match error text, as Hermes's `_RESPAWN_BLOCKER_RE` does.** It parked healthy cards when "author"
matched (#117009). Classification here happens in the adapter, from provider status and typed errors.

## Consequences

**Good.** An outage costs waiting, not cards. A run that cannot succeed stops at the first proof. The
reaper race is gone by construction.

**Costs.** `runs` gains two columns, and the claim gains one more clause, which R15's `EXPLAIN ANALYZE`
must cover. Failed attempts leave branches until teardown removes them. A long provider rate limit can
now exhaust a card's free retries, and a person has to requeue it.

**Halted runs need a person,** which fits the README's "a helper, not an unattended system".

**Not measured.** None of this has run. The Hermes evidence shows these failures occur in a SQLite and
host-PID system. It does not show that these fixes work here.

## What would change our mind

- **Free-retry quarantines occur in an outage that later clears** → raise the limit, or build the
  circuit breaker.
- **A halting class fires when the provider was actually fine** → narrow its classification. If that
  cannot be done, return the class to charged retries.
- **Leftover branches become a real cost** → remove them sooner. Nothing else depends on them.
- **Ten real runs with no provisioning failure and no halt** → these are margin, and principle 8
  applies.
